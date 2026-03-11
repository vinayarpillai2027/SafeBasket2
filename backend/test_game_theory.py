"""test_game_theory.py - Test the Game Theory Engine

Run this to verify the game theory components are working correctly.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_theory_engine import analyze_purchase_decision, GameTheoryEngine
from services.trust_scorer import compute_trust_score
from services.sentiment_analyzer import SentimentResult
from services.grievance_detector import GrievanceResult
from services.fake_review_detector import FakeReviewResult

print("=" * 80)
print("🎮 GAME THEORY ENGINE TEST SUITE")
print("=" * 80)

# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: High-Quality Product (Should recommend Purchase)
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 80)
print("TEST 1: High-Quality Product Analysis")
print("─" * 80)

high_quality_product = {
    "trust_score": 85,
    "fake_review_risk": 10,
    "grievance_rate": 5,
    "price": 5000,
    "perceived_value": 6000,
    "total_reviews": 150,
    "average_rating": 4.5,
    "sentiment_positive": 80,
    "sentiment_negative": 10,
    "credibility_score": 85,
    "opportunity_cost": 500
}

print(f"Product Data:")
print(f"  Trust Score: {high_quality_product['trust_score']}/100")
print(f"  Price: ₹{high_quality_product['price']}")
print(f"  Perceived Value: ₹{high_quality_product['perceived_value']}")
print(f"  Total Reviews: {high_quality_product['total_reviews']}")
print(f"  Average Rating: {high_quality_product['average_rating']}/5")

print("\n🎯 Running Game Theory Analysis...")
gt_result = analyze_purchase_decision(high_quality_product)

print(f"\n📊 Results:")
print(f"  Scenario Type: {gt_result.scenario_type}")
print(f"  Nash Equilibria Found: {len(gt_result.nash_equilibria)}")

if gt_result.nash_equilibria:
    nash = gt_result.nash_equilibria[0]
    print(f"\n  Nash Equilibrium #1:")
    print(f"    Strategy Profile: {nash.strategy_profile}")
    print(f"    Buyer Payoff: {nash.payoffs['buyer']:.2f}")
    print(f"    Seller Payoff: {nash.payoffs['seller']:.2f}")
    print(f"    Explanation: {nash.explanation[:100]}...")

print(f"\n  Optimal Strategy:")
print(f"    Buyer should: {gt_result.optimal_strategy.get('buyer', 'Unknown')}")
print(f"    Seller expected: {gt_result.optimal_strategy.get('seller', 'Unknown')}")

print(f"\n  Risk Assessment:")
print(f"    Overall Risk: {gt_result.risk_assessment['overall_risk_score']:.1f}/100")
print(f"    Risk Level: {gt_result.risk_assessment['risk_level']}")
print(f"    Dominant Risk: {gt_result.risk_assessment['dominant_risk_factor']}")

print(f"\n  Confidence: {gt_result.confidence_score:.1f}/100")

print(f"\n  Recommendation:")
print(f"    {gt_result.recommendation[:150]}...")

test1_pass = (
    len(gt_result.nash_equilibria) > 0 and
    gt_result.optimal_strategy.get('buyer') == 'Purchase' and
    gt_result.risk_assessment['risk_level'] == 'Low'
)
print(f"\n{'✅ PASS' if test1_pass else '❌ FAIL'}: High-quality product correctly identified")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Suspicious Product (Should recommend Don't Purchase)
# ══════════════════════════════════════════════════════════════════════════════

print("\n\n" + "─" * 80)
print("TEST 2: Suspicious/Low-Quality Product Analysis")
print("─" * 80)

suspicious_product = {
    "trust_score": 30,
    "fake_review_risk": 85,
    "grievance_rate": 65,
    "price": 3000,
    "perceived_value": 2000,  # Overpriced
    "total_reviews": 50,
    "average_rating": 2.1,
    "sentiment_positive": 20,
    "sentiment_negative": 70,
    "credibility_score": 25,
    "opportunity_cost": 300
}

print(f"Product Data:")
print(f"  Trust Score: {suspicious_product['trust_score']}/100")
print(f"  Fake Review Risk: {suspicious_product['fake_review_risk']}/100")
print(f"  Grievance Rate: {suspicious_product['grievance_rate']}%")
print(f"  Price: ₹{suspicious_product['price']}")
print(f"  Average Rating: {suspicious_product['average_rating']}/5")

print("\n🎯 Running Game Theory Analysis...")
gt_result2 = analyze_purchase_decision(suspicious_product)

print(f"\n📊 Results:")
print(f"  Nash Equilibria Found: {len(gt_result2.nash_equilibria)}")
print(f"  Optimal Buyer Strategy: {gt_result2.optimal_strategy.get('buyer', 'Unknown')}")
print(f"  Overall Risk: {gt_result2.risk_assessment['overall_risk_score']:.1f}/100")
print(f"  Risk Level: {gt_result2.risk_assessment['risk_level']}")
print(f"  Confidence: {gt_result2.confidence_score:.1f}/100")

print(f"\n  Recommendation:")
print(f"    {gt_result2.recommendation[:150]}...")

test2_pass = (
    gt_result2.optimal_strategy.get('buyer') == "Don't Purchase" and
    gt_result2.risk_assessment['risk_level'] in ['High', 'Medium']
)
print(f"\n{'✅ PASS' if test2_pass else '❌ FAIL'}: Suspicious product correctly flagged")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: Integrated Trust Score
# ══════════════════════════════════════════════════════════════════════════════

print("\n\n" + "─" * 80)
print("TEST 3: Integrated Trust Score (Traditional + Game Theory)")
print("─" * 80)

# Create mock traditional analysis results
sentiment = SentimentResult(
    positive=80.0,
    neutral=10.0,
    negative=10.0,
    average_polarity=0.65,
    total_analyzed=150
)

grievance = GrievanceResult(
    total_reviews_analyzed=150,
    total_flagged=8,
    grievance_rate=5.3,
    breakdown={"Quality Issues": 5, "Delivery Problems": 3},
    top_complaint="Quality Issues"
)

fake = FakeReviewResult(
    risk_score=10.0,
    risk_label="Low",
    signals={
        "short_reviews_pct": 5,
        "generic_phrases_pct": 8,
        "excessive_punct_pct": 2,
        "rating_spike_score": 10,
        "similarity_score": 5
    }
)

print("Traditional Analysis Inputs:")
print(f"  Sentiment: {sentiment.positive}% pos, {sentiment.negative}% neg")
print(f"  Grievances: {grievance.grievance_rate}% flagged")
print(f"  Fake Risk: {fake.risk_score}/100 ({fake.risk_label})")

print("\n🎯 Computing Integrated Trust Score...")
trust = compute_trust_score(
    average_rating=4.5,
    sentiment_result=sentiment,
    grievance_result=grievance,
    fake_result=fake,
    game_theory_result=gt_result  # From TEST 1
)

print(f"\n📊 Trust Score Results:")
print(f"  Final Score: {trust.score:.1f}/100")
print(f"  Classification: {trust.classification}")
print(f"\n  Component Breakdown:")
print(f"    Rating Component: {trust.rating_component:.1f}")
print(f"    Sentiment Component: {trust.sentiment_component:.1f}")
print(f"    Fake Risk Component: {trust.fake_risk_component:.1f}")
print(f"    Grievance Component: {trust.grievance_component:.1f}")
print(f"\n  Game Theory Analysis:")
print(f"    Nash Equilibrium: {trust.nash_equilibrium_exists}")
print(f"    Optimal Strategy: {trust.optimal_strategy}")
print(f"    GT Confidence: {trust.game_theory_confidence:.1f}/100")
print(f"    Risk Level: {trust.risk_assessment.get('risk_level', 'Unknown')}")

print(f"\n  Recommendation:")
print(f"    {trust.recommendation[:200]}...")

test3_pass = (
    trust.score >= 70 and
    trust.classification == "Safe" and
    trust.nash_equilibrium_exists
)
print(f"\n{'✅ PASS' if test3_pass else '❌ FAIL'}: Integrated trust score computed correctly")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: Payoff Matrix Verification
# ══════════════════════════════════════════════════════════════════════════════

print("\n\n" + "─" * 80)
print("TEST 4: Payoff Matrix Structure Verification")
print("─" * 80)

print("Testing all strategy combinations...")
all_outcomes = gt_result.all_outcomes

print(f"\nTotal Outcomes: {len(all_outcomes)}")
print(f"Expected: 4 (2 buyer strategies × 2 seller strategies)")

for i, outcome in enumerate(all_outcomes, 1):
    print(f"\n  Outcome {i}:")
    print(f"    Strategies: {outcome.strategy_profile}")
    print(f"    Payoffs: Buyer={outcome.payoffs['buyer']:.2f}, Seller={outcome.payoffs['seller']:.2f}")
    print(f"    Nash Equilibrium: {outcome.is_nash_equilibrium}")

test4_pass = len(all_outcomes) == 4
print(f"\n{'✅ PASS' if test4_pass else '❌ FAIL'}: Payoff matrix complete")

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

print("\n\n" + "=" * 80)
print("📋 TEST SUMMARY")
print("=" * 80)

all_tests = [
    ("High-Quality Product Analysis", test1_pass),
    ("Suspicious Product Detection", test2_pass),
    ("Integrated Trust Score", test3_pass),
    ("Payoff Matrix Structure", test4_pass),
]

passed = sum(1 for _, result in all_tests if result)
total = len(all_tests)

for test_name, result in all_tests:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"  {status}: {test_name}")

print(f"\n{'='*80}")
print(f"Results: {passed}/{total} tests passed")

if passed == total:
    print("\n🎉 SUCCESS! All game theory components working correctly!")
    print("\nThe system can now:")
    print("  ✅ Find Nash Equilibria")
    print("  ✅ Calculate strategic payoffs")
    print("  ✅ Assess purchase risks")
    print("  ✅ Provide optimal recommendations")
    print("  ✅ Integrate traditional + game theory analysis")
    print("\nReady to deploy! 🚀")
else:
    print("\n⚠️  Some tests failed. Please review the output above.")

print("=" * 80)
