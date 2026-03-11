"""services/__init__.py – Services package initialization."""
from .review_extractor import fetch_reviews
from .sentiment_analyzer import analyze_sentiment
from .grievance_detector import detect_grievances
from .fake_review_detector import detect_fake_reviews
from .trust_scorer import compute_trust_score