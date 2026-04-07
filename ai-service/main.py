import math
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


class ChunksRequest(BaseModel):
    chunks: list[dict]


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
    return _analyze_single(request.text, include_sentences=True)


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
    }
