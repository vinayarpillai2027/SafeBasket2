"""services/sentiment_analyzer.py – Advanced Sentiment Analysis for Reviews."""
from __future__ import annotations
import logging
from dataclasses import dataclass
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger("safebasket.sentiment")

# Initialize VADER analyzer
analyzer = SentimentIntensityAnalyzer()

@dataclass
class SentimentResult:
    """Data container for sentiment analysis results."""
    positive: float = 0.0
    neutral: float = 0.0
    negative: float = 0.0
    average_polarity: float = 0.0
    total_analyzed: int = 0

    def to_dict(self):
        return {
            "positive": self.positive,
            "neutral": self.neutral,
            "negative": self.negative,
            "average_polarity": self.average_polarity,
            "total_analyzed": self.total_analyzed
        }

def analyze_sentiment(reviews: list[dict]) -> SentimentResult:
    """
    Analyzes a list of reviews and returns a statistical breakdown.
    Input: [{'text': '...', 'rating': 5}, ...]
    """
    if not reviews:
        return SentimentResult()

    counts = {"pos": 0, "neu": 0, "neg": 0}
    total_compound = 0.0

    for review in reviews:
        text = review.get("text", "")
        if not text:
            continue
            
        scores = analyzer.polarity_scores(text)
        compound = scores['compound']
        total_compound += compound

        if compound >= 0.05:
            counts["pos"] += 1
        elif compound <= -0.05:
            counts["neg"] += 1
        else:
            counts["neu"] += 1

    total = sum(counts.values())
    
    if total == 0:
        return SentimentResult()

    return SentimentResult(
        positive=round((counts["pos"] / total) * 100, 1),
        neutral=round((counts["neu"] / total) * 100, 1),
        negative=round((counts["neg"] / total) * 100, 1),
        average_polarity=round(total_compound / total, 3),
        total_analyzed=total
    )