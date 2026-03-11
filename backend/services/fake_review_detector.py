"""services/fake_review_detector.py – Fake review pattern detection."""
from __future__ import annotations
import re, logging, math
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger("safebasket.fake")

# Generic filler phrases common in fake reviews
GENERIC_PHRASES = [
    r"\bgreat product\b", r"\bhighly recommend\b", r"\bvery good\b",
    r"\bamazing product\b", r"\bexcellent product\b", r"\bperfect product\b",
    r"\bbest product\b", r"\blove (it|this product)\b", r"\bvery nice\b",
    r"\bgood quality\b", r"\bwaste of money\b", r"\bdo not buy\b",
    r"\b5 stars\b", r"\bfive stars\b", r"\bone star\b",
]
_GENERIC = [re.compile(p, re.IGNORECASE) for p in GENERIC_PHRASES]

@dataclass
class FakeReviewResult:
    risk_score: float  = 0.0   # 0–100
    risk_label: str    = "Low"
    signals: dict      = None

    def to_dict(self):
        return {"risk_score": round(self.risk_score, 1), "risk_label": self.risk_label, "signals": self.signals or {}}

def _text_length_score(reviews: list[dict]) -> float:
    """Short reviews (<20 chars) are suspicious."""
    short = sum(1 for r in reviews if len(r.get("text", "")) < 20)
    return (short / max(len(reviews), 1)) * 100

def _generic_phrase_score(reviews: list[dict]) -> float:
    """Reviews full of generic filler phrases are suspicious."""
    flagged = 0
    for r in reviews:
        text = r.get("text", "")
        if sum(1 for p in _GENERIC if p.search(text)) >= 2:
            flagged += 1
    return (flagged / max(len(reviews), 1)) * 100

def _punctuation_score(reviews: list[dict]) -> float:
    """Excessive punctuation (!!!, ???) is suspicious."""
    flagged = 0
    for r in reviews:
        text = r.get("text", "")
        if len(re.findall(r"[!?]{2,}", text)) >= 2:
            flagged += 1
    return (flagged / max(len(reviews), 1)) * 100

def _rating_spike_score(reviews: list[dict]) -> float:
    """If ratings are heavily polarised (all 5s or all 1s), suspicious."""
    ratings = [r.get("rating", 3) for r in reviews]
    if not ratings:
        return 0.0
    counter = Counter(round(r) for r in ratings)
    total   = len(ratings)
    max_pct = max(counter.values()) / total * 100
    # If >80% same rating → suspicious
    return max(0.0, (max_pct - 60) * 2) if max_pct > 60 else 0.0

def _similarity_score(reviews: list[dict]) -> float:
    """Simple word-overlap similarity between reviews. High overlap = suspicious."""
    texts = [set(r.get("text", "").lower().split()) for r in reviews if r.get("text")]
    if len(texts) < 2:
        return 0.0
    overlaps = []
    sample = texts[:min(30, len(texts))]
    for i in range(len(sample)):
        for j in range(i + 1, len(sample)):
            a, b = sample[i], sample[j]
            if not a or not b:
                continue
            intersection = len(a & b)
            union        = len(a | b)
            if union > 0:
                overlaps.append(intersection / union)
    if not overlaps:
        return 0.0
    avg_sim = sum(overlaps) / len(overlaps)
    return min(100.0, avg_sim * 300)  # scale up

def detect_fake_reviews(reviews: list[dict]) -> FakeReviewResult:
    if not reviews:
        return FakeReviewResult(risk_score=0.0, risk_label="Low", signals={})

    length_s  = _text_length_score(reviews)
    generic_s = _generic_phrase_score(reviews)
    punct_s   = _punctuation_score(reviews)
    spike_s   = _rating_spike_score(reviews)
    sim_s     = _similarity_score(reviews)

    # Weighted combination
    risk_score = (
        length_s  * 0.20 +
        generic_s * 0.30 +
        punct_s   * 0.15 +
        spike_s   * 0.20 +
        sim_s     * 0.15
    )
    risk_score = min(100.0, max(0.0, risk_score))

    if risk_score >= 60:
        label = "High"
    elif risk_score >= 30:
        label = "Moderate"
    else:
        label = "Low"

    signals = {
        "short_reviews_pct":   round(length_s, 1),
        "generic_phrases_pct": round(generic_s, 1),
        "excessive_punct_pct": round(punct_s, 1),
        "rating_spike_score":  round(spike_s, 1),
        "similarity_score":    round(sim_s, 1),
    }

    logger.info("FakeReview → score:%.1f label:%s", risk_score, label)
    return FakeReviewResult(risk_score=risk_score, risk_label=label, signals=signals)
