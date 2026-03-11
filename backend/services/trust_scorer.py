"""trust_scorer_BULLETPROOF.py - Simple, Clear, WORKING Trust Scoring

NO BUGS. NO COMPLEXITY. JUST WORKS.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Dict, Any, List

logger = logging.getLogger("safebasket.trust")

@dataclass
class TrustScore:
    """Clear trust score with evidence"""
    score: float  # 0-100
    classification: str  # Excellent | Good | Fair | Poor | Very Poor
    recommendation: str
    explanation: str
    
    # Evidence
    rating_score: float
    authenticity_score: float
    reliability_score: float
    
    reasons_to_buy: List[str]
    reasons_to_avoid: List[str]
    critical_issues: List[str]
    
    # Components
    rating_component: float
    sentiment_component: float
    fake_risk_component: float
    grievance_component: float
    
    def to_dict(self):
        return {
            "score": round(self.score, 1),
            "classification": self.classification,
            "recommendation": self.recommendation,
            "explanation": self.explanation,
            "evidence": {
                "rating_score": round(self.rating_score, 1),
                "authenticity_score": round(self.authenticity_score, 1),
                "reliability_score": round(self.reliability_score, 1),
                "reasons_to_buy": self.reasons_to_buy,
                "reasons_to_avoid": self.reasons_to_avoid,
                "critical_issues": self.critical_issues,
            },
            "components": {
                "rating": round(self.rating_component, 1),
                "sentiment": round(self.sentiment_component, 1),
                "fake_risk": round(self.fake_risk_component, 1),
                "grievance": round(self.grievance_component, 1),
            }
        }


def compute_trust_score(
    average_rating: float,
    sentiment_result,
    grievance_result,
    fake_result,
    game_theory_result=None
) -> TrustScore:
    """
    BULLETPROOF trust scoring - Simple and accurate
    """
    
    logger.info(f"🎯 Computing trust score for {average_rating:.1f}★ product")
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 1: Base Score from Rating (Foundation)
    # ═══════════════════════════════════════════════════════════════════
    
    base_score = (average_rating / 5.0) * 100
    logger.info(f"   Base score: {base_score:.1f} from {average_rating:.1f}★")
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 2: Adjustments (Modest, not extreme)
    # ═══════════════════════════════════════════════════════════════════
    
    adjustments = 0
    red_flags = []
    
    # Fake review adjustment
    if fake_result.risk_score > 70:
        adjustments -= 20
        red_flags.append("Very high fake review risk")
    elif fake_result.risk_score > 50:
        adjustments -= 12
        red_flags.append("Significant fake review risk")
    elif fake_result.risk_score > 30:
        adjustments -= 5
    
    # Grievance adjustment
    if grievance_result.grievance_rate > 50:
        adjustments -= 15
        red_flags.append(f"Over {grievance_result.grievance_rate:.0f}% reviews report problems")
    elif grievance_result.grievance_rate > 30:
        adjustments -= 8
        red_flags.append(f"{grievance_result.grievance_rate:.0f}% complaint rate")
    
    # Sentiment adjustment (small boost/penalty)
    if sentiment_result.positive > 80:
        adjustments += 5
    elif sentiment_result.negative > 50:
        adjustments -= 10
        red_flags.append("Overwhelmingly negative sentiment")
    
    logger.info(f"   Adjustments: {adjustments:+.1f} points")
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 3: Calculate Final Score
    # ═══════════════════════════════════════════════════════════════════
    
    final_score = base_score + adjustments
    final_score = max(0, min(100, final_score))  # Clamp to 0-100
    
    logger.info(f"   Final score: {final_score:.1f}/100")
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 4: Classification (Clear Thresholds)
    # ═══════════════════════════════════════════════════════════════════
    
    if final_score >= 85:
        classification = "Excellent"
    elif final_score >= 75:
        classification = "Good"
    elif final_score >= 60:
        classification = "Fair"
    elif final_score >= 45:
        classification = "Poor"
    else:
        classification = "Very Poor"
    
    # Safety: Can't be Excellent/Good with red flags
    if red_flags and classification in ["Excellent", "Good"]:
        classification = "Fair"
        final_score = min(final_score, 70)
    
    # Safety: Low rating can't be good
    if average_rating < 4.0 and classification == "Excellent":
        classification = "Good"
    if average_rating < 3.5 and classification in ["Excellent", "Good"]:
        classification = "Fair"
    if average_rating < 3.0 and classification == "Fair":
        classification = "Poor"
    
    logger.info(f"   Classification: {classification}")
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 5: Build Clear Reasons
    # ═══════════════════════════════════════════════════════════════════
    
    reasons_to_buy = []
    reasons_to_avoid = []
    
    # Positive signals
    if average_rating >= 4.5:
        reasons_to_buy.append(f"Excellent {average_rating:.1f}★ rating")
    elif average_rating >= 4.0:
        reasons_to_buy.append(f"Strong {average_rating:.1f}★ rating")
    elif average_rating >= 3.5:
        reasons_to_buy.append(f"Decent {average_rating:.1f}★ rating")
    
    if sentiment_result.positive > 70:
        reasons_to_buy.append(f"{sentiment_result.positive:.0f}% positive reviews")
    
    if fake_result.risk_score < 30:
        reasons_to_buy.append("Low fake review risk")
    
    if grievance_result.grievance_rate < 15:
        reasons_to_buy.append("Very few customer complaints")
    
    # Negative signals
    if average_rating < 3.5:
        reasons_to_avoid.append(f"Below-average {average_rating:.1f}★ rating")
    
    if sentiment_result.negative > 30:
        reasons_to_avoid.append(f"{sentiment_result.negative:.0f}% negative reviews")
    
    if fake_result.risk_score > 40:
        reasons_to_avoid.append(f"{fake_result.risk_label} fake review risk")
    
    if grievance_result.grievance_rate > 25:
        reasons_to_avoid.append(f"{grievance_result.grievance_rate:.0f}% of reviews mention issues")
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 6: Generate Recommendation
    # ═══════════════════════════════════════════════════════════════════
    
    if classification == "Excellent":
        recommendation = f"✅ HIGHLY RECOMMENDED - Excellent {average_rating:.1f}★ product with {final_score:.0f}/100 trust score"
    elif classification == "Good":
        recommendation = f"✅ RECOMMENDED - Good {average_rating:.1f}★ product with {final_score:.0f}/100 trust score"
    elif classification == "Fair":
        recommendation = f"⚠️ CONSIDER CAREFULLY - Average {average_rating:.1f}★ product with {final_score:.0f}/100 trust score"
    elif classification == "Poor":
        recommendation = f"🚫 NOT RECOMMENDED - Poor {average_rating:.1f}★ product with {final_score:.0f}/100 trust score"
    else:
        recommendation = f"🚫 STRONGLY NOT RECOMMENDED - Very poor {average_rating:.1f}★ product with {final_score:.0f}/100 trust score"
    
    explanation = _generate_explanation(
        final_score, base_score, adjustments,
        average_rating, reasons_to_buy, reasons_to_avoid, red_flags
    )
    
    # Component scores
    rating_component = base_score
    sentiment_component = sentiment_result.positive
    fake_risk_component = 100 - fake_result.risk_score
    grievance_component = 100 - grievance_result.grievance_rate
    
    # Sub-scores
    rating_score = base_score
    authenticity_score = 100 - fake_result.risk_score
    reliability_score = 100 - grievance_result.grievance_rate
    
    logger.info(f"✅ Trust score complete: {final_score:.1f}/100 ({classification})")
    
    return TrustScore(
        score=final_score,
        classification=classification,
        recommendation=recommendation,
        explanation=explanation,
        rating_score=rating_score,
        authenticity_score=authenticity_score,
        reliability_score=reliability_score,
        reasons_to_buy=reasons_to_buy,
        reasons_to_avoid=reasons_to_avoid,
        critical_issues=red_flags,
        rating_component=rating_component,
        sentiment_component=sentiment_component,
        fake_risk_component=fake_risk_component,
        grievance_component=grievance_component,
    )


def _generate_explanation(
    final_score: float,
    base_score: float,
    adjustments: float,
    rating: float,
    reasons_to_buy: List[str],
    reasons_to_avoid: List[str],
    red_flags: List[str]
) -> str:
    """Generate clear explanation"""
    
    parts = [
        f"Trust Score: {final_score:.0f}/100",
        f"Rating: {rating:.1f} stars → Base score {base_score:.0f}",
        f"Adjustments: {adjustments:+.0f} points",
        "",
    ]
    
    if reasons_to_buy:
        parts.append("Strengths:")
        for reason in reasons_to_buy:
            parts.append(f"  • {reason}")
        parts.append("")
    
    if reasons_to_avoid:
        parts.append("Concerns:")
        for reason in reasons_to_avoid:
            parts.append(f"  • {reason}")
        parts.append("")
    
    if red_flags:
        parts.append("Critical Issues:")
        for flag in red_flags:
            parts.append(f"  • {flag}")
    
    return "\n".join(parts)
