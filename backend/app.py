"""app.py – Game-Theory-Based Decision Support System (SafeBasket v3) - FIXED VERSION

Fixes:
1. Compare endpoint now returns proper data structure
2. Price comparison properly extracts product names from analysis
3. Better error handling
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime, timezone, timedelta
from functools import wraps

import bcrypt
import jwt
from flask import Flask, request, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import func

from config import Config
from database import db, init_db
from models import User, Analysis, Purchase
from services.review_extractor import fetch_reviews
from price_comparison import fetch_price_comparison, get_price_statistics
from services.sentiment_analyzer import analyze_sentiment
from services.grievance_detector import detect_grievances
from services.fake_review_detector import detect_fake_reviews

# NEW: Game Theory imports
from game_theory_engine import analyze_purchase_decision as gt_analyze
from services.trust_scorer import compute_trust_score

from enhanced_features import (
    get_detailed_grievances, 
    analyze_review_timeline,
    analyze_value_perception,
    assess_reviewer_credibility,
    generate_smart_recommendation
)
from utils import validate_product_url, success_response, error_response, infer_category, setup_logging

logger = setup_logging(Config.DEBUG)

# ── JWT helpers (unchanged) ───────────────────────────────────────────────

def generate_token(user_id: int, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return error_response("Missing or invalid Authorization header.", 401)
        token = auth.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return error_response("Token expired. Please login again.", 401)
        except jwt.InvalidTokenError:
            return error_response("Invalid token.", 401)
        g.user_id = payload["user_id"]
        g.role    = payload["role"]
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if g.role != "admin":
            return error_response("Admin access required.", 403)
        return f(*args, **kwargs)
    return decorated

# ── App factory ───────────────────────────────────────────────────────────

def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"]                     = Config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"]        = Config.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"]                = False

    CORS(app, origins="*", supports_credentials=True)

    limiter = Limiter(get_remote_address, app=app,
                      default_limits=[Config.RATE_LIMIT],
                      storage_uri="memory://")

    init_db(app)

    # ══════════════════════════════════════════════════════════════════════
    #  AUTH ROUTES (unchanged)
    # ══════════════════════════════════════════════════════════════════════

    @app.post("/register")
    def register():
        body = request.get_json(silent=True) or {}
        name  = (body.get("name") or "").strip()
        email = (body.get("email") or "").strip().lower()
        pwd   = (body.get("password") or "").strip()

        if not name or not email or not pwd:
            return error_response("Name, email, and password are required.", 422)
        if len(pwd) < 6:
            return error_response("Password must be at least 6 characters.", 422)
        if User.query.filter_by(email=email).first():
            return error_response("An account with this email already exists.", 409)

        pw_hash = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
        user = User(name=name, email=email, password_hash=pw_hash, role="user")
        db.session.add(user)
        db.session.commit()

        token = generate_token(user.id, user.role)
        logger.info("New user registered: %s (id=%d)", email, user.id)
        return success_response({"token": token, "user": user.to_dict()}, 201)

    @app.post("/login")
    def login():
        body  = request.get_json(silent=True) or {}
        email = (body.get("email") or "").strip().lower()
        pwd   = (body.get("password") or "").strip()

        if not email or not pwd:
            return error_response("Email and password are required.", 422)

        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.checkpw(pwd.encode(), user.password_hash.encode()):
            return error_response("Invalid email or password.", 401)

        token = generate_token(user.id, user.role)
        logger.info("User logged in: %s", email)
        return success_response({"token": token, "user": user.to_dict()})

    @app.get("/me")
    @jwt_required
    def me():
        user = User.query.get(g.user_id)
        if not user:
            return error_response("User not found.", 404)
        return success_response({"user": user.to_dict()})

    # ══════════════════════════════════════════════════════════════════════
    #  ENHANCED ANALYSIS ROUTE (with Game Theory)
    # ══════════════════════════════════════════════════════════════════════

    @app.post("/analyze")
    @jwt_required
    @limiter.limit("10 per minute")
    def analyze():
        """
        Enhanced product analysis with game-theoretic decision support
        
        Process:
        1. Extract reviews and product data
        2. Traditional analysis (sentiment, fake reviews, grievances)
        3. Game theory analysis (Nash equilibrium, payoff matrices)
        4. Integrated trust scoring and strategic recommendations
        """
        body = request.get_json(silent=True) or {}
        url  = (body.get("product_url") or body.get("url") or "").strip()

        valid, err = validate_product_url(url)
        if not valid:
            return error_response(err, 422)

        logger.info("🎮 Game-theoretic analysis requested by user=%d for %s", g.user_id, url)

        # ─────────────────────────────────────────────────────────────────
        # STEP 1: Extract Reviews and Product Data
        # ─────────────────────────────────────────────────────────────────
        try:
            review_data = fetch_reviews(url)
        except (ValueError, RuntimeError) as exc:
            return error_response(str(exc), 502)
        except Exception as exc:
            logger.exception("Review extraction failed")
            return error_response("Failed to extract reviews.", 500, str(exc))

        reviews        = review_data["reviews"]
        total_reviews  = review_data["total_reviews"]
        average_rating = review_data["average_rating"]
        product_name   = review_data.get("product_name")
        product_image  = review_data.get("product_image")
        product_description = review_data.get("product_description")
        product_price  = review_data.get("product_price")
        product_currency = review_data.get("product_currency")

        if len(reviews) < Config.MIN_REVIEWS:
            return error_response("Not enough reviews to analyze. Minimum required: 1 review.", 422)

        # ─────────────────────────────────────────────────────────────────
        # STEP 2: Traditional Analysis Components
        # ─────────────────────────────────────────────────────────────────
        sentiment_result = analyze_sentiment(reviews)
        grievance_result = detect_grievances(reviews)
        fake_result      = detect_fake_reviews(reviews)

        # ─────────────────────────────────────────────────────────────────
        # STEP 3: Preliminary Trust Score (for game theory input)
        # ─────────────────────────────────────────────────────────────────
        # Compute trust score WITHOUT game theory first
        preliminary_trust = compute_trust_score(
            average_rating, 
            sentiment_result, 
            grievance_result, 
            fake_result,
            None  # No game theory yet
        )
        
        logger.info(f"📊 Preliminary trust score: {preliminary_trust.score:.1f}/100")

        # ─────────────────────────────────────────────────────────────────
        # STEP 4: Game Theory Analysis (with real trust score!)
        # ─────────────────────────────────────────────────────────────────
        
        # Prepare game theory inputs with REAL trust score
        price_value = float(product_price or 100)  # Default if not available
        
        game_theory_input = {
            "trust_score": preliminary_trust.score,  # CRITICAL FIX: Use real trust!
            "average_rating": average_rating,  # CRITICAL FIX: Add rating!
            "fake_review_risk": fake_result.risk_score,
            "grievance_rate": grievance_result.grievance_rate,
            "sentiment_positive": sentiment_result.positive,  # CRITICAL FIX: Add sentiment!
            "sentiment_negative": sentiment_result.negative,  # CRITICAL FIX: Add sentiment!
            "price": price_value,
            "perceived_value": price_value * (average_rating / 5.0),
            "total_reviews": total_reviews,
        }
        
        # Run game theory analysis
        game_theory_result = gt_analyze(game_theory_input)
        
        logger.info("🎮 Game theory decision: %s (confidence: %.1f%%)", 
                   game_theory_result.decision, game_theory_result.confidence)

        # ─────────────────────────────────────────────────────────────────
        # STEP 5: Final Trust Score (refined with game theory)
        # ─────────────────────────────────────────────────────────────────
        # Re-compute trust score WITH game theory for final refinement
        trust_result = compute_trust_score(
            average_rating, 
            sentiment_result, 
            grievance_result, 
            fake_result,
            game_theory_result
        )

        # ─────────────────────────────────────────────────────────────────
        # STEP 6: Enhanced Features (Optional add-ons)
        # ─────────────────────────────────────────────────────────────────
        detailed_grievances = get_detailed_grievances(reviews)
        timeline_analysis = analyze_review_timeline(reviews)
        value_perception = analyze_value_perception(reviews)
        credibility_assessment = assess_reviewer_credibility(reviews)
        smart_recommendation = generate_smart_recommendation(
            trust_result.score,
            detailed_grievances,
            sentiment_result.to_dict(),
            fake_result.risk_score
        )

        # ─────────────────────────────────────────────────────────────────
        # STEP 7: Store in Database
        # ─────────────────────────────────────────────────────────────────
        analysis = Analysis(
            user_id=g.user_id,
            product_url=url,
            product_name=product_name,
            trust_score=trust_result.score,
            classification=trust_result.classification,
            recommendation=trust_result.recommendation,
            explanation=trust_result.explanation,
            total_reviews=total_reviews,
            average_rating=average_rating,
            fake_review_risk=fake_result.risk_score,
            fake_risk_label=fake_result.risk_label,
        )
        analysis.sentiment_data = sentiment_result.to_dict()
        analysis.grievance_data = grievance_result.to_dict()
        db.session.add(analysis)
        db.session.commit()

        logger.info("✅ Analysis complete: trust=%.1f (%s), game_theory=%s",
                   trust_result.score, trust_result.classification, game_theory_result.decision)

        # ─────────────────────────────────────────────────────────────────
        # STEP 7: Return Enhanced Response
        # ─────────────────────────────────────────────────────────────────
        return success_response({
            "analysis_id": analysis.id,
            "product_name": product_name,
            "product_image": product_image,
            "product_description": product_description,
            "product_price": product_price,
            "product_currency": product_currency,
            
            # Core metrics
            "trust_score": trust_result.to_dict(),
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            
            # Traditional analysis
            "sentiment": sentiment_result.to_dict(),
            "grievances": grievance_result.to_dict(),
            "fake_reviews": fake_result.to_dict(),
            
            # Game Theory Analysis (NEW!)
            "game_theory_analysis": game_theory_result.to_dict(),
            
            # Enhanced features
            "detailed_grievances": detailed_grievances,
            "timeline_analysis": timeline_analysis,
            "value_perception": value_perception,
            "credibility_assessment": credibility_assessment,
            "smart_recommendation": smart_recommendation,
            
            "analyzed_at": analysis.analyzed_at.isoformat(),
        }, 200)

    # ══════════════════════════════════════════════════════════════════════
    #  PRODUCT COMPARISON (FIXED!)
    # ══════════════════════════════════════════════════════════════════════

    @app.post("/compare")
    @jwt_required
    @limiter.limit("5 per minute")
    def compare():
        """
        FIXED: Compare two products with proper data structure
        """
        body = request.get_json(silent=True) or {}
        url1 = (body.get("url1") or "").strip()
        url2 = (body.get("url2") or "").strip()

        if not url1 or not url2:
            return error_response("Both url1 and url2 are required.", 422)

        valid1, err1 = validate_product_url(url1)
        valid2, err2 = validate_product_url(url2)
        
        if not valid1:
            return error_response(f"Product 1 URL invalid: {err1}", 422)
        if not valid2:
            return error_response(f"Product 2 URL invalid: {err2}", 422)

        logger.info("🎮 Comparative analysis for 2 products")

        # Analyze both products
        products = []
        
        for url in [url1, url2]:
            try:
                # Extract reviews
                review_data = fetch_reviews(url)
                reviews = review_data["reviews"]
                
                if len(reviews) < Config.MIN_REVIEWS:
                    return error_response(f"Not enough reviews for {url}", 422)
                
                # Traditional analysis
                sentiment = analyze_sentiment(reviews)
                grievance = detect_grievances(reviews)
                fake = detect_fake_reviews(reviews)
                
                # Game theory input
                price_val = float(review_data.get("product_price") or 100)
                gt_input = {
                    "trust_score": 0,
                    "fake_review_risk": fake.risk_score,
                    "grievance_rate": grievance.grievance_rate,
                    "price": price_val,
                    "perceived_value": price_val * (review_data["average_rating"] / 5.0),
                    "total_reviews": review_data["total_reviews"],
                }
                
                gt_result = gt_analyze(gt_input)
                
                # Trust score
                trust = compute_trust_score(
                    review_data["average_rating"], 
                    sentiment, 
                    grievance, 
                    fake, 
                    gt_result
                )
                
                # Build product data (FIXED structure to match frontend)
                products.append({
                    "url": url,
                    "product_name": review_data.get("product_name", "Unknown Product"),
                    "product_image": review_data.get("product_image"),
                    "trust_score": trust.score,
                    "classification": trust.classification,
                    "recommendation": trust.recommendation,
                    "average_rating": review_data["average_rating"],
                    "total_reviews": review_data["total_reviews"],
                    "fake_review_risk": fake.risk_score,
                    "fake_risk_label": fake.risk_label,
                    "sentiment": sentiment.to_dict(),
                    "game_theory": gt_result.to_dict(),
                })
                
            except Exception as e:
                logger.error(f"Comparison failed for {url}: {e}")
                return error_response(f"Failed to analyze {url}: {str(e)}", 500)

        if len(products) < 2:
            return error_response("Could not analyze both products", 422)

        # Determine winner
        p1_utility = products[0]["trust_score"] - products[0]["game_theory"]["risk_assessment"]["overall_risk_score"]
        p2_utility = products[1]["trust_score"] - products[1]["game_theory"]["risk_assessment"]["overall_risk_score"]
        
        if p1_utility > p2_utility:
            winner_url = products[0]["url"]
            difference = p1_utility - p2_utility
            verdict = f"🏆 {products[0]['product_name']} is the better choice by {difference:.1f} utility points"
        elif p2_utility > p1_utility:
            winner_url = products[1]["url"]
            difference = p2_utility - p1_utility
            verdict = f"🏆 {products[1]['product_name']} is the better choice by {difference:.1f} utility points"
        else:
            winner_url = products[0]["url"]
            verdict = "⚖️ Both products are equally matched - choose based on personal preference"

        return success_response({
            "product_1": products[0],
            "product_2": products[1],
            "products": products,  # For backward compatibility
            "winner_url": winner_url,
            "verdict": verdict,
            "comparison_type": "game_theory_strategic"
        })

    # ══════════════════════════════════════════════════════════════════════
    #  PRICE COMPARISON (ENHANCED!)
    # ══════════════════════════════════════════════════════════════════════

    @app.post("/price-comparison")
    @jwt_required
    @limiter.limit("10 per minute")
    def price_comparison():
        """
        ENHANCED: Price comparison now properly extracts product name
        """
        body = request.get_json(silent=True) or {}
        product_name = (body.get("product_name") or "").strip()
        product_url = (body.get("product_url") or "").strip()
        analysis_id = body.get("analysis_id")
        
        # If no product name provided, try to get it from analysis or URL
        if not product_name:
            if analysis_id:
                analysis = Analysis.query.get(analysis_id)
                if analysis:
                    product_name = analysis.product_name
                    logger.info(f"📦 Using product name from analysis: {product_name}")
            
            # If still no product name, extract from URL
            if not product_name and product_url:
                logger.info(f"🔍 Extracting product name from URL: {product_url}")
                review_data = fetch_reviews(product_url)
                product_name = review_data.get("product_name", "")
                logger.info(f"📦 Extracted product name: {product_name}")
        
        if not product_name:
            return error_response("Could not determine product name. Please provide product_name or ensure analysis has product data.", 422)
        
        try:
            logger.info(f"💰 Fetching price comparison for: {product_name}")
            sellers = fetch_price_comparison(product_name, product_url)
            
            if not sellers:
                return error_response("No price data found for this product", 404)
            
            stats = get_price_statistics(sellers)
            
            return success_response({
                "product_name": product_name,
                "sellers": sellers,
                "total_sellers": len(sellers),
                "statistics": stats,
                "message": f"Found prices from {stats.get('platforms_count', 0)} platforms"
            })
        except Exception as e:
            logger.exception("Price comparison error")
            return error_response(f"Price comparison failed: {str(e)}", 500)
    
    # NEW: GET endpoint for price comparison with analysis_id in URL
    @app.get("/price-comparison/<int:analysis_id>")
    @jwt_required
    @limiter.limit("10 per minute")
    def price_comparison_by_id(analysis_id):
        """
        GET /price-comparison/52 - Fetch prices using analysis ID
        Frontend calls this endpoint
        """
        logger.info(f"💰 Price comparison requested for analysis_id={analysis_id}")
        
        # Get the analysis
        analysis = Analysis.query.get(analysis_id)
        if not analysis:
            logger.error(f"❌ Analysis {analysis_id} not found")
            return error_response(f"Analysis {analysis_id} not found", 404)
        
        # Check ownership
        if analysis.user_id != g.user_id:
            return error_response("Access denied", 403)
        
        product_name = analysis.product_name
        product_url = analysis.product_url
        
        logger.info(f"📦 Product: {product_name}")
        
        if not product_name:
            logger.warning("⚠️ No product name in analysis, extracting from URL...")
            review_data = fetch_reviews(product_url)
            product_name = review_data.get("product_name", "")
        
        if not product_name:
            return error_response("Could not determine product name from analysis", 422)
        
        try:
            logger.info(f"🔍 Fetching prices for: {product_name}")
            sellers = fetch_price_comparison(product_name, product_url)
            
            if not sellers:
                logger.warning("⚠️ No sellers found")
                return error_response("No price data found for this product", 404)
            
            stats = get_price_statistics(sellers)
            
            logger.info(f"✅ Found {len(sellers)} sellers across {stats.get('platforms_count', 0)} platforms")
            
            return success_response({
                "product_name": product_name,
                "sellers": sellers,
                "total_sellers": len(sellers),
                "statistics": stats,
                "message": f"Found prices from {stats.get('platforms_count', 0)} platforms"
            })
        except Exception as e:
            logger.exception("❌ Price comparison error")
            return error_response(f"Price comparison failed: {str(e)}", 500)

    # ══════════════════════════════════════════════════════════════════════
    #  DASHBOARD & HISTORY (unchanged)
    # ══════════════════════════════════════════════════════════════════════

    @app.get("/dashboard")
    @jwt_required
    def dashboard():
        user = User.query.get(g.user_id)
        if not user:
            return error_response("User not found.", 404)

        analyses = Analysis.query.filter_by(user_id=g.user_id).all()
        total = len(analyses)

        if total == 0:
            return success_response({
                "user": user.to_dict(),
                "total_analyses": 0,
                "avg_trust_score": 0,
                "safe_count": 0,
                "high_risk_count": 0,
                "moderate_count": 0,
                "avg_fake_risk": 0,
                "recent_analyses": [],
                "risk_trend": [],
                "purchase_count": 0,
            })

        scores = [a.trust_score for a in analyses]
        fake_risks = [a.fake_review_risk for a in analyses]
        safe_count = sum(1 for s in scores if s >= 70)
        high_risk = sum(1 for s in scores if s < 40)
        moderate = total - safe_count - high_risk

        recent = sorted(analyses, key=lambda a: a.analyzed_at)[-10:]
        risk_trend = [{"date": a.analyzed_at.strftime("%d %b"), "score": round(a.trust_score, 1)} for a in recent]

        purchases = Purchase.query.filter_by(user_id=g.user_id).count()

        return success_response({
            "user": user.to_dict(),
            "total_analyses": total,
            "avg_trust_score": round(sum(scores) / total, 1),
            "safe_count": safe_count,
            "high_risk_count": high_risk,
            "moderate_count": moderate,
            "avg_fake_risk": round(sum(fake_risks) / total, 1),
            "recent_analyses": [a.to_dict() for a in sorted(analyses, key=lambda x: x.analyzed_at, reverse=True)[:5]],
            "risk_trend": risk_trend,
            "purchase_count": purchases,
        })

    @app.get("/history")
    @jwt_required
    def get_history():
        analyses = (Analysis.query
                    .filter_by(user_id=g.user_id)
                    .order_by(Analysis.analyzed_at.desc())
                    .limit(100).all())
        return success_response({"records": [a.to_dict() for a in analyses]})

    @app.delete("/history/<int:record_id>")
    @jwt_required
    def delete_history(record_id):
        record = Analysis.query.filter_by(id=record_id, user_id=g.user_id).first()
        if not record:
            return error_response("Record not found.", 404)
        db.session.delete(record)
        db.session.commit()
        return success_response({"deleted_id": record_id})

    @app.post("/mark-purchased")
    @jwt_required
    def mark_purchased():
        body = request.get_json(silent=True) or {}
        product_url = (body.get("product_url") or "").strip()
        analysis_id = body.get("analysis_id")

        if not product_url:
            return error_response("product_url is required.", 422)

        analysis = Analysis.query.filter_by(id=analysis_id, user_id=g.user_id).first() if analysis_id else None
        trust_score = analysis.trust_score if analysis else 0.0
        product_name = analysis.product_name if analysis else None
        category = infer_category(product_url)

        purchase = Purchase(
            user_id=g.user_id,
            analysis_id=analysis_id,
            product_url=product_url,
            product_name=product_name,
            trust_score=trust_score,
            category=category,
        )
        db.session.add(purchase)
        db.session.commit()

        purchases = Purchase.query.filter_by(user_id=g.user_id).all()
        categories = [p.category for p in purchases]
        top_cat = max(set(categories), key=categories.count) if categories else "General"
        avg_risk = sum(p.trust_score for p in purchases) / len(purchases)
        risk_label = "safe" if avg_risk >= 70 else "moderate-risk" if avg_risk >= 40 else "high-risk"
        insight = f"You tend to buy {risk_label} {top_cat.lower()} products."

        return success_response({"purchase": purchase.to_dict(), "insight": insight}, 201)

    @app.get("/purchases")
    @jwt_required
    def get_purchases():
        purchases = (Purchase.query.filter_by(user_id=g.user_id)
                     .order_by(Purchase.purchased_at.desc()).all())
        categories = [p.category for p in purchases]
        top_cat = max(set(categories), key=categories.count) if categories else "General"
        avg_score = sum(p.trust_score for p in purchases) / max(len(purchases), 1)
        risk_label = "safe" if avg_score >= 70 else "moderate-risk" if avg_score >= 40 else "high-risk"
        insight = f"You tend to buy {risk_label} {top_cat.lower()} products." if purchases else "No purchases tracked yet."
        return success_response({
            "purchases": [p.to_dict() for p in purchases],
            "insight": insight,
            "avg_trust_score": round(avg_score, 1),
        })

    # ══════════════════════════════════════════════════════════════════════
    #  ADMIN ROUTES (unchanged)
    # ══════════════════════════════════════════════════════════════════════

    @app.get("/admin/stats")
    @admin_required
    def admin_stats():
        total_users = User.query.count()
        total_analyses = Analysis.query.count()
        avg_score = db.session.query(func.avg(Analysis.trust_score)).scalar() or 0
        safe_count = Analysis.query.filter(Analysis.trust_score >= 70).count()
        high_risk = Analysis.query.filter(Analysis.trust_score < 40).count()
        avg_fake = db.session.query(func.avg(Analysis.fake_review_risk)).scalar() or 0
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()

        return success_response({
            "total_users": total_users,
            "total_analyses": total_analyses,
            "avg_trust_score": round(float(avg_score), 1),
            "safe_analyses": safe_count,
            "high_risk_analyses": high_risk,
            "avg_fake_risk": round(float(avg_fake), 1),
            "recent_users": [u.to_dict() for u in recent_users],
        })

    @app.get("/admin/users")
    @admin_required
    def admin_users():
        users = User.query.order_by(User.created_at.desc()).all()
        return success_response({"users": [u.to_dict() for u in users]})

    # ══════════════════════════════════════════════════════════════════════
    #  UTILITY ROUTES
    # ══════════════════════════════════════════════════════════════════════

    @app.get("/health")
    def health():
        try:
            db.session.execute(db.text("SELECT 1"))
            db_status = "healthy"
        except Exception:
            db_status = "degraded"
        
        # Check if API keys configured
        serpapi_configured = bool(Config.SERPAPI_KEY and Config.SERPAPI_KEY != "")
        
        return success_response({
            "status": "ok",
            "database": db_status,
            "serpapi_key": "configured" if serpapi_configured else "missing",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "3.0.1-fixed"
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(_): return error_response("Endpoint not found.", 404)
    @app.errorhandler(405)
    def method_not_allowed(_): return error_response("Method not allowed.", 405)
    @app.errorhandler(429)
    def rate_limited(_): return error_response("Too many requests. Slow down.", 429)
    @app.errorhandler(500)
    def internal(_): return error_response("Internal server error.", 500)

    return app

app = create_app()

if __name__ == "__main__":
    logger.info("🎮 Starting SafeBasket v3 (Fixed Edition) on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
