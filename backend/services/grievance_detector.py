"""services/grievance_detector.py – Identifying product complaints."""
from __future__ import annotations
import logging
from dataclasses import dataclass

logger = logging.getLogger("safebasket.grievance")

@dataclass
class GrievanceResult:
    """Data container for grievance analysis results."""
    total_reviews_analyzed: int = 0
    total_flagged: int = 0
    grievance_rate: float = 0.0
    breakdown: dict = None
    top_complaint: str = "None"

    def to_dict(self):
        return {
            "total_reviews_analyzed": self.total_reviews_analyzed,
            "total_flagged": self.total_flagged,
            "grievance_rate": round(self.grievance_rate, 2),
            "breakdown": self.breakdown or {},
            "top_complaint": self.top_complaint
        }

# Categories of user grievances
GRIEVANCE_MAP = {
    "Quality Issues": [
        "broken", "damaged", "poor quality", "cheap material", "stopped working", 
        "defective", "fragile", "substandard", "fake material", "low grade"
    ],
    "Delivery & Shipping": [
        "late", "delayed", "slow delivery", "package opened", "missing item", 
        "never arrived", "tracking issues", "worst delivery"
    ],
    "Customer Service": [
        "no response", "rude", "refund refused", "warranty denied", 
        "support is bad", "ignored", "contacted many times"
    ],
    "Product Mismatch": [
        "different item", "wrong size", "color mismatch", "not as described", 
        "misleading photos", "fake product", "advertised wrongly"
    ]
}

def detect_grievances(reviews: list[dict]) -> GrievanceResult:
    """
    Analyzes list of reviews for specific grievances.
    Returns a GrievanceResult object.
    """
    if not reviews:
        return GrievanceResult()

    results = {cat: 0 for cat in GRIEVANCE_MAP}
    total_reviews = len(reviews)
    flagged_reviews_count = 0

    for review in reviews:
        text = (review.get("text") or "").lower()
        found_in_review = False
        
        for category, keywords in GRIEVANCE_MAP.items():
            for word in keywords:
                if word in text:
                    results[category] += 1
                    found_in_review = True
                    break # Count category once per review
        
        if found_in_review:
            flagged_reviews_count += 1

    grievance_rate = (flagged_reviews_count / total_reviews) * 100 if total_reviews > 0 else 0

    return GrievanceResult(
        total_reviews_analyzed=total_reviews,
        total_flagged=flagged_reviews_count,
        grievance_rate=grievance_rate,
        breakdown=results,
        top_complaint=max(results, key=results.get) if flagged_reviews_count > 0 else "None"
    )