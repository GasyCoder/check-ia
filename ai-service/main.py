import re
import math

import torch
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    GPT2LMHeadModel,
    GPT2TokenizerFast,
)

app = FastAPI()

# ── Model 1: RoBERTa classifier ──
detector = pipeline(
    "text-classification",
    model="roberta-base-openai-detector",
    top_k=None,
)

# ── Model 2: GPT-2 for perplexity analysis ──
gpt2_tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
gpt2_model = GPT2LMHeadModel.from_pretrained("gpt2")
gpt2_model.eval()

# ── Translation model (FR → EN) ──
translator_tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-fr-en")
translator_model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-fr-en")


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
    matches = sum(1 for p in french_markers if re.search(p, text_lower))
    return matches >= 5


def translate_to_english(text: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""

    for s in sentences:
        if len(current) + len(s) < 400:
            current += (" " + s) if current else s
        else:
            if current:
                chunks.append(current)
            current = s
    if current:
        chunks.append(current)

    parts = []
    for chunk in chunks:
        inputs = translator_tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)
        outputs = translator_model.generate(**inputs, max_length=512, num_beams=1)
        parts.append(translator_tokenizer.decode(outputs[0], skip_special_tokens=True))

    return " ".join(parts)


# ═══════════════════════════════════════════
# Text characteristics detection
# ═══════════════════════════════════════════

def detect_text_features(text: str) -> dict:
    """Detect features that help distinguish human vs AI text."""
    features = {}

    # Academic citations: (Author, 2024), (Name et al., 2023)
    citations = re.findall(r'\([A-ZÀ-Ü][a-zà-ü]+(?:\s+(?:et\s+al\.|&)\s*,?\s*)?(?:\d{4})\)', text)
    features["citation_count"] = len(citations)

    # Bibliographic references with page numbers
    refs = re.findall(r'\b(?:p\.\s*\d+|pp\.\s*\d+\s*-\s*\d+|ibid|op\.\s*cit)', text, re.I)
    features["ref_count"] = len(refs)

    # Sentence length variation (humans write varied lengths)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 5]
    if len(sentences) >= 3:
        lengths = [len(s.split()) for s in sentences]
        features["sentence_length_std"] = float(np.std(lengths))
        features["sentence_length_mean"] = float(np.mean(lengths))
        features["sentence_count"] = len(sentences)
    else:
        features["sentence_length_std"] = 0
        features["sentence_length_mean"] = 0
        features["sentence_count"] = len(sentences)

    # Rare/specialized vocabulary (proper nouns, acronyms, technical terms)
    acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
    features["acronym_count"] = len(acronyms)

    # Parenthetical content (humans use more parentheses for asides)
    parens = re.findall(r'\([^)]{5,}\)', text)
    features["parenthetical_count"] = len(parens)

    return features


def human_bias_from_features(features: dict) -> float:
    """
    Return a bias toward human (negative = more human, positive = more AI).
    Range: -0.25 to +0.05
    """
    bias = 0.0

    # Citations are a STRONG signal of human academic writing
    if features["citation_count"] >= 3:
        bias -= 0.20
    elif features["citation_count"] >= 1:
        bias -= 0.12

    # References
    if features["ref_count"] >= 2:
        bias -= 0.05

    # High sentence length variation = human
    if features["sentence_length_std"] > 8:
        bias -= 0.08
    elif features["sentence_length_std"] > 5:
        bias -= 0.04

    # Many acronyms = specialized/human text
    if features["acronym_count"] >= 5:
        bias -= 0.05

    return max(bias, -0.25)


# ═══════════════════════════════════════════
# Method 1: RoBERTa classifier score
# ═══════════════════════════════════════════

def get_fake_score(results):
    for r in results:
        label = r["label"].lower()
        if label in ("fake", "label_1"):
            return r["score"]
        if label in ("real", "label_0"):
            return 1.0 - r["score"]
    return 0.0


def roberta_score(text: str) -> float:
    words = text.split()

    if len(words) <= 300:
        results = detector(text, truncation=True, max_length=512)
        return get_fake_score(results[0] if isinstance(results[0], list) else results)

    chunk_size, step = 256, 200
    scores = []
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if len(chunk.split()) < 20:
            continue
        results = detector(chunk, truncation=True, max_length=512)
        scores.append(get_fake_score(results[0] if isinstance(results[0], list) else results))

    return sum(scores) / len(scores) if scores else 0.0


# ═══════════════════════════════════════════
# Method 2: Perplexity & burstiness analysis
# ═══════════════════════════════════════════

def compute_perplexity(text: str) -> float:
    encodings = gpt2_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    input_ids = encodings["input_ids"]

    if input_ids.size(1) < 2:
        return 999.0

    with torch.no_grad():
        outputs = gpt2_model(input_ids, labels=input_ids)

    return torch.exp(outputs.loss).item()


def perplexity_score(text: str) -> float:
    """
    AI text → low perplexity, low burstiness (uniform, predictable)
    Human text → higher perplexity, high burstiness (varied, creative)

    Returns a score 0.0 (human) to 1.0 (AI).
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 20]

    if len(sentences) < 3:
        ppl = compute_perplexity(text)
        if ppl < 20:
            return 0.92
        elif ppl < 40:
            return 0.70
        elif ppl < 80:
            return 0.40
        elif ppl < 150:
            return 0.20
        elif ppl < 300:
            return 0.10
        return 0.05

    # Compute per-sentence perplexity
    ppls = []
    for sentence in sentences:
        ppl = compute_perplexity(sentence)
        if not math.isinf(ppl) and not math.isnan(ppl) and ppl < 10000:
            ppls.append(ppl)

    if len(ppls) < 3:
        return 0.5

    avg_ppl = np.mean(ppls)
    std_ppl = np.std(ppls)
    burstiness = std_ppl / avg_ppl if avg_ppl > 0 else 0

    # ── Perplexity score (shifted thresholds — less aggressive) ──
    # Pure AI (ChatGPT etc): avg_ppl 15-40
    # AI-assisted/paraphrased: avg_ppl 40-80
    # Human formal/academic: avg_ppl 60-200
    # Human casual/creative: avg_ppl 150-500+
    if avg_ppl < 20:
        ppl_score = 0.95
    elif avg_ppl < 35:
        ppl_score = 0.82
    elif avg_ppl < 55:
        ppl_score = 0.60
    elif avg_ppl < 80:
        ppl_score = 0.35
    elif avg_ppl < 120:
        ppl_score = 0.18
    elif avg_ppl < 200:
        ppl_score = 0.08
    else:
        ppl_score = 0.03

    # ── Burstiness score (shifted — academic text is bursty too) ──
    # Pure AI: burstiness 0.15-0.4 (very uniform)
    # Human: burstiness 0.5-2.0+ (varied)
    if burstiness < 0.25:
        burst_score = 0.92
    elif burstiness < 0.4:
        burst_score = 0.65
    elif burstiness < 0.6:
        burst_score = 0.35
    elif burstiness < 0.85:
        burst_score = 0.15
    else:
        burst_score = 0.05

    return ppl_score * 0.60 + burst_score * 0.40


# ═══════════════════════════════════════════
# Combined prediction
# ═══════════════════════════════════════════

class TextRequest(BaseModel):
    text: str


class ChunksRequest(BaseModel):
    chunks: list[dict]


def _score_sentence_quick(sentence: str) -> float:
    """Quick per-sentence AI score using perplexity only (fast)."""
    ppl = compute_perplexity(sentence)
    if ppl < 15:
        return 0.95
    elif ppl < 30:
        return 0.80
    elif ppl < 50:
        return 0.60
    elif ppl < 80:
        return 0.35
    elif ppl < 130:
        return 0.18
    elif ppl < 250:
        return 0.08
    return 0.03


def _analyze_sentences(text: str) -> list:
    """Split text into sentences and score each one."""
    raw_sentences = re.split(r'(?<=[.!?:;])\s+', text)
    sentences = []

    for s in raw_sentences:
        s = s.strip()
        if len(s) < 10:
            # Too short to score — merge with previous if possible
            if sentences:
                sentences[-1]["text"] += " " + s
            continue
        sentences.append({"text": s})

    # Score each sentence
    for sent in sentences:
        if len(sent["text"].split()) < 5:
            sent["score"] = 0.0  # Too short, assume human
        else:
            sent["score"] = round(_score_sentence_quick(sent["text"]) * 100, 1)

    return sentences


def _analyze_single(text: str, include_sentences: bool = False) -> dict:
    """Analyze a single text and return detailed scores."""
    text = text.strip()
    if len(text) < 20:
        return {"ai_probability": 0, "score_roberta": 0, "score_ppl": 0}

    # Detect text features (citations, academic patterns, etc.)
    features = detect_text_features(text)
    human_bias = human_bias_from_features(features)

    # Translate if French
    english_text = text
    is_french = is_mostly_french(text)
    if is_french:
        english_text = translate_to_english(text)

    # Method 1: RoBERTa classifier
    score_roberta = roberta_score(english_text)

    # Method 2: Perplexity analysis (on ORIGINAL text)
    score_ppl = perplexity_score(text)

    # Also compute perplexity on translated text
    if english_text != text:
        score_ppl_en = perplexity_score(english_text)
        # Use average instead of max (less aggressive)
        score_ppl = score_ppl * 0.6 + score_ppl_en * 0.4

    # ── Final score: weighted combination ──
    # RoBERTa is trained on actual AI text, give it more weight
    # Perplexity is a heuristic, use as secondary signal
    final_score = score_roberta * 0.55 + score_ppl * 0.45

    # Apply human bias from text features (citations etc.)
    final_score = final_score + human_bias

    # Confidence boosting only when BOTH methods strongly agree
    if score_ppl > 0.80 and score_roberta > 0.75:
        final_score = max(final_score, 0.88)
    elif score_ppl < 0.15 and score_roberta < 0.20:
        # Both say human → push down
        final_score = min(final_score, 0.08)
    elif score_roberta < 0.25 and score_ppl < 0.40:
        # RoBERTa says human, perplexity moderate → trust RoBERTa
        final_score = score_roberta * 0.70 + score_ppl * 0.30

    # Clamp
    final_score = max(0.0, min(final_score, 0.999))

    result = {
        "ai_probability": round(final_score * 100, 2),
        "score_roberta": round(score_roberta, 4),
        "score_ppl": round(score_ppl, 4),
    }

    if include_sentences:
        result["sentences"] = _analyze_sentences(text)

    return result


@app.post("/predict")
def predict(request: TextRequest):
    result = _analyze_single(request.text, include_sentences=True)
    return {
        "ai_probability": result["ai_probability"],
        "sentences": result.get("sentences", []),
    }


@app.post("/predict-chunks")
def predict_chunks(request: ChunksRequest):
    """Analyze multiple text chunks and return per-chunk + aggregated results."""
    results = []
    total_weight = 0
    weighted_sum = 0

    for chunk in request.chunks:
        text = chunk.get("text", "").strip()
        label = chunk.get("label", "Section")

        if len(text) < 20:
            continue

        analysis = _analyze_single(text, include_sentences=True)

        weight = min(len(text), 3000)
        total_weight += weight
        weighted_sum += analysis["ai_probability"] * weight

        results.append({
            "label": label,
            "ai_probability": analysis["ai_probability"],
            "score_roberta": analysis["score_roberta"],
            "score_ppl": analysis["score_ppl"],
            "char_count": len(text),
            "text": text,
            "sentences": analysis.get("sentences", []),
        })

    overall = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0

    return {
        "ai_probability": overall,
        "chunks": results,
        "chunk_count": len(results),
    }
