"""config.py – Centralised configuration."""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY        = os.getenv("SECRET_KEY", "dev-secret")
    FLASK_ENV         = os.getenv("FLASK_ENV", "development")
    DEBUG             = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    DATABASE_URL      = os.getenv("DATABASE_URL", "sqlite:///safebasket.db")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL  = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO   = False

    SERPAPI_KEY       = os.getenv("SERPAPI_KEY", "")
    
    # Multi-API Configuration for Enhanced Scraping
    SCRAPINGDOG_KEY   = os.getenv("SCRAPINGDOG_KEY", "")
    OXYLABS_USER      = os.getenv("OXYLABS_USER", "")
    OXYLABS_PASS      = os.getenv("OXYLABS_PASS", "")
    BRIGHTDATA_TOKEN  = os.getenv("BRIGHTDATA_TOKEN", "")

    JWT_SECRET_KEY    = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 86400))

    CORS_ORIGINS      = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
    RATE_LIMIT        = os.getenv("RATE_LIMIT", "30 per minute")

    MAX_REVIEWS       = 100
    MIN_REVIEWS       = 1

    W_RATING    = 0.35
    W_POSITIVE  = 0.35
    W_NEGATIVE  = 0.25
    W_FAKE      = 0.15
    W_GRIEVANCE = 0.10  # Fixed: was 5.0, causing scores to go negative