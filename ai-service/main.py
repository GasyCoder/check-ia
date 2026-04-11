import math
import random
import re
from typing import Optional

import numpy as np
import torch
from fastapi import FastAPI
from pydantic import BaseModel
from scipy.stats import variation
from transformers import (
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    pipeline,
)

app = FastAPI()

# ═══════════════════════════════════════════
# Model configuration — Multi-model ensemble
# ═══════════════════════════════════════════

# Detector 1: RoBERTa-base fine-tuned on ChatGPT output
DETECTOR1_NAME = "Hello-SimpleAI/chatgpt-detector-roberta"

# Detector 2: RoBERTa-large fine-tuned by OpenAI (better on longer texts)
DETECTOR2_NAME = "openai-community/roberta-large-openai-detector"

# Perplexity models for Binoculars-style cross-perplexity
PPL_SMALL_NAME = "gpt2"
PPL_MEDIUM_NAME = "gpt2-medium"

# Translation
TRANSLATION_MODEL_NAME = "Helsinki-NLP/opus-mt-fr-en"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
PIPELINE_DEVICE = 0 if DEVICE.type == "cuda" else -1

print("[INIT] Loading Detector 1 (RoBERTa-base ChatGPT)...")
detector1 = pipeline(
    "text-classification",
    model=DETECTOR1_NAME,
    tokenizer=DETECTOR1_NAME,
    top_k=None,
    device=PIPELINE_DEVICE,
)

print("[INIT] Loading Detector 2 (RoBERTa-large OpenAI)...")
detector2 = pipeline(
    "text-classification",
    model=DETECTOR2_NAME,
    tokenizer=DETECTOR2_NAME,
    top_k=None,
    device=PIPELINE_DEVICE,
)

print("[INIT] Loading GPT-2 (small) for perplexity...")
ppl_small_tokenizer = AutoTokenizer.from_pretrained(PPL_SMALL_NAME, use_fast=True)
ppl_small_model = AutoModelForCausalLM.from_pretrained(PPL_SMALL_NAME).to(DEVICE)
ppl_small_model.eval()

print("[INIT] Loading GPT-2 Medium for cross-perplexity...")
ppl_medium_tokenizer = AutoTokenizer.from_pretrained(PPL_MEDIUM_NAME, use_fast=True)
ppl_medium_model = AutoModelForCausalLM.from_pretrained(PPL_MEDIUM_NAME).to(DEVICE)
ppl_medium_model.eval()

print("[INIT] Loading translation model (FR→EN)...")
translator_tokenizer = AutoTokenizer.from_pretrained(TRANSLATION_MODEL_NAME)
translator_model = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATION_MODEL_NAME).to(DEVICE)
translator_model.eval()

print("[INIT] All models loaded.")


def _clamp(score: float, lower: float = 0.0, upper: float = 0.999) -> float:
    return max(lower, min(upper, float(score)))


def _to_device(batch: dict) -> dict:
    return {key: value.to(DEVICE) for key, value in batch.items()}


def _split_sentences(text: str, min_chars: int = 5) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if len(sentence.strip()) >= min_chars
    ]


# ═══════════════════════════════════════════
# Language detection & translation
# ═══════════════════════════════════════════

def is_mostly_french(text: str) -> bool:
    french_markers = [
        r"\ble\b", r"\bla\b", r"\bles\b", r"\bdes\b", r"\bdu\b",
        r"\bun\b", r"\bune\b", r"\best\b", r"\bet\b", r"\ben\b",
        r"\bde\b", r"\bpour\b", r"\bdans\b", r"\bqui\b", r"\bque\b",
        r"\baux\b", r"\bavec\b", r"\bplus\b", r"\bpar\b", r"\bsur\b",
    ]
    text_lower = text.lower()
    matches = sum(1 for pattern in french_markers if re.search(pattern, text_lower))
    return matches >= 5


def translate_to_english(text: str) -> str:
    sentences = _split_sentences(text, min_chars=1)
    chunks, current = [], ""

    for sentence in sentences:
        if len(current) + len(sentence) < 400:
            current += (" " + sentence) if current else sentence
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    translated_parts = []
    for chunk in chunks:
        inputs = translator_tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)
        inputs = _to_device(inputs)
        with torch.no_grad():
            outputs = translator_model.generate(**inputs, max_length=512, num_beams=1)
        translated_parts.append(translator_tokenizer.decode(outputs[0], skip_special_tokens=True))

    return " ".join(translated_parts).strip() or text


# ═══════════════════════════════════════════
# RoBERTa detectors (shared logic)
# ═══════════════════════════════════════════

def _label_is_ai(label: str) -> bool:
    normalized = label.strip().lower()
    return normalized in {"fake", "label_1", "generated"} or any(
        token in normalized for token in ("chatgpt", "ai", "synthetic", "machine")
    )


def _label_is_human(label: str) -> bool:
    normalized = label.strip().lower()
    return normalized in {"real", "label_0", "human"}


def _extract_model_score(results) -> float:
    rows = results[0] if isinstance(results, list) and results and isinstance(results[0], list) else results

    ai_score = None
    human_score = None

    for row in rows:
        label = str(row.get("label", ""))
        score = float(row.get("score", 0.0))

        if _label_is_ai(label):
            ai_score = score
        elif _label_is_human(label):
            human_score = score

    if ai_score is not None:
        return _clamp(ai_score)

    if human_score is not None:
        return _clamp(1.0 - human_score)

    return 0.5


def _run_detector(det_pipeline, text: str) -> float:
    """Run a single RoBERTa detector with sliding window for long texts."""
    words = text.split()
    if not words:
        return 0.0

    if len(words) <= 320:
        results = det_pipeline(text, truncation=True, max_length=512)
        return _extract_model_score(results)

    chunk_size = 320
    step = 240
    weighted_scores = []

    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]
        if len(chunk_words) < 20:
            continue

        chunk = " ".join(chunk_words)
        results = det_pipeline(chunk, truncation=True, max_length=512)
        weighted_scores.append((_extract_model_score(results), len(chunk_words)))

    if not weighted_scores:
        return 0.0

    scores = np.array([score for score, _weight in weighted_scores], dtype=np.float32)
    weights = np.array([weight for _score, weight in weighted_scores], dtype=np.float32)
    return _clamp(float(np.average(scores, weights=weights)))


def roberta_score(text: str) -> float:
    """Detector 1: RoBERTa-base (ChatGPT-trained)."""
    return _run_detector(detector1, text)


def roberta_large_score(text: str) -> float:
    """Detector 2: RoBERTa-large (OpenAI-trained)."""
    return _run_detector(detector2, text)


# ═══════════════════════════════════════════
# Perplexity & Binoculars-style detection
# ═══════════════════════════════════════════

def _compute_perplexity_with_model(text: str, tokenizer, model) -> float:
    cleaned = text.strip()
    if len(cleaned.split()) < 3:
        return 999.0

    encodings = tokenizer(cleaned, return_tensors="pt")
    input_ids = encodings["input_ids"].to(DEVICE)
    seq_len = input_ids.size(1)

    if seq_len < 2:
        return 999.0

    max_length = min(getattr(model.config, "n_positions", 1024), 1024)
    stride = min(256, max_length // 2)
    nlls = []
    prev_end_loc = 0

    for begin_loc in range(0, seq_len, stride):
        end_loc = min(begin_loc + max_length, seq_len)
        target_len = end_loc - prev_end_loc

        input_ids_slice = input_ids[:, begin_loc:end_loc]
        target_ids = input_ids_slice.clone()
        target_ids[:, :-target_len] = -100

        with torch.no_grad():
            outputs = model(input_ids_slice, labels=target_ids)

        nlls.append(outputs.loss * target_len)
        prev_end_loc = end_loc

        if end_loc >= seq_len:
            break

    if not nlls:
        return 999.0

    perplexity = torch.exp(torch.stack(nlls).sum() / max(seq_len - 1, 1)).item()
    if math.isnan(perplexity) or math.isinf(perplexity):
        return 999.0

    return float(perplexity)


def compute_perplexity(text: str) -> float:
    """Perplexity using GPT-2 small."""
    return _compute_perplexity_with_model(text, ppl_small_tokenizer, ppl_small_model)


def compute_perplexity_medium(text: str) -> float:
    """Perplexity using GPT-2 medium."""
    return _compute_perplexity_with_model(text, ppl_medium_tokenizer, ppl_medium_model)


def binoculars_score(text: str) -> float:
    """Binoculars-style: compare perplexity ratio between small and medium GPT-2.

    AI text has similar perplexity across model sizes (both predict it well).
    Human text shows a bigger gap (medium handles it better than small).

    Returns 0.0 (human) to 1.0 (AI).
    """
    ppl_small = compute_perplexity(text)
    ppl_medium = compute_perplexity_medium(text)

    if ppl_small > 900 or ppl_medium > 900:
        return 0.5  # Can't determine

    # Ratio: how much better is medium vs small?
    # Low ratio (close to 1.0) → both models equally good → AI text
    # High ratio (>> 1.0) → medium much better → human text
    ratio = ppl_small / max(ppl_medium, 1.0)

    if ratio < 1.15:
        return 0.92  # Very similar perplexity → strong AI signal
    if ratio < 1.30:
        return 0.78
    if ratio < 1.50:
        return 0.60
    if ratio < 1.80:
        return 0.40
    if ratio < 2.20:
        return 0.22
    return 0.08  # Big gap → likely human


def _perplexity_to_score(perplexity: float) -> float:
    if perplexity < 12:
        return 0.995
    if perplexity < 20:
        return 0.96
    if perplexity < 30:
        return 0.90
    if perplexity < 40:
        return 0.84
    if perplexity < 55:
        return 0.68
    if perplexity < 80:
        return 0.48
    if perplexity < 120:
        return 0.26
    if perplexity < 180:
        return 0.14
    return 0.06


def analyze_style(text: str, english_text: Optional[str] = None) -> dict:
    sentences = _split_sentences(text, min_chars=15)
    sentence_lengths = np.array([len(sentence.split()) for sentence in sentences], dtype=np.float32)

    burstiness_variance = float(np.var(sentence_lengths)) if sentence_lengths.size >= 2 else 0.0
    burstiness_cv = (
        float(variation(sentence_lengths))
        if sentence_lengths.size >= 2 and float(np.mean(sentence_lengths)) > 0
        else 0.0
    )

    perplexity_source = english_text.strip() if english_text and english_text.strip() else text
    perplexity = compute_perplexity(perplexity_source)
    perplexity_score = _perplexity_to_score(perplexity)

    if sentence_lengths.size < 2:
        burstiness_score = 0.50
    elif burstiness_variance < 12 and burstiness_cv < 0.35:
        burstiness_score = 0.88
    elif burstiness_variance < 20 and burstiness_cv < 0.45:
        burstiness_score = 0.76
    elif burstiness_variance < 35:
        burstiness_score = 0.58
    elif burstiness_variance < 60:
        burstiness_score = 0.34
    else:
        burstiness_score = 0.12

    style_score = perplexity_score * 0.65 + burstiness_score * 0.35

    if perplexity < 20:
        style_score += 0.14
    elif perplexity < 30:
        style_score += 0.10
    elif perplexity < 45:
        style_score += 0.05

    if sentence_lengths.size >= 2:
        if burstiness_variance < 12 and burstiness_cv < 0.35:
            style_score += 0.08
        elif burstiness_variance < 20 and burstiness_cv < 0.45:
            style_score += 0.04

    return {
        "style_score": _clamp(style_score),
        "perplexity": round(perplexity, 4),
        "perplexity_score": round(perplexity_score, 4),
        "burstiness": round(burstiness_variance, 4),
        "burstiness_cv": round(burstiness_cv, 4),
        "burstiness_score": round(_clamp(burstiness_score), 4),
        "sentence_count": int(sentence_lengths.size),
    }


# ═══════════════════════════════════════════
# Ensemble: combine all signals
# ═══════════════════════════════════════════

class TextRequest(BaseModel):
    text: str
    mode: str = "detect"
    task_type: str = "detect"
    intensity: str = "medium"


class ChunksRequest(BaseModel):
    chunks: list[dict]
    mode: str = "detect"
    task_type: str = "detect"
    intensity: str = "medium"


def _score_sentence_quick(sentence: str) -> float:
    perplexity = compute_perplexity(sentence)
    base_score = _perplexity_to_score(perplexity)

    if perplexity < 18:
        base_score += 0.08
    elif perplexity < 30:
        base_score += 0.05
    elif perplexity < 40:
        base_score += 0.03

    return _clamp(base_score)


def _analyze_sentences(text: str, global_score: float = 0.0) -> list[dict]:
    """Score each sentence relative to each other, then redistribute around the global score."""
    raw_sentences = re.split(r"(?<=[.!?:;])\s+", text)
    entries: list[dict] = []

    for sentence in raw_sentences:
        sentence = sentence.strip()
        if len(sentence) < 10:
            if entries:
                entries[-1]["text"] += " " + sentence
            continue

        if len(sentence.split()) < 5:
            entries.append({"text": sentence, "raw": None})
        else:
            ppl_score = _score_sentence_quick(sentence)
            sent_text = sentence
            if is_mostly_french(sentence):
                try:
                    sent_text = translate_to_english(sentence)
                except Exception:
                    sent_text = sentence
            rob_score = roberta_score(sent_text)
            combined = rob_score * 0.60 + ppl_score * 0.40
            entries.append({"text": sentence, "raw": combined})

    if not entries:
        return []

    raw_scores = [e["raw"] for e in entries if e["raw"] is not None]

    if not raw_scores:
        return [{"text": e["text"], "score": round(global_score * 100, 1)} for e in entries]

    # Sort raw scores to determine percentile rank of each sentence
    sorted_raw = sorted(raw_scores)
    n = len(sorted_raw)

    def percentile_rank(value: float) -> float:
        """Where does this value fall among all sentences? 0.0 = lowest, 1.0 = highest."""
        if n <= 1:
            return 0.5
        pos = 0
        for s in sorted_raw:
            if s < value:
                pos += 1
            elif s == value:
                pos += 0.5
                break
        return pos / n

    # Map percentile rank onto a score range centered on global_score.
    # The lowest-ranked sentence gets a score well below global,
    # the highest-ranked gets a score well above global.
    # The spread ensures visible green/red differentiation.
    global_pct = global_score * 100
    # Range: the lower the global score, the more room above; the higher, more room below.
    spread_below = min(global_pct, 40.0)     # How far below global the greenest sentence can go
    spread_above = min(100 - global_pct, 40.0)  # How far above global the reddest sentence can go

    result = []
    for entry in entries:
        if entry["raw"] is None:
            score = global_pct
        else:
            rank = percentile_rank(entry["raw"])
            # rank 0.0 → most human → global - spread_below
            # rank 0.5 → average → global
            # rank 1.0 → most AI → global + spread_above
            if rank <= 0.5:
                # Below average: interpolate between (global - spread_below) and global
                t = rank / 0.5  # 0.0 to 1.0
                score = (global_pct - spread_below) + t * spread_below
            else:
                # Above average: interpolate between global and (global + spread_above)
                t = (rank - 0.5) / 0.5  # 0.0 to 1.0
                score = global_pct + t * spread_above
            score = max(0.0, min(100.0, round(score, 1)))
        result.append({"text": entry["text"], "score": score})

    return result


def _build_result(global_score: float, scores: dict, style: dict, include_sentences: bool, text: str) -> dict:
    result = {
        "global_score": round(global_score, 4),
        "model_score": round(scores["roberta_base"], 4),
        "model_score_large": round(scores["roberta_large"], 4),
        "binoculars_score": round(scores["binoculars"], 4),
        "style_score": round(style["style_score"], 4),
        "perplexity": style["perplexity"],
        "perplexity_medium": round(scores.get("ppl_medium", 0), 4),
        "burstiness": style["burstiness"],
        "burstiness_cv": style["burstiness_cv"],
        "perplexity_score": style["perplexity_score"],
        "burstiness_score": style["burstiness_score"],
        # Compatibility aliases
        "ai_probability": round(global_score * 100, 2),
        "score_roberta": round(scores["roberta_base"], 4),
        "score_roberta_large": round(scores["roberta_large"], 4),
        "score_binoculars": round(scores["binoculars"], 4),
        "score_ppl": round(style["perplexity_score"], 4),
    }

    if include_sentences:
        result["sentences"] = _analyze_sentences(text, global_score)

    return result


def _detect_academic_density(text: str) -> float:
    """Detect academic writing markers. Returns 0.0 (not academic) to 1.0 (very academic).

    Academic text has citations, references, formal structure — these are strong
    human signals because LLMs rarely produce proper inline citations.
    """
    # Inline citations: (Author, Year), (Author et al., Year), (Name, Year; Name, Year)
    citations = re.findall(r"\([A-ZÀ-Ü][a-zà-ü]+(?:\s+et\s+al\.?)?,?\s*\d{4}[a-z]?\)", text)
    # Also match multi-author citations like (AUF et al., 2022)
    citations += re.findall(r"\([A-ZÀ-Ü]{2,}(?:\s+et\s+al\.?)?,?\s*\d{4}[a-z]?\)", text)
    # Reference-style markers
    citations += re.findall(r"\([^)]*\d{4}[a-z]?[^)]*\)", text)

    # Deduplicate
    citation_count = len(set(citations))

    # Count sentences for density
    sentence_count = max(len(re.split(r"(?<=[.!?])\s+", text)), 1)
    citation_density = citation_count / sentence_count

    # Academic vocabulary
    academic_words = [
        r"\bselon\b", r"\bd'après\b", r"\bétude\b", r"\brecherche\b",
        r"\banalyse\b", r"\blittérature\b", r"\bméthodologie\b",
        r"\bhypothèse\b", r"\brésultats\b", r"\bconclusion\b",
        r"\bcf\.\b", r"\bibid\b", r"\bop\.?\s*cit\b",
        r"\baccording\s+to\b", r"\bstudy\b", r"\bresearch\b",
        r"\bfindings\b", r"\bliterature\b", r"\bmethodology\b",
    ]
    word_count = max(len(text.split()), 1)
    academic_hits = sum(len(re.findall(p, text, re.IGNORECASE)) for p in academic_words)
    academic_word_density = academic_hits / word_count

    # Combine signals
    score = 0.0
    if citation_count >= 5:
        score += 0.50
    elif citation_count >= 3:
        score += 0.35
    elif citation_count >= 1:
        score += 0.20

    if citation_density >= 0.3:
        score += 0.25
    elif citation_density >= 0.15:
        score += 0.15

    if academic_word_density >= 0.02:
        score += 0.15
    elif academic_word_density >= 0.01:
        score += 0.08

    return min(score, 1.0)


def _analyze_single(text: str, include_sentences: bool = False) -> dict:
    text = text.strip()
    empty_scores = {"roberta_base": 0.0, "roberta_large": 0.0, "binoculars": 0.0, "ppl_medium": 0.0}

    if len(text) < 20:
        return _build_result(0.0, empty_scores, {
            "style_score": 0.0,
            "perplexity": 999.0,
            "burstiness": 0.0,
            "burstiness_cv": 0.0,
            "perplexity_score": 0.0,
            "burstiness_score": 0.0,
        }, include_sentences, text)

    english_text = text
    is_french = is_mostly_french(text)
    if is_french:
        english_text = translate_to_english(text)

    # ── Run all detectors ──────────────────────────────
    score_base = roberta_score(english_text)
    score_large = roberta_large_score(english_text)
    score_bino = binoculars_score(english_text)
    style = analyze_style(text, english_text=english_text)
    ppl_medium = compute_perplexity_medium(english_text)
    academic = _detect_academic_density(text)

    scores = {
        "roberta_base": score_base,
        "roberta_large": score_large,
        "binoculars": score_bino,
        "ppl_medium": ppl_medium,
    }

    # ── Ensemble: weighted vote ────────────────────────
    global_score = (
        score_large * 0.30
        + score_base * 0.20
        + score_bino * 0.25
        + style["style_score"] * 0.25
    )

    # ── Detector disagreement penalty ──────────────────
    # If RoBERTa-base and RoBERTa-large strongly disagree, one is wrong.
    # Disagreement = the text is ambiguous, reduce confidence.
    detector_gap = abs(score_base - score_large)
    if detector_gap > 0.50:
        # Massive disagreement — trust the lower score more
        global_score -= 0.12
    elif detector_gap > 0.35:
        global_score -= 0.06

    # ── Agreement boosters (only when detectors agree) ─
    ai_votes = sum(1 for s in [score_base, score_large, score_bino] if s >= 0.60)
    human_votes = sum(1 for s in [score_base, score_large, score_bino] if s < 0.30)

    if ai_votes >= 3:
        global_score += 0.08
    elif ai_votes >= 2 and detector_gap < 0.30:
        global_score += 0.04

    if human_votes >= 3:
        global_score -= 0.06
    elif human_votes >= 2:
        global_score -= 0.03

    # ── Academic text correction ───────────────────────
    # Academic writing (citations, references) is a strong human signal.
    # Formal academic style can fool AI detectors — correct for this.
    if academic >= 0.50:
        global_score -= 0.25  # Heavy correction for clearly academic text
    elif academic >= 0.30:
        global_score -= 0.15
    elif academic >= 0.15:
        global_score -= 0.08

    # ── Mild perplexity booster (only if non-academic) ─
    if academic < 0.20:
        if style["perplexity"] < 25:
            global_score += 0.06
        elif style["perplexity"] < 40:
            global_score += 0.03

    # ── Burstiness booster (only if non-academic) ──────
    if academic < 0.20:
        if style["burstiness"] < 12 and style["burstiness_cv"] < 0.35:
            global_score += 0.04
        elif style["burstiness"] < 20 and style["burstiness_cv"] < 0.45:
            global_score += 0.02

    # ── Strong human signal dampening ──────────────────
    if score_base < 0.15 and score_large < 0.15 and style["style_score"] < 0.25:
        global_score *= 0.65

    global_score = _clamp(global_score)
    return _build_result(global_score, scores, style, include_sentences, text)


def _weighted_average(results: list[tuple[float, float]]) -> float:
    if not results:
        return 0.0

    scores = np.array([score for score, _weight in results], dtype=np.float32)
    weights = np.array([weight for _score, weight in results], dtype=np.float32)
    return float(np.average(scores, weights=weights))


@app.post("/predict")
def predict(request: TextRequest):
    result = _analyze_single(request.text, include_sentences=True)
    result["mode"] = request.mode
    result["task_type"] = request.task_type
    result["intensity"] = request.intensity
    return result


@app.post("/predict-chunks")
def predict_chunks(request: ChunksRequest):
    results = []
    global_scores = []
    model_scores = []
    model_large_scores = []
    binoculars_scores = []
    style_scores = []
    perplexity_scores = []
    perplexities = []
    burstiness_scores = []
    burstiness_values = []

    for chunk in request.chunks:
        text = str(chunk.get("text", "")).strip()
        label = str(chunk.get("label", "Section"))

        if len(text) < 20:
            continue

        analysis = _analyze_single(text, include_sentences=True)
        weight = float(min(len(text), 3000))

        global_scores.append((analysis["global_score"], weight))
        model_scores.append((analysis["model_score"], weight))
        model_large_scores.append((analysis["model_score_large"], weight))
        binoculars_scores.append((analysis["binoculars_score"], weight))
        style_scores.append((analysis["style_score"], weight))
        perplexity_scores.append((analysis["perplexity_score"], weight))
        perplexities.append((analysis["perplexity"], weight))
        burstiness_scores.append((analysis["burstiness_score"], weight))
        burstiness_values.append((analysis["burstiness"], weight))

        results.append({
            "label": label,
            **analysis,
            "char_count": len(text),
            "text": text,
        })

    overall_global_score = _weighted_average(global_scores)

    return {
        "global_score": round(overall_global_score, 4),
        "model_score": round(_weighted_average(model_scores), 4),
        "model_score_large": round(_weighted_average(model_large_scores), 4),
        "binoculars_score": round(_weighted_average(binoculars_scores), 4),
        "style_score": round(_weighted_average(style_scores), 4),
        "perplexity_score": round(_weighted_average(perplexity_scores), 4),
        "perplexity": round(_weighted_average(perplexities), 4),
        "burstiness_score": round(_weighted_average(burstiness_scores), 4),
        "burstiness": round(_weighted_average(burstiness_values), 4),
        "ai_probability": round(overall_global_score * 100, 2),
        "chunks": results,
        "chunk_count": len(results),
        "mode": request.mode,
        "task_type": request.task_type,
        "intensity": request.intensity,
    }


# ═══════════════════════════════════════════
# Humanization engine
# ═══════════════════════════════════════════

# Common synonym mappings for humanization (both EN and FR)
_SYNONYMS = {
    # English
    "however": ["nevertheless", "yet", "still", "though", "on the other hand"],
    "therefore": ["thus", "hence", "consequently", "as a result", "so"],
    "furthermore": ["moreover", "additionally", "besides", "also", "in addition"],
    "significant": ["notable", "considerable", "substantial", "meaningful", "important"],
    "utilize": ["use", "employ", "apply", "leverage", "make use of"],
    "demonstrate": ["show", "illustrate", "reveal", "highlight", "exhibit"],
    "implement": ["apply", "execute", "carry out", "put into practice", "deploy"],
    "subsequently": ["later", "afterward", "then", "following that", "next"],
    "approximately": ["about", "roughly", "around", "nearly", "close to"],
    "facilitate": ["help", "assist", "enable", "support", "make easier"],
    "indicate": ["suggest", "show", "point to", "reveal", "signal"],
    "establish": ["set up", "create", "build", "found", "form"],
    "obtain": ["get", "acquire", "gain", "secure", "receive"],
    "provide": ["give", "offer", "supply", "deliver", "furnish"],
    "require": ["need", "demand", "call for", "necessitate", "involve"],
    "regarding": ["about", "concerning", "as for", "with respect to", "on the topic of"],
    # French
    "cependant": ["toutefois", "néanmoins", "pourtant", "malgré tout", "en revanche"],
    "par conséquent": ["donc", "ainsi", "de ce fait", "en conséquence", "dès lors"],
    "de plus": ["en outre", "par ailleurs", "qui plus est", "également", "aussi"],
    "important": ["considérable", "majeur", "notable", "significatif", "essentiel"],
    "utiliser": ["employer", "se servir de", "recourir à", "exploiter", "faire usage de"],
    "démontrer": ["montrer", "illustrer", "prouver", "mettre en évidence", "révéler"],
    "permettre": ["rendre possible", "autoriser", "donner la possibilité", "offrir", "favoriser"],
    "effectuer": ["réaliser", "accomplir", "mener à bien", "exécuter", "procéder à"],
    "obtenir": ["acquérir", "décrocher", "se procurer", "recevoir", "gagner"],
    "nécessaire": ["indispensable", "requis", "essentiel", "fondamental", "primordial"],
    "concernant": ["à propos de", "au sujet de", "quant à", "en ce qui concerne", "relatif à"],
    "afin de": ["pour", "dans le but de", "en vue de", "dans l'optique de", "de manière à"],
    "notamment": ["en particulier", "particulièrement", "surtout", "entre autres", "spécialement"],
    "ainsi": ["de cette façon", "de cette manière", "par ce biais", "de la sorte", "en procédant ainsi"],
}

# Transition / filler phrases to inject naturalness (FR + EN)
_FILLERS_FR = [
    "En fait,", "D'ailleurs,", "À vrai dire,", "Il faut noter que",
    "On le voit bien,", "Il faut pourtant noter que,", "Au fond,",
    "En clair,", "Pourtant,", "Certes,",
]

_FILLERS_EN = [
    "In fact,", "Actually,", "Interestingly,", "That said,",
    "To put it plainly,", "Still,", "At the same time,",
    "Put differently,", "And yet,", "Notably,",
]

_AGGRESSIVE_FILLERS_FR = [
    "En clair,", "Certes,", "Pourtant,", "C'est là que le bât blesse,",
    "Dit autrement,", "À bien regarder les choses,", "Dans les faits,",
]

_AGGRESSIVE_FILLERS_EN = [
    "Put bluntly,", "And yet,", "That is where things get tricky,",
    "Looked at closely,", "In concrete terms,", "Still,",
]

_FORMALITY_REWRITES_FR = [
    (r"\bil convient de souligner que\b", ["il faut noter que", "on voit aussi que"]),
    (r"\bil est important de noter que\b", ["il faut noter que", "on remarque aussi que"]),
    (r"\bil est possible de\b", ["on peut"]),
    (r"\bil apparaît que\b", ["on voit que", "il ressort que"]),
    (r"\bdans le cadre de\b", ["pour", "dans"]),
    (r"\bafin de\b", ["pour"]),
    (r"\bil s'agit de\b", ["c'est", "on parle de"]),
    (r"\bnous nous sommes demandé\b", ["nous avons fini par nous demander", "une question s'est vite imposée à nous"]),
    (r"\bcela permet de\b", ["cela aide à", "cela ouvre la voie à"]),
    (r"\bil devient possible de\b", ["on peut alors", "il devient plus simple de"]),
]

_FORMALITY_REWRITES_EN = [
    (r"\bit is important to note that\b", ["it is worth noting that", "it helps to note that"]),
    (r"\bit should be noted that\b", ["it is worth noting that", "it is useful to note that"]),
    (r"\bit is possible to\b", ["you can", "it becomes possible to"]),
    (r"\bin the context of\b", ["within", "for"]),
    (r"\bin order to\b", ["to"]),
    (r"\bit appears that\b", ["it seems that", "one can see that"]),
    (r"\bthis allows us to\b", ["this helps us", "this opens the way to"]),
]

_INTRO_MARKERS_FR = (
    "afin de", "pour", "dans le but de", "en pratique", "en réalité",
    "sur le terrain", "à ce stade", "dans ce contexte", "par ailleurs",
    "en revanche", "de plus", "en effet", "au fond", "en clair",
)

_INTRO_MARKERS_EN = (
    "in practice", "in reality", "in this context", "to", "in order to",
    "at this stage", "on the ground", "moreover", "however", "in fact",
)


def _replace_synonyms(text: str, probability: float = 0.3) -> str:
    """Replace words/phrases with synonyms at a given probability."""
    result = text
    for phrase, alternatives in _SYNONYMS.items():
        if phrase.lower() in result.lower():
            if random.random() < probability:
                replacement = random.choice(alternatives)
                # Preserve original case
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                match = pattern.search(result)
                if match:
                    original = match.group()
                    if original[0].isupper():
                        replacement = replacement[0].upper() + replacement[1:]
                    result = result[:match.start()] + replacement + result[match.end():]
    return result


def _chaos_probability(probability: float, temperature: float = 0.7, top_p: float = 0.9) -> float:
    return _clamp(
        probability * (0.65 + temperature * 0.45) * (0.80 + top_p * 0.25),
        0.0,
        0.98,
    )


def _apply_pattern_rewrites(text: str, rewrites: list[tuple[str, list[str]]], probability: float = 0.3) -> str:
    result = text

    for pattern, alternatives in rewrites:
        if random.random() >= probability:
            continue

        def replacer(match: re.Match) -> str:
            replacement = random.choice(alternatives)
            if match.group(0) and match.group(0)[0].isupper():
                return replacement[0].upper() + replacement[1:]
            return replacement

        result, count = re.subn(pattern, replacer, result, count=1, flags=re.IGNORECASE)
        if count:
            break

    return result


def _split_sentence_words(sentence: str) -> list[str]:
    return [word for word in sentence.strip().split() if word]


def _capitalize_fragment(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return cleaned
    return cleaned[0].upper() + cleaned[1:]


def _lowercase_fragment(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return cleaned
    return cleaned[0].lower() + cleaned[1:]


def _split_terminal_punctuation(sentence: str) -> tuple[str, str]:
    cleaned = sentence.strip()
    if cleaned and cleaned[-1] in ".!?":
        return cleaned[:-1].strip(), cleaned[-1]
    return cleaned, "."


def _normalize_humanized_text(text: str) -> str:
    result = text.strip()
    result = re.sub(r"\s+([,.;:!?])", r"\1", result)
    result = re.sub(r"([,.;:!?])(?=\S)", r"\1 ", result)
    result = re.sub(r"\s{2,}", " ", result)
    return result.strip()


def _choose_fillers(is_french: bool, aggressive: bool = False) -> list[str]:
    if aggressive:
        return _AGGRESSIVE_FILLERS_FR if is_french else _AGGRESSIVE_FILLERS_EN
    return _FILLERS_FR if is_french else _FILLERS_EN


def _shift_intro_clause(sentence: str, probability: float = 0.25, is_french: bool = False) -> str:
    if random.random() >= probability:
        return sentence

    core, punctuation = _split_terminal_punctuation(sentence)
    parts = [part.strip() for part in core.split(",", 1)]

    if len(parts) != 2:
        return sentence

    intro, main = parts
    intro_markers = _INTRO_MARKERS_FR if is_french else _INTRO_MARKERS_EN

    if len(intro.split()) > 12 or not intro.lower().startswith(intro_markers):
        return sentence

    return f"{_capitalize_fragment(main)}, {_lowercase_fragment(intro)}{punctuation}"


def _frontload_subordinate_clause(sentence: str, probability: float = 0.22, is_french: bool = False) -> str:
    if random.random() >= probability:
        return sentence

    core, punctuation = _split_terminal_punctuation(sentence)
    markers = (
        [" parce que ", " alors que ", " tandis que ", " quand ", " lorsque ", " même si "]
        if is_french
        else [" because ", " while ", " when ", " although ", " even if "]
    )

    for marker in markers:
        if marker in core.lower():
            index = core.lower().find(marker)
            main = core[:index].strip()
            clause = core[index + 1:].strip()

            if len(main.split()) >= 6 and len(clause.split()) >= 5:
                return f"{_capitalize_fragment(clause)}, {main[0].lower() + main[1:] if len(main) > 1 else main.lower()}{punctuation}"

    return sentence


def _reframe_colon_clause(sentence: str, probability: float = 0.18) -> list[str]:
    if random.random() >= probability or ":" not in sentence:
        return [sentence]

    core, punctuation = _split_terminal_punctuation(sentence)
    left, right = [part.strip() for part in core.split(":", 1)]

    if len(left.split()) < 3 or len(right.split()) < 4:
        return [sentence]

    return [f"{left}.", f"{_capitalize_fragment(right)}{punctuation}"]


def _split_long_sentence(sentence: str, probability: float = 0.25, is_french: bool = False) -> list[str]:
    if random.random() >= probability:
        return [sentence]

    core, punctuation = _split_terminal_punctuation(sentence)
    comma_parts = [part.strip() for part in re.split(r",\s+", core) if part.strip()]

    if len(comma_parts) >= 2:
        best_index = None
        total_words = len(core.split())
        running_words = 0
        best_gap = None

        for index in range(1, len(comma_parts)):
            running_words += len(comma_parts[index - 1].split())
            remaining_words = total_words - running_words
            if running_words < 6 or remaining_words < 6:
                continue

            gap = abs(running_words - remaining_words)
            if best_gap is None or gap < best_gap:
                best_gap = gap
                best_index = index

        if best_index is not None:
            left = ", ".join(comma_parts[:best_index]).strip()
            right = ", ".join(comma_parts[best_index:]).strip()
            return [f"{left}.", f"{_capitalize_fragment(right)}{punctuation}"]

    split_markers = [" mais ", " toutefois ", " cependant ", " but ", " however ", " yet "]
    for marker in split_markers:
        if marker in core.lower():
            index = core.lower().find(marker)
            left = core[:index].strip()
            right = core[index + len(marker):].strip()

            if len(left.split()) >= 6 and len(right.split()) >= 6:
                marker_word = marker.strip()
                return [f"{left}.", f"{_capitalize_fragment(marker_word)} {_lowercase_fragment(right)}{punctuation}"]

    return [sentence]


def _carve_punch_sentence(sentence: str, probability: float = 0.16) -> list[str]:
    if random.random() >= probability:
        return [sentence]

    words = _split_sentence_words(sentence)
    if len(words) < 18:
        return [sentence]

    cut = min(7, max(4, len(words) // 4))
    left_words = words[:-cut]
    right_words = words[-cut:]

    if len(left_words) < 10:
        return [sentence]

    _, punctuation = _split_terminal_punctuation(sentence)
    return [
        f"{' '.join(left_words).rstrip('.!?')}.",
        f"{_capitalize_fragment(' '.join(right_words).rstrip('.!?'))}{punctuation}",
    ]


def _rewrite_sentence(sentence: str, cfg: dict, is_french: bool = False, radical: bool = False) -> list[str]:
    rewritten = sentence.strip()
    if not rewritten:
        return []

    rewrites = _FORMALITY_REWRITES_FR if is_french else _FORMALITY_REWRITES_EN
    rewritten = _apply_pattern_rewrites(rewritten, rewrites, cfg["register_prob"])
    rewritten = _shift_intro_clause(rewritten, cfg["intro_shift_prob"], is_french)
    rewritten = _frontload_subordinate_clause(rewritten, cfg["clause_shift_prob"], is_french)
    rewritten = _replace_synonyms(rewritten, cfg["synonym_prob"])

    fragments: list[str] = []
    for fragment in _reframe_colon_clause(rewritten, cfg["colon_break_prob"]):
        fragments.extend(_split_long_sentence(fragment, cfg["split_prob"], is_french))

    if radical:
        radical_fragments: list[str] = []
        for fragment in fragments:
            radical_fragments.extend(_carve_punch_sentence(fragment, cfg["punch_prob"]))
        fragments = radical_fragments or fragments

    return [_normalize_humanized_text(fragment) for fragment in fragments if fragment.strip()]


def _sample_text_for_quality(text: str, max_sentences: int = 8, max_words: int = 900) -> str:
    sentences = _split_sentences(text, min_chars=5)
    if not sentences:
        words = text.split()
        return " ".join(words[:max_words]).strip()

    if len(sentences) > max_sentences:
        indices = sorted(set(np.linspace(0, len(sentences) - 1, max_sentences, dtype=int).tolist()))
        sentences = [sentences[index] for index in indices]

    sample = " ".join(sentences)
    words = sample.split()
    if len(words) > max_words:
        sample = " ".join(words[:max_words])

    return sample.strip()


def _estimate_humanization_metrics(text: str) -> dict:
    sample = _sample_text_for_quality(text)
    lexical_tokens = re.findall(r"\b[\w'-]+\b", sample.lower())
    lexical_variety = len(set(lexical_tokens)) / max(len(lexical_tokens), 1)
    sample_sentences = _split_sentences(sample, min_chars=5)
    openings = []

    for sentence in sample_sentences:
        tokens = re.findall(r"\b[\w'-]+\b", sentence.lower())
        if tokens:
            openings.append(" ".join(tokens[:2]))

    repeated_openings = max(0, len(openings) - len(set(openings)))

    try:
        analysis = _analyze_single(sample, include_sentences=False)
        detector_score = float(analysis["global_score"])
        style_score = float(analysis["style_score"])
        burstiness = float(analysis["burstiness"])
    except Exception:
        style = analyze_style(sample)
        detector_score = float(style["style_score"])
        style_score = float(style["style_score"])
        burstiness = float(style["burstiness"])

    naturalness = (
        (1.0 - detector_score) * 0.55
        + (1.0 - style_score) * 0.20
        + min(lexical_variety / 0.55, 1.0) * 0.15
        + min(burstiness / 45.0, 1.0) * 0.10
        - min(repeated_openings * 0.03, 0.15)
    )

    return {
        "detector_score": detector_score,
        "style_score": style_score,
        "burstiness": burstiness,
        "lexical_variety": lexical_variety,
        "naturalness": naturalness,
    }


def _retry_creativity_levels(intensity: str) -> list[float]:
    return {
        "light": [0.0, 0.14],
        "medium": [0.0, 0.16, 0.30],
        "aggressive": [0.10, 0.26, 0.42, 0.60, 0.78],
    }.get(intensity, [0.0, 0.16, 0.30])


def _candidate_is_better(candidate: dict, best: Optional[dict]) -> bool:
    if best is None:
        return True

    candidate_score = candidate["metrics"]["detector_score"]
    best_score = best["metrics"]["detector_score"]

    if candidate_score < best_score - 0.004:
        return True

    if abs(candidate_score - best_score) <= 0.004 and candidate["metrics"]["naturalness"] > best["metrics"]["naturalness"] + 0.02:
        return True

    return False


def _inject_fillers(
    sentences: list[str],
    probability: float = 0.15,
    is_french: bool = False,
    aggressive: bool = False,
) -> list[str]:
    """Inject filler/transition phrases at sentence boundaries."""
    fillers = _choose_fillers(is_french, aggressive=aggressive)
    result = []
    for i, sentence in enumerate(sentences):
        if i > 0 and i < len(sentences) - 1 and random.random() < probability:
            filler = random.choice(fillers)
            # Lowercase the first char of the sentence and prepend filler
            if sentence and sentence[0].isupper():
                sentence = filler + " " + sentence[0].lower() + sentence[1:]
            else:
                sentence = filler + " " + sentence
        result.append(sentence)
    return result


def _vary_sentence_lengths(sentences: list[str], intensity: float = 0.3, is_french: bool = False) -> list[str]:
    """Inject burstiness by occasionally splitting or merging sentences."""
    result = []
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        words = sentence.split()

        # Try splitting long sentences
        if len(words) > 18 and random.random() < intensity:
            split_markers = [" mais ", " et ", " car ", " or ", " but ", " and ", " because ", " since ", " while "]
            split_done = False
            for marker in split_markers:
                if marker in sentence.lower():
                    idx = sentence.lower().find(marker)
                    part1 = sentence[:idx].strip()
                    part2 = sentence[idx + len(marker):].strip()
                    if part1 and part2:
                        if not part1[-1] in ".!?":
                            part1 += "."
                        part2 = part2[0].upper() + part2[1:] if part2 else part2
                        result.append(part1)
                        result.append(part2)
                        split_done = True
                        break
            if not split_done:
                result.append(sentence)
        # Try merging short sentences
        elif len(words) < 8 and i + 1 < len(sentences) and random.random() < intensity * 0.5:
            next_sentence = sentences[i + 1]
            connectors = [", et ", ", puis ", "; "] if is_mostly_french(sentence) else [", and ", ", then ", "; "]
            connector = random.choice(connectors)
            merged = sentence.rstrip(".!?") + connector + next_sentence[0].lower() + next_sentence[1:] if next_sentence else sentence
            result.append(merged)
            i += 1  # skip next
        else:
            result.append(sentence)
        i += 1
    return result


def _enforce_burstiness_profile(
    sentences: list[str],
    intensity: float = 0.3,
    is_french: bool = False,
    radical: bool = False,
) -> list[str]:
    if len(sentences) < 2:
        return sentences

    result: list[str] = []
    expect_short = False

    for sentence in sentences:
        words = _split_sentence_words(sentence)

        if radical and not expect_short and len(words) >= 20:
            carved = _carve_punch_sentence(sentence, intensity)
            result.extend(carved)
            expect_short = True
            continue

        if expect_short and len(words) > 10:
            carved = _carve_punch_sentence(sentence, intensity * 0.75)
            if len(carved) > 1:
                result.extend(carved)
                expect_short = False
                continue

        result.append(sentence)
        expect_short = len(words) >= 16

    has_short = any(len(_split_sentence_words(sentence)) <= 6 for sentence in result)
    has_long = any(len(_split_sentence_words(sentence)) >= 18 for sentence in result)

    if radical and (not has_short or not has_long):
        adjusted: list[str] = []
        injected = False
        for sentence in result:
            if not injected and len(_split_sentence_words(sentence)) >= 18:
                adjusted.extend(_carve_punch_sentence(sentence, 0.95))
                injected = True
            else:
                adjusted.append(sentence)
        result = adjusted

    return result


def _humanize_text(text: str, intensity: str = "medium", creativity: float = 0.0, radical: bool = False) -> str:
    """Main humanization pipeline with structural rewrites and burstiness control."""
    text = text.strip()
    if len(text) < 20:
        return text

    is_french = is_mostly_french(text)

    # Intensity parameters
    configs = {
        "light": {
            "synonym_prob": 0.08,
            "filler_prob": 0.04,
            "burst_intensity": 0.18,
            "register_prob": 0.18,
            "intro_shift_prob": 0.16,
            "split_prob": 0.14,
            "clause_shift_prob": 0.12,
            "colon_break_prob": 0.08,
            "punch_prob": 0.10,
            "temperature": 0.62,
            "top_p": 0.78,
        },
        "medium": {
            "synonym_prob": 0.14,
            "filler_prob": 0.08,
            "burst_intensity": 0.30,
            "register_prob": 0.32,
            "intro_shift_prob": 0.30,
            "split_prob": 0.28,
            "clause_shift_prob": 0.24,
            "colon_break_prob": 0.14,
            "punch_prob": 0.18,
            "temperature": 0.74,
            "top_p": 0.84,
        },
        "aggressive": {
            "synonym_prob": 0.20,
            "filler_prob": 0.10,
            "burst_intensity": 0.44,
            "register_prob": 0.48,
            "intro_shift_prob": 0.46,
            "split_prob": 0.42,
            "clause_shift_prob": 0.40,
            "colon_break_prob": 0.28,
            "punch_prob": 0.32,
            "temperature": 0.90,
            "top_p": 0.92,
        },
    }
    base_cfg = configs.get(intensity, configs["medium"])
    cfg = {
        key: (
            _clamp(value + creativity * 0.12, 0.0, 0.99)
            if key in {"temperature", "top_p"}
            else _clamp(value + creativity * 0.18 if key != "burst_intensity" else value + creativity * 0.22, 0.0, 0.95)
        )
        for key, value in base_cfg.items()
    }

    for key in ("synonym_prob", "filler_prob", "register_prob", "intro_shift_prob", "split_prob", "clause_shift_prob", "colon_break_prob", "punch_prob"):
        cfg[key] = _chaos_probability(cfg[key], cfg["temperature"], cfg["top_p"])

    # Step 2: Split into sentences
    sentences = _split_sentences(text, min_chars=5)
    if not sentences:
        return text

    rewritten_sentences: list[str] = []
    for sentence in sentences:
        rewritten_sentences.extend(_rewrite_sentence(sentence, cfg, is_french, radical=radical))

    if not rewritten_sentences:
        rewritten_sentences = sentences

    # Step 3: Inject natural fillers
    sentences = _inject_fillers(
        rewritten_sentences,
        cfg["filler_prob"],
        is_french,
        aggressive=(intensity == "aggressive" or radical),
    )

    # Step 4: Vary sentence lengths (burstiness injection)
    sentences = _vary_sentence_lengths(sentences, cfg["burst_intensity"], is_french)
    sentences = _enforce_burstiness_profile(
        sentences,
        cfg["burst_intensity"],
        is_french,
        radical=(intensity == "aggressive" or radical),
    )

    # Step 5: Minor word-level perturbations for aggressive mode
    if intensity == "aggressive":
        new_sentences = []
        for s in sentences:
            words = s.split()
            # Occasionally swap adjacent words (keeps meaning mostly intact)
            for j in range(1, len(words) - 1):
                if random.random() < 0.03 and words[j].isalpha() and words[j + 1 if j + 1 < len(words) else j].isalpha():
                    # Only swap adjective-noun style pairs (short words)
                    if len(words[j]) < 8 and j + 1 < len(words) and len(words[j + 1]) < 8:
                        words[j], words[j + 1] = words[j + 1], words[j]
            new_sentences.append(" ".join(words))
        sentences = new_sentences

    return _normalize_humanized_text(" ".join(sentences))


def _humanize_with_retry(text: str, intensity: str, segment_texts: Optional[list[str]] = None) -> dict:
    baseline_metrics = _estimate_humanization_metrics(text)
    best: Optional[dict] = None

    for attempt_index, creativity in enumerate(_retry_creativity_levels(intensity), start=1):
        radical = intensity == "aggressive" and attempt_index >= 2

        if segment_texts is not None:
            candidate_segments = [
                _humanize_text(segment_text, intensity, creativity=creativity, radical=radical) if segment_text.strip() else segment_text
                for segment_text in segment_texts
            ]
            candidate_text = _normalize_humanized_text(" ".join(segment for segment in candidate_segments if segment.strip()))
        else:
            candidate_segments = None
            candidate_text = _humanize_text(text, intensity, creativity=creativity, radical=radical)

        candidate = {
            "text": candidate_text,
            "segments": candidate_segments,
            "attempt_index": attempt_index,
            "creativity": creativity,
            "metrics": _estimate_humanization_metrics(candidate_text),
        }

        if intensity == "aggressive" and candidate["metrics"]["naturalness"] < baseline_metrics["naturalness"]:
            continue

        if _candidate_is_better(candidate, best):
            best = candidate

        if (
            candidate["metrics"]["detector_score"] + 0.01 < baseline_metrics["detector_score"]
            and candidate["metrics"]["naturalness"] >= baseline_metrics["naturalness"] - 0.05
        ):
            break

    if best is None or best["metrics"]["detector_score"] > baseline_metrics["detector_score"] + 0.003:
        return {
            "text": text,
            "segments": segment_texts,
            "metrics": baseline_metrics,
            "baseline_metrics": baseline_metrics,
            "retry_count": 0 if best is None else best["attempt_index"] - 1,
            "used_fallback": True,
        }

    return {
        **best,
        "baseline_metrics": baseline_metrics,
        "retry_count": max(0, best["attempt_index"] - 1),
        "used_fallback": False,
    }


class HumanizeSegment(BaseModel):
    id: Optional[str | int] = None
    text: str


class HumanizeRequest(BaseModel):
    text: str
    intensity: str = "medium"
    mode: str = "manual-humanize"
    task_type: str = "humanize"
    segments: Optional[list[HumanizeSegment]] = None


def _humanize_segments(segments: list[HumanizeSegment], intensity: str) -> list[dict]:
    original_segments = [segment.text.strip() for segment in segments]
    original_text = _normalize_humanized_text(" ".join(segment for segment in original_segments if segment))
    selection = _humanize_with_retry(original_text, intensity, segment_texts=original_segments)
    selected_segments = selection["segments"] or original_segments

    result: list[dict] = []

    for index, segment in enumerate(segments):
        original_text = segment.text.strip()
        humanized_text = selected_segments[index] if index < len(selected_segments) else original_text

        result.append({
            "id": segment.id if segment.id is not None else index,
            "index": index,
            "original_text": original_text,
            "humanized_text": humanized_text,
        })

    return result


@app.post("/humanize")
def humanize(request: HumanizeRequest):
    """Humanize AI-detected text using paraphrasing techniques.

    Intensity levels:
    - "light": subtle changes, preserves original style
    - "medium": balanced naturalness and fidelity
    - "aggressive": deep rewriting, very different style
    """
    if request.intensity not in ("light", "medium", "aggressive"):
        request.intensity = "light" if request.intensity == "easy" else "medium"

    humanized_segments: list[dict] = []

    if request.segments:
        humanized_segments = _humanize_segments(request.segments, request.intensity)
        humanized = " ".join(segment["humanized_text"] for segment in humanized_segments if segment["humanized_text"]).strip()
        baseline_score = None
        final_score = None
        retry_count = None
        used_fallback = None
    else:
        selection = _humanize_with_retry(request.text, request.intensity)
        humanized = selection["text"]
        baseline_score = round(selection["baseline_metrics"]["detector_score"] * 100, 2)
        final_score = round(selection["metrics"]["detector_score"] * 100, 2)
        retry_count = selection["retry_count"]
        used_fallback = selection["used_fallback"]

    return {
        "humanized_text": humanized,
        "original_length": len(request.text),
        "humanized_length": len(humanized),
        "intensity": request.intensity,
        "mode": request.mode,
        "task_type": request.task_type,
        "segments": humanized_segments,
        "estimated_score_before": baseline_score,
        "estimated_score_after": final_score,
        "retry_count": retry_count,
        "used_fallback": used_fallback,
    }
