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

DETECTOR_MODEL_NAME = "Hello-SimpleAI/chatgpt-detector-roberta"
PERPLEXITY_MODEL_NAME = "gpt2"
TRANSLATION_MODEL_NAME = "Helsinki-NLP/opus-mt-fr-en"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
PIPELINE_DEVICE = 0 if DEVICE.type == "cuda" else -1

# RoBERTa detector for GPT-4/GPT-5 style text detection.
detector = pipeline(
    "text-classification",
    model=DETECTOR_MODEL_NAME,
    tokenizer=DETECTOR_MODEL_NAME,
    top_k=None,
    device=PIPELINE_DEVICE,
)

# GPT-style language model for perplexity scoring.
perplexity_tokenizer = AutoTokenizer.from_pretrained(PERPLEXITY_MODEL_NAME, use_fast=True)
perplexity_model = AutoModelForCausalLM.from_pretrained(PERPLEXITY_MODEL_NAME).to(DEVICE)
perplexity_model.eval()

# Translation model to normalize French input before detector/perplexity scoring.
translator_tokenizer = AutoTokenizer.from_pretrained(TRANSLATION_MODEL_NAME)
translator_model = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATION_MODEL_NAME).to(DEVICE)
translator_model.eval()


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
# Method 1: RoBERTa detector
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


def roberta_score(text: str) -> float:
    words = text.split()
    if not words:
        return 0.0

    if len(words) <= 320:
        results = detector(text, truncation=True, max_length=512)
        return _extract_model_score(results)

    chunk_size = 320
    step = 240
    weighted_scores = []

    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]
        if len(chunk_words) < 20:
            continue

        chunk = " ".join(chunk_words)
        results = detector(chunk, truncation=True, max_length=512)
        weighted_scores.append((_extract_model_score(results), len(chunk_words)))

    if not weighted_scores:
        return 0.0

    scores = np.array([score for score, _weight in weighted_scores], dtype=np.float32)
    weights = np.array([weight for _score, weight in weighted_scores], dtype=np.float32)
    return _clamp(float(np.average(scores, weights=weights)))


# ═══════════════════════════════════════════
# Method 2: Perplexity & burstiness
# ═══════════════════════════════════════════

def compute_perplexity(text: str) -> float:
    cleaned = text.strip()
    if len(cleaned.split()) < 3:
        return 999.0

    encodings = perplexity_tokenizer(cleaned, return_tensors="pt")
    input_ids = encodings["input_ids"].to(DEVICE)
    seq_len = input_ids.size(1)

    if seq_len < 2:
        return 999.0

    max_length = min(getattr(perplexity_model.config, "n_positions", 1024), 1024)
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
            outputs = perplexity_model(input_ids_slice, labels=target_ids)

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

    # Low perplexity is the strongest secondary indicator for current LLM output.
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
# Combined prediction
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
    """Score each sentence relative to each other, then redistribute around the global score.

    Per-sentence RoBERTa/perplexity is used only for ranking (which sentences
    are MORE vs LESS likely AI).  The absolute scale is anchored to the global
    score so that the visual coloring is consistent with the gauge.
    """
    raw_sentences = re.split(r"(?<=[.!?:;])\s+", text)
    entries: list[dict] = []

    # --- Pass 1: collect raw per-sentence signals for ranking ---------------
    for sentence in raw_sentences:
        sentence = sentence.strip()
        if len(sentence) < 10:
            if entries:
                entries[-1]["text"] += " " + sentence
            continue

        if len(sentence.split()) < 5:
            # Too short – no independent signal
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

    # --- Pass 2: redistribute around global_score --------------------------
    raw_scores = [e["raw"] for e in entries if e["raw"] is not None]

    if not raw_scores:
        # All sentences too short – just assign global score
        return [{"text": e["text"], "score": round(global_score * 100, 1)} for e in entries]

    raw_mean = sum(raw_scores) / len(raw_scores)
    raw_std = (sum((r - raw_mean) ** 2 for r in raw_scores) / len(raw_scores)) ** 0.5

    result = []
    for entry in entries:
        if entry["raw"] is None:
            score = global_score * 100
        else:
            if raw_std < 0.01:
                # All sentences score the same – no variation to spread
                score = global_score * 100
            else:
                # How many std-devs above/below the mean this sentence is
                z = (entry["raw"] - raw_mean) / raw_std
                # Spread: each std-dev shifts ±12 percentage points from global
                score = global_score * 100 + z * 12.0
            score = max(0.0, min(100.0, score))
            score = round(score, 1)
        result.append({"text": entry["text"], "score": score})

    return result


def _build_result(global_score: float, model_score: float, style: dict, include_sentences: bool, text: str) -> dict:
    result = {
        "global_score": round(global_score, 4),
        "model_score": round(model_score, 4),
        "style_score": round(style["style_score"], 4),
        "perplexity": style["perplexity"],
        "burstiness": style["burstiness"],
        "burstiness_cv": style["burstiness_cv"],
        "perplexity_score": style["perplexity_score"],
        "burstiness_score": style["burstiness_score"],
        # Compatibility aliases for the Laravel app.
        "ai_probability": round(global_score * 100, 2),
        "score_roberta": round(model_score, 4),
        "score_ppl": round(style["perplexity_score"], 4),
    }

    if include_sentences:
        result["sentences"] = _analyze_sentences(text, global_score)

    return result


def _analyze_single(text: str, include_sentences: bool = False) -> dict:
    text = text.strip()
    if len(text) < 20:
        return _build_result(0.0, 0.0, {
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

    model_score = roberta_score(english_text)
    style = analyze_style(text, english_text=english_text)

    global_score = model_score * 0.50 + style["style_score"] * 0.50

    if style["perplexity"] < 30:
        global_score += 0.15 if (model_score >= 0.35 or style["style_score"] >= 0.68) else 0.08
    elif style["perplexity"] < 45:
        global_score += 0.06

    if style["burstiness"] < 12 and style["burstiness_cv"] < 0.35:
        global_score += 0.06
    elif style["burstiness"] < 20 and style["burstiness_cv"] < 0.45:
        global_score += 0.03

    if is_french:
        global_score += 0.10

    if model_score < 0.20 and style["style_score"] < 0.28:
        global_score *= 0.80

    global_score = _clamp(global_score)
    return _build_result(global_score, model_score, style, include_sentences, text)


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
        "style_score": round(_weighted_average(style_scores), 4),
        "perplexity_score": round(_weighted_average(perplexity_scores), 4),
        "perplexity": round(_weighted_average(perplexities), 4),
        "burstiness_score": round(_weighted_average(burstiness_scores), 4),
        "burstiness": round(_weighted_average(burstiness_values), 4),
        "ai_probability": round(overall_global_score * 100, 2),
        "chunks": results,
        "chunk_count": len(results),
    }
