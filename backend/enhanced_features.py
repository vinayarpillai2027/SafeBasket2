"""enhanced_features.py - Advanced features to make SafeBasket more valuable than basic rating sites"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass
from collections import Counter
from datetime import datetime, timedelta

logger = logging.getLogger("safebasket.enhanced")

# ══════════════════════════════════════════════════════════════════════════════
#  FEATURE 1: Detailed Grievance Breakdown with Specific Mentions
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EnhancedGrievance:
    category: str
    count: int
    percentage: float
    severity: str  # Low, Medium, High
    example_phrases: list[str]
    recommendation: str

def get_detailed_grievances(reviews: list[dict]) -> dict:
    """
    Returns specific grievance mentions that can populate the Risk Alerts dashboard
    """
    grievance_categories = {
        "Quality Issues": {
            "keywords": ["broken", "damaged", "poor quality", "cheap", "stopped working", 
                        "defective", "fragile", "fake", "counterfeit", "not genuine"],
            "severity_triggers": ["completely broken", "totally damaged", "worst quality"],
        },
        "Delivery Problems": {
            "keywords": ["late", "delayed", "never arrived", "missing", "lost package",
                        "damaged in shipping", "wrong address", "tracking"],
            "severity_triggers": ["never received", "still waiting", "month late"],
        },
        "Misleading Description": {
            "keywords": ["not as described", "different product", "wrong item", "misleading",
                        "fake photos", "color mismatch", "size wrong", "false advertising"],
            "severity_triggers": ["completely different", "total scam", "nothing like"],
        },
        "Customer Service": {
            "keywords": ["no response", "rude", "unhelpful", "refused refund", "warranty denied",
                        "ignored", "poor support", "can't contact", "no help"],
            "severity_triggers": ["never responded", "hung up", "blocked me"],
        },
        "Safety Concerns": {
            "keywords": ["dangerous", "fire hazard", "toxic", "unsafe", "injury", "hurt",
                        "sharp edges", "overheating", "electrical shock", "chemical smell"],
            "severity_triggers": ["caught fire", "injured", "hospital", "burned"],
        },
        "Value for Money": {
            "keywords": ["overpriced", "not worth", "waste of money", "too expensive",
                        "cheaper elsewhere", "poor value", "rip off", "scam"],
            "severity_triggers": ["total waste", "biggest scam", "complete rip-off"],
        }
    }
    
    results = []
    total_reviews = len(reviews)
    
    for category, data in grievance_categories.items():
        mentions = []
        severity_count = 0
        
        for review in reviews:
            text = (review.get("text") or "").lower()
            
            # Check for keywords
            for keyword in data["keywords"]:
                if keyword in text:
                    # Extract surrounding context (50 chars on each side)
                    match_pos = text.find(keyword)
                    start = max(0, match_pos - 50)
                    end = min(len(text), match_pos + len(keyword) + 50)
                    context = text[start:end].strip()
                    mentions.append(context)
                    break  # One mention per review per category
            
            # Check severity
            for trigger in data["severity_triggers"]:
                if trigger in text:
                    severity_count += 1
                    break
        
        if mentions:
            count = len(mentions)
            percentage = (count / total_reviews) * 100
            
            # Determine severity
            if severity_count > count * 0.3 or percentage > 40:
                severity = "High"
            elif percentage > 20 or severity_count > 0:
                severity = "Medium"
            else:
                severity = "Low"
            
            # Generate recommendation
            if category == "Safety Concerns" and severity == "High":
                recommendation = "🚫 AVOID - Safety issues reported"
            elif severity == "High":
                recommendation = f"⚠️ Critical: {count} reports of {category.lower()}"
            elif severity == "Medium":
                recommendation = f"⚠️ Consider: {count} mentions of {category.lower()}"
            else:
                recommendation = f"ℹ️ Minor: {count} reports (monitor this)"
            
            results.append(EnhancedGrievance(
                category=category,
                count=count,
                percentage=round(percentage, 1),
                severity=severity,
                example_phrases=mentions[:3],  # Top 3 examples
                recommendation=recommendation
            ))
    
    # Sort by severity and count
    severity_order = {"High": 0, "Medium": 1, "Low": 2}
    results.sort(key=lambda x: (severity_order[x.severity], -x.count))
    
    return {
        "grievances": [
            {
                "category": g.category,
                "mentions": g.count,
                "percentage": g.percentage,
                "severity": g.severity,
                "examples": g.example_phrases,
                "recommendation": g.recommendation
            }
            for g in results
        ],
        "total_flagged": sum(g.count for g in results),
        "highest_risk": results[0].category if results else "None"
    }

# ══════════════════════════════════════════════════════════════════════════════
#  FEATURE 2: Review Timeline Analysis
# ══════════════════════════════════════════════════════════════════════════════

def analyze_review_timeline(reviews: list[dict]) -> dict:
    """
    Detects suspicious patterns in review posting times
    E.g., 20 reviews posted on same day = likely fake
    """
    if not reviews:
        return {"suspicious": False}
    
    # Extract dates from reviews (if available)
    dates = []
    for review in reviews:
        if "date" in review:
            dates.append(review["date"])
    
    if len(dates) < 5:
        return {
            "suspicious": False,
            "reason": "Not enough date data available",
            "pattern": "unknown"
        }
    
    # Count reviews per day
    date_counts = Counter(dates)
    max_per_day = max(date_counts.values())
    total_days = len(date_counts)
    
    # Detection logic
    suspicious = False
    reason = ""
    pattern = "normal"
    
    if max_per_day > len(reviews) * 0.5:
        suspicious = True
        reason = f"{max_per_day} reviews posted on single day (burst pattern)"
        pattern = "burst"
    elif total_days < 3 and len(reviews) > 10:
        suspicious = True
        reason = f"All reviews within {total_days} days"
        pattern = "compressed"
    elif len(reviews) > 20 and total_days == len(reviews):
        # Too uniform - one review per day like clockwork
        suspicious = True
        reason = "Perfectly distributed reviews (too uniform)"
        pattern = "uniform"
    
    return {
        "suspicious": suspicious,
        "reason": reason,
        "pattern": pattern,
        "reviews_per_day_max": max_per_day,
        "total_days_span": total_days
    }

# ══════════════════════════════════════════════════════════════════════════════
#  FEATURE 3: Comparative Pricing Analysis
# ══════════════════════════════════════════════════════════════════════════════

def extract_price_from_text(text: str) -> float | None:
    """Extract price from review text or product description"""
    # Match patterns like: ₹1,299 | $99.99 | Rs.500 | 1299 rupees
    patterns = [
        r'[₹$]\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # ₹1,299.00 or $99.99
        r'(?:Rs\.?|INR)\s*(\d{1,3}(?:,\d{3})*)',      # Rs.1299
        r'(\d{1,3}(?:,\d{3})*)\s*(?:rupees|dollars)',  # 1299 rupees
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except:
                pass
    return None

def analyze_value_perception(reviews: list[dict], product_name: str = "") -> dict:
    """
    Analyzes if users think the product is overpriced or good value
    """
    value_positive = ["worth it", "good value", "great price", "affordable", 
                     "reasonable", "cheap", "best price", "value for money"]
    value_negative = ["overpriced", "expensive", "waste", "not worth", 
                     "too costly", "rip off", "cheaper elsewhere", "save money"]
    
    positive_count = 0
    negative_count = 0
    prices_mentioned = []
    
    for review in reviews:
        text = (review.get("text") or "").lower()
        
        # Check value sentiment
        if any(phrase in text for phrase in value_positive):
            positive_count += 1
        if any(phrase in text for phrase in value_negative):
            negative_count += 1
        
        # Extract price mentions
        price = extract_price_from_text(text)
        if price:
            prices_mentioned.append(price)
    
    total_value_mentions = positive_count + negative_count
    
    if total_value_mentions == 0:
        verdict = "No value feedback"
        score = 50  # Neutral
    else:
        positive_pct = (positive_count / total_value_mentions) * 100
        if positive_pct >= 70:
            verdict = "Good value for money"
            score = 80
        elif positive_pct >= 40:
            verdict = "Mixed opinions on value"
            score = 50
        else:
            verdict = "Users report overpricing"
            score = 20
    
    avg_price = sum(prices_mentioned) / len(prices_mentioned) if prices_mentioned else None
    
    return {
        "value_verdict": verdict,
        "value_score": score,
        "positive_mentions": positive_count,
        "negative_mentions": negative_count,
        "average_price_mentioned": round(avg_price, 2) if avg_price else None,
        "price_range": f"₹{min(prices_mentioned):.0f} - ₹{max(prices_mentioned):.0f}" if len(prices_mentioned) > 1 else None
    }

# ══════════════════════════════════════════════════════════════════════════════
#  FEATURE 4: Reviewer Credibility Score
# ══════════════════════════════════════════════════════════════════════════════

def assess_reviewer_credibility(reviews: list[dict]) -> dict:
    """
    Attempts to gauge if reviewers seem genuine
    """
    verified_count = 0
    detailed_reviews = 0
    generic_reviews = 0
    one_time_reviewers = 0
    
    for review in reviews:
        text = review.get("text", "")
        is_verified = review.get("verified_purchase", False)
        reviewer_id = review.get("reviewer_id", "")
        
        if is_verified:
            verified_count += 1
        
        # Detailed review = >100 chars with specific details
        if len(text) > 100 and any(word in text.lower() for word in 
                                   ["days", "weeks", "used", "purchased", "experience"]):
            detailed_reviews += 1
        
        # Generic = short and uses generic phrases
        if len(text) < 50 or any(phrase in text.lower() for phrase in 
                                ["good product", "nice", "love it", "bad", "worst"]):
            generic_reviews += 1
    
    total = len(reviews)
    credibility_score = (
        (verified_count / total * 40) +
        (detailed_reviews / total * 40) +
        ((total - generic_reviews) / total * 20)
    )
    
    if credibility_score >= 70:
        assessment = "High - Reviews appear genuine"
    elif credibility_score >= 40:
        assessment = "Medium - Mixed credibility signals"
    else:
        assessment = "Low - Many generic/suspicious reviews"
    
    return {
        "credibility_score": round(credibility_score, 1),
        "assessment": assessment,
        "verified_purchases": verified_count,
        "detailed_reviews": detailed_reviews,
        "generic_reviews": generic_reviews,
        "total_reviewed": total
    }

# ══════════════════════════════════════════════════════════════════════════════
#  FEATURE 5: Smart Recommendations
# ══════════════════════════════════════════════════════════════════════════════

def generate_smart_recommendation(trust_score: float, grievances: dict, 
                                 sentiment: dict, fake_risk: float) -> dict:
    """
    Provides actionable recommendations beyond simple buy/don't buy
    """
    recommendations = []
    
    # Based on trust score
    if trust_score >= 70:
        recommendations.append("✅ Generally safe to purchase")
    elif trust_score >= 40:
        recommendations.append("⚠️ Proceed with caution - read specific issues below")
    else:
        recommendations.append("🚫 High risk - consider alternatives")
    
    # Based on grievances
    if grievances.get("total_flagged", 0) > 0:
        top_issues = [g for g in grievances.get("grievances", []) if g["severity"] in ["High", "Medium"]]
        if top_issues:
            recommendations.append(f"⚠️ Watch out for: {', '.join([g['category'] for g in top_issues[:2]])}")
    
    # Based on fake reviews
    if fake_risk > 60:
        recommendations.append("🚨 High fake review risk - verify with other sources")
    elif fake_risk > 30:
        recommendations.append("⚠️ Some review manipulation detected")
    
    # Based on sentiment distribution
    positive_pct = sentiment.get("positive", 0)
    negative_pct = sentiment.get("negative", 0)
    
    if negative_pct > 40:
        recommendations.append(f"⚠️ {negative_pct:.0f}% negative sentiment - check common complaints")
    elif positive_pct > 70:
        recommendations.append(f"✓ {positive_pct:.0f}% positive feedback")
    
    # Specific actions
    actions = []
    if trust_score < 60:
        actions.append("Compare with similar products")
        actions.append("Check seller reputation separately")
    if fake_risk > 40:
        actions.append("Look for verified purchase reviews")
        actions.append("Cross-reference with other platforms")
    if grievances.get("total_flagged", 0) > len(grievances.get("grievances", [])) * 0.3:
        actions.append("Read negative reviews carefully")
        actions.append("Check return/warranty policy")
    
    return {
        "summary_recommendations": recommendations,
        "action_items": actions,
        "risk_level": "High" if trust_score < 40 else "Medium" if trust_score < 70 else "Low",
        "confidence": "High" if len(sentiment) > 20 else "Medium" if len(sentiment) > 10 else "Low"
    }
