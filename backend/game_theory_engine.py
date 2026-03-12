"""game_theory_NUANCED.py - Smart Decision Making with Context

PHILOSOPHY:
- ONE factor shouldn't dominate the decision
- Consider USER NEEDS and product TYPE
- Look at the WHOLE PICTURE, not just trust score
- Give NUANCED recommendations based on context
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Dict, Any, List

logger = logging.getLogger("safebasket.gametheory")

@dataclass
class PurchaseAnalysis:
    """Nuanced purchase decision analysis"""
    
    information_reliability: float
    value_proposition: float
    risk_level: float
    market_confidence: float
    
    decision: str
    confidence: float
    reasoning: List[str]
    context_notes: List[str]  # NEW: Contextual advice
    
    information_risks: List[str]
    product_risks: List[str]
    financial_risks: List[str]
    
    potential_upside: str
    potential_downside: str
    alternatives_suggestion: str
    
    def to_dict(self):
        return {
            "scenario_type": "Purchase Decision Analysis",
            "decision_factors": {
                "information_reliability": round(self.information_reliability, 1),
                "value_proposition": round(self.value_proposition, 1),
                "risk_level": round(self.risk_level, 1),
                "market_confidence": round(self.market_confidence, 1),
            },
            "recommendation": {
                "decision": self.decision,
                "confidence": round(self.confidence, 1),
                "reasoning": self.reasoning,
                "context_notes": self.context_notes,
            },
            "risk_assessment": {
                "overall_risk_score": round(self.risk_level, 1),
                "risk_level": _risk_level_label(self.risk_level),
                "information_asymmetry": round(100 - self.information_reliability, 1),
                "market_uncertainty": round(100 - self.market_confidence, 1),
                "strategic_risk": round(self.risk_level, 1),
                "dominant_risk_factor": _identify_dominant_risk(self),
                "information_risks": self.information_risks,
                "product_risks": self.product_risks,
                "financial_risks": self.financial_risks,
            },
            "opportunity_analysis": {
                "potential_upside": self.potential_upside,
                "potential_downside": self.potential_downside,
                "alternatives_suggestion": self.alternatives_suggestion,
            },
            # Removed nash_equilibria to prevent React rendering issues
            # Frontend was trying to render {buyer, seller} objects directly
            "strategic_recommendation": self._generate_strategic_rec(),
            "confidence_score": round(self.confidence, 1),
            "alternative_strategies": self._generate_alternatives(),
        }
    
    def _generate_strategic_rec(self) -> str:
        base = f"Based on our analysis (confidence: {self.confidence:.0f}%), "
        
        if self.decision == "Buy":
            return base + "this product represents a solid purchase. The combination of factors suggests it will meet your needs."
        elif self.decision == "Maybe":
            return base + "this is a balanced decision. The product has both strengths and weaknesses - consider what matters most to you."
        else:
            return base + "we recommend exploring alternatives. The risks outweigh the benefits for most buyers."
    
    def _generate_alternatives(self) -> List[Dict]:
        alternatives = []
        
        if self.decision == "Don't Buy":
            alternatives.append({
                "strategy": "Find similar products with better ratings",
                "expected_payoff": 75.0,
                "conditions": "Look for 4+ stars with lower risk"
            })
        
        if self.decision == "Maybe":
            alternatives.append({
                "strategy": "Wait for a sale or discount",
                "expected_payoff": 65.0,
                "conditions": "Better value if price drops 15-20%"
            })
        
        return alternatives


def _risk_level_label(risk_score: float) -> str:
    if risk_score < 25:
        return "Low"
    elif risk_score < 50:
        return "Medium"
    else:
        return "High"


def _identify_dominant_risk(analysis: PurchaseAnalysis) -> str:
    risks = {
        "Information Quality": 100 - analysis.information_reliability,
        "Product Quality": analysis.risk_level,
        "Market Confidence": 100 - analysis.market_confidence,
    }
    return max(risks, key=risks.get)


def analyze_purchase_decision(product_data: Dict) -> PurchaseAnalysis:
    """
    NUANCED decision analysis - considers multiple factors with context
    
    Args:
        product_data: Dict with:
            - trust_score: 0-100
            - average_rating: 0-5
            - fake_review_risk: 0-100
            - grievance_rate: 0-100
            - sentiment_positive: 0-100
            - sentiment_negative: 0-100
            - total_reviews: int
    """
    
    logger.info("🎯 Starting NUANCED purchase decision analysis")
    
    # Extract data
    trust_score = product_data.get("trust_score", 50)
    rating = product_data.get("average_rating", 3.0)
    fake_risk = product_data.get("fake_review_risk", 50)
    grievance_rate = product_data.get("grievance_rate", 30)
    sentiment_pos = product_data.get("sentiment_positive", 50)
    sentiment_neg = product_data.get("sentiment_negative", 30)
    total_reviews = product_data.get("total_reviews", 0)
    
    logger.info(f"📊 Analyzing: trust={trust_score}, rating={rating:.1f}★, fake={fake_risk}%, grievance={grievance_rate}%")
    
    # ══════════════════════════════════════════════════════════════════
    # FACTOR 1: Information Reliability
    # ══════════════════════════════════════════════════════════════════
    
    info_reliability = 100.0
    info_risks = []
    
    if fake_risk > 70:
        info_reliability -= 35
        info_risks.append("High fake review risk - treat ratings cautiously")
    elif fake_risk > 50:
        info_reliability -= 20
        info_risks.append("Moderate fake review risk detected")
    elif fake_risk > 30:
        info_reliability -= 10
    
    if total_reviews < 10:
        info_reliability -= 25
        info_risks.append(f"Only {total_reviews} reviews - limited data")
    elif total_reviews < 30:
        info_reliability -= 12
    
    info_reliability = max(0, min(100, info_reliability))
    
    if not info_risks:
        info_risks.append("Reviews appear reliable")
    
    logger.info(f"📊 Information Reliability: {info_reliability:.1f}/100")
    
    # ══════════════════════════════════════════════════════════════════
    # FACTOR 2: Value Proposition
    # ══════════════════════════════════════════════════════════════════
    
    # Base on rating
    value_score = (rating / 5.0) * 100
    
    # Adjust for sentiment
    if sentiment_pos > 75:
        value_score = min(100, value_score + 10)
    elif sentiment_neg > 50:
        value_score = max(0, value_score - 15)
    
    logger.info(f"💰 Value Proposition: {value_score:.1f}/100")
    
    # ══════════════════════════════════════════════════════════════════
    # FACTOR 3: Risk Level (Derived from trust score)
    # ══════════════════════════════════════════════════════════════════
    
    risk_level = 100 - trust_score
    
    product_risks = []
    
    if rating < 3.5:
        product_risks.append(f"Below-average {rating:.1f}★ rating")
    
    if grievance_rate > 40:
        product_risks.append(f"High complaint rate ({grievance_rate:.0f}%)")
    elif grievance_rate > 25:
        product_risks.append(f"Notable complaints ({grievance_rate:.0f}%)")
    
    if not product_risks:
        product_risks.append("No major product issues detected")
    
    logger.info(f"⚠️ Risk Level: {risk_level:.1f}/100")
    
    # ══════════════════════════════════════════════════════════════════
    # FACTOR 4: Market Confidence
    # ══════════════════════════════════════════════════════════════════
    
    market_confidence = (info_reliability * 0.5) + (trust_score * 0.5)
    
    logger.info(f"📈 Market Confidence: {market_confidence:.1f}/100")
    
    # ══════════════════════════════════════════════════════════════════
    # DECISION: NUANCED MULTI-FACTOR ANALYSIS
    # ══════════════════════════════════════════════════════════════════
    
    # Calculate weighted decision score
    decision_score = (
        trust_score * 0.35 +           # Trust important but not dominant
        value_score * 0.30 +            # Value matters
        info_reliability * 0.20 +       # Need good data
        (100 - risk_level) * 0.15       # Risk matters
    )
    
    logger.info(f"🎯 Decision score: {decision_score:.1f}/100")
    
    reasoning = []
    context_notes = []
    
    # NUANCED DECISION LOGIC
    # ═══════════════════════════════════════════════════════════════════
    
    # SCENARIO 1: High trust + Good rating → BUY
    if trust_score >= 70 and rating >= 4.0:
        decision = "Buy"
        confidence = min(95, (trust_score + value_score) / 2)
        reasoning = [
            f"Solid trust score ({trust_score:.0f}/100)",
            f"Good {rating:.1f}★ customer rating",
        ]
        if info_reliability > 70:
            reasoning.append("Reviews appear authentic")
        context_notes.append("This is a reliable choice for most buyers")
    
    # SCENARIO 2: Moderate trust but excellent value → MAYBE (with context)
    elif trust_score >= 60 and rating >= 4.2:
        decision = "Maybe"
        confidence = 75
        reasoning = [
            f"Moderate trust score ({trust_score:.0f}/100)",
            f"Strong {rating:.1f}★ rating suggests good quality",
            "Some concerns but overall positive feedback",
        ]
        context_notes.append("Good option if the specific features match your needs")
        context_notes.append("Consider reading detailed reviews about your use case")
    
    # SCENARIO 3: Lower trust but specific strengths → MAYBE (nuanced)
    elif trust_score >= 50 and rating >= 3.8:
        decision = "Maybe"
        confidence = 65
        reasoning = [
            f"Fair trust score ({trust_score:.0f}/100)",
            f"Decent {rating:.1f}★ rating",
            "Mixed reviews - works well for some users",
        ]
        context_notes.append("Not the safest choice, but may work if you're flexible")
        context_notes.append("Consider if you can tolerate potential minor issues")
        
        if grievance_rate < 25:
            context_notes.append("Low complaint rate is a positive sign")
    
    # SCENARIO 3.5: Good trust but average rating → MAYBE (NEW - FIXES YOUR ISSUE)
    elif trust_score >= 65 and rating >= 3.3:
        decision = "Maybe"
        confidence = 70
        reasoning = [
            f"Good trust score ({trust_score:.0f}/100)",
            f"Average {rating:.1f}★ rating",
            "Product is generally reliable despite average rating",
        ]
        
        if fake_risk < 30:
            reasoning.append("Low fake review risk")
        if grievance_rate < 20:
            reasoning.append("Few customer complaints")
        
        context_notes.append("Solid mid-range option - may exceed expectations")
        context_notes.append("Read reviews to ensure it matches your specific needs")
    
    # SCENARIO 4: Good rating but trust concerns → MAYBE (with caution)
    elif rating >= 4.0 and fake_risk > 50:
        decision = "Maybe"
        confidence = 60
        reasoning = [
            f"Good {rating:.1f}★ rating",
            f"But high fake review risk ({fake_risk:.0f}%)",
            "Rating may not be fully reliable",
        ]
        context_notes.append("Proceed with caution - verify with detailed reviews")
        context_notes.append("Look for verified purchase reviews specifically")
    
    # SCENARIO 5: Low trust or poor rating → DON'T BUY
    else:
        decision = "Don't Buy"
        confidence = min(90, 100 - decision_score)
        reasoning = []
        
        if trust_score < 50:
            reasoning.append(f"Low trust score ({trust_score:.0f}/100)")
        if rating < 3.5:
            reasoning.append(f"Below-average {rating:.1f}★ rating")
        if grievance_rate > 35:
            reasoning.append(f"High complaint rate ({grievance_rate:.0f}%)")
        
        if not reasoning:
            reasoning.append("Overall risk outweighs potential benefits")
        
        context_notes.append("Better alternatives likely available")
    
    logger.info(f"🎯 DECISION: {decision} (confidence: {confidence:.1f}%)")
    
    # ══════════════════════════════════════════════════════════════════
    # OPPORTUNITY ANALYSIS
    # ══════════════════════════════════════════════════════════════════
    
    if rating >= 4.5:
        upside = f"Excellent {rating:.1f}★ rating - likely to exceed expectations"
    elif rating >= 4.0:
        upside = f"Strong {rating:.1f}★ rating - should meet expectations"
    elif rating >= 3.5:
        upside = f"Average {rating:.1f}★ rating - may work for specific needs"
    else:
        upside = f"Limited upside with {rating:.1f}★ rating"
    
    if risk_level > 60:
        downside = "High risk of disappointment or quality issues"
    elif risk_level > 40:
        downside = "Moderate risk - may not work for everyone"
    else:
        downside = "Low risk - generally reliable"
    
    if decision == "Don't Buy":
        alternatives = "Search for products with 4+ stars and trust scores above 70"
    elif decision == "Maybe":
        alternatives = "Compare 2-3 similar options before deciding"
    else:
        alternatives = "This is a solid choice - minimal need to look elsewhere"
    
    financial_risks = []
    if risk_level > 50:
        financial_risks.append("Risk of money wasted on poor quality")
    else:
        financial_risks.append("Low financial risk")
    
    return PurchaseAnalysis(
        information_reliability=info_reliability,
        value_proposition=value_score,
        risk_level=risk_level,
        market_confidence=market_confidence,
        decision=decision,
        confidence=confidence,
        reasoning=reasoning,
        context_notes=context_notes,
        information_risks=info_risks,
        product_risks=product_risks,
        financial_risks=financial_risks,
        potential_upside=upside,
        potential_downside=downside,
        alternatives_suggestion=alternatives,
    )
