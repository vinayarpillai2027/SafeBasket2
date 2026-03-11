"""models.py – All ORM models for SafeBasket v2."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from database import db


class User(db.Model):
    __tablename__ = "users"

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(120), nullable=False)
    email        = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash= db.Column(db.Text, nullable=False)
    role         = db.Column(db.String(16), nullable=False, default="user")  # user | admin
    created_at   = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    analyses     = db.relationship("Analysis", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    purchases    = db.relationship("Purchase", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email,
                "role": self.role, "created_at": self.created_at.isoformat()}


class Analysis(db.Model):
    __tablename__ = "analyses"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    product_url      = db.Column(db.Text, nullable=False)
    product_name     = db.Column(db.Text, nullable=True)

    trust_score      = db.Column(db.Float, nullable=False)
    classification   = db.Column(db.String(32), nullable=False)
    recommendation   = db.Column(db.Text, nullable=False)
    explanation      = db.Column(db.Text, nullable=False, default="")

    total_reviews    = db.Column(db.Integer, default=0)
    average_rating   = db.Column(db.Float, default=0.0)
    fake_review_risk = db.Column(db.Float, default=0.0)
    fake_risk_label  = db.Column(db.String(16), default="Low")

    _sentiment_data  = db.Column("sentiment_data", db.Text, default="{}")
    _grievance_data  = db.Column("grievance_data", db.Text, default="{}")

    analyzed_at      = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    @property
    def sentiment_data(self):
        return json.loads(self._sentiment_data)
    @sentiment_data.setter
    def sentiment_data(self, v):
        self._sentiment_data = json.dumps(v)

    @property
    def grievance_data(self):
        return json.loads(self._grievance_data)
    @grievance_data.setter
    def grievance_data(self, v):
        self._grievance_data = json.dumps(v)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_url": self.product_url,
            "product_name": self.product_name,
            "trust_score": round(self.trust_score, 1),
            "classification": self.classification,
            "recommendation": self.recommendation,
            "explanation": self.explanation,
            "total_reviews": self.total_reviews,
            "average_rating": round(self.average_rating, 2),
            "fake_review_risk": round(self.fake_review_risk, 1),
            "fake_risk_label": self.fake_risk_label,
            "sentiment": self.sentiment_data,
            "grievances": self.grievance_data,
            "analyzed_at": self.analyzed_at.isoformat(),
        }


class Purchase(db.Model):
    __tablename__ = "purchases"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    analysis_id  = db.Column(db.Integer, db.ForeignKey("analyses.id"), nullable=True)
    product_url  = db.Column(db.Text, nullable=False)
    product_name = db.Column(db.Text, nullable=True)
    trust_score  = db.Column(db.Float, nullable=False, default=0.0)
    category     = db.Column(db.String(64), nullable=True, default="General")
    purchased_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "product_url": self.product_url,
            "product_name": self.product_name,
            "trust_score": self.trust_score,
            "category": self.category,
            "purchased_at": self.purchased_at.isoformat(),
        }
