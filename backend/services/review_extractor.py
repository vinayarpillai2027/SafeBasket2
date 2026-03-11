"""review_extractor.py – FINAL WORKING VERSION with better search queries"""
from __future__ import annotations
import re
import logging
from typing import Any
import requests
from config import Config

logger = logging.getLogger("safebasket.extractor")


def _extract_asin_from_url(url: str) -> str:
    """Extract ASIN from Amazon URL"""
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})',
        r'/gp/product/([A-Z0-9]{10})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _get_product_name_from_url(url: str) -> str:
    """Extract product name from URL structure"""
    url_lower = url.lower()
    
    # Amazon
    if 'amazon' in url_lower:
        match = re.search(r'amazon\.[^/]+/([^/]+)/dp/', url)
        if match:
            product_slug = match.group(1)
            product_name = product_slug.replace('-', ' ').replace('_', ' ')
            product_name = re.sub(r'\s+(online|buy|best|price).*', '', product_name, flags=re.IGNORECASE)
            return product_name.title()[:100]
    
    # Flipkart
    elif 'flipkart' in url_lower:
        match = re.search(r'flipkart\.com/([^/]+)/p/', url)
        if match:
            product_slug = match.group(1)
            product_name = product_slug.replace('-', ' ').replace('_', ' ')
            product_name = re.sub(r'\s+(online|buy|best|price).*', '', product_name, flags=re.IGNORECASE)
            return product_name.title()[:100]
    
    # Myntra
    elif 'myntra' in url_lower:
        match = re.search(r'myntra\.com/([^/]+)/\d+/', url)
        if match:
            product_slug = match.group(1)
            return product_slug.replace('-', ' ').title()[:100]
    
    return None


def _fetch_reviews_serpapi(search_query: str) -> tuple[list[dict], dict]:
    """Fetch reviews using SerpAPI"""
    if not Config.SERPAPI_KEY:
        return [], {}
    
    try:
        logger.info(f"🔍 SerpAPI: Searching '{search_query}'")
        
        params = {
            "api_key": Config.SERPAPI_KEY,
            "engine": "google",
            "q": search_query,
            "num": 20,
            "gl": "in",
            "hl": "en"
        }
        
        response = requests.get("https://serpapi.com/search", params=params, timeout=25)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            logger.error(f"SerpAPI error: {data['error']}")
            # Try with simpler query
            simple_query = ' '.join(search_query.split()[:3])
            if simple_query != search_query:
                logger.info(f"🔄 Retrying with: {simple_query}")
                params["q"] = simple_query
                response = requests.get("https://serpapi.com/search", params=params, timeout=25)
                data = response.json()
                if "error" in data:
                    return [], {}
        
        # Extract product details
        product_details = {}
        
        # Try knowledge graph
        kg = data.get("knowledge_graph", {})
        if kg:
            product_details = {
                'name': kg.get('title', '')[:100],
                'image_url': kg.get('image'),
                'description': kg.get('description', '')[:200],
                'rating': kg.get('rating'),
            }
            
            if "price" in kg:
                price_str = str(kg.get("price", ""))
                price_match = re.search(r"([\d,]+(?:\.\d{2})?)", price_str)
                if price_match:
                    product_details['price'] = price_match.group(1).replace(",", "")
                    product_details['currency'] = "INR"
        
        # Try shopping results
        shopping = data.get("shopping_results", [])
        if shopping:
            first = shopping[0]
            if not product_details.get('name'):
                product_details['name'] = first.get('title', '')[:100]
            if not product_details.get('image_url'):
                product_details['image_url'] = first.get('thumbnail')
            if not product_details.get('price'):
                product_details['price'] = first.get('extracted_price')
                product_details['currency'] = first.get('currency', 'INR')
        
        # Extract reviews
        reviews = []
        for result in data.get("organic_results", [])[:15]:
            snippet = result.get("snippet", "")
            title = result.get("title", "")
            
            if not snippet or len(snippet) < 15:
                continue
            
            # Skip if it's just a product listing
            if any(word in title.lower() for word in ['buy', 'price', 'shop', 'amazon.in', 'flipkart.com']):
                continue
            
            # Rating detection
            rating = 3.5  # default
            rating_match = re.search(r"(\d(?:\.\d)?)\s*(?:/|out of)\s*5", snippet, re.IGNORECASE)
            if not rating_match:
                rating_match = re.search(r"(\d)\s*stars?", snippet, re.IGNORECASE)
            
            if rating_match:
                rating = min(5.0, max(1.0, float(rating_match.group(1))))
            else:
                # Sentiment-based rating
                snippet_lower = snippet.lower()
                if any(word in snippet_lower for word in ["excellent", "amazing", "perfect", "love it", "best"]):
                    rating = 4.5
                elif any(word in snippet_lower for word in ["good", "nice", "decent", "satisfied", "recommend"]):
                    rating = 4.0
                elif any(word in snippet_lower for word in ["okay", "average", "fine"]):
                    rating = 3.0
                elif any(word in snippet_lower for word in ["bad", "poor", "worst", "terrible", "disappointed", "waste"]):
                    rating = 2.0
            
            reviews.append({
                "text": snippet[:500],
                "title": title[:100],
                "rating": rating
            })
        
        logger.info(f"✅ Found {len(reviews)} review snippets and product details")
        return reviews, product_details
        
    except Exception as e:
        logger.exception(f"❌ SerpAPI error: {e}")
        return [], {}


def _compute_average(reviews: list[dict]) -> float:
    """Calculate average rating"""
    ratings = [r["rating"] for r in reviews if r.get("rating")]
    return round(sum(ratings) / len(ratings), 2) if ratings else 3.0


def fetch_reviews(url: str) -> dict[str, Any]:
    """
    Main review fetching function - FINAL WORKING VERSION
    """
    
    logger.info(f"🎯 Extracting reviews for: {url}")
    
    # Extract product name from URL
    url_based_name = _get_product_name_from_url(url)
    asin = _extract_asin_from_url(url) if 'amazon' in url.lower() else None
    
    # Build search query - multiple strategies
    search_queries = []
    
    # Strategy 1: Use product name from URL
    if url_based_name:
        search_queries.append(f"{url_based_name} review india")
        search_queries.append(f"{url_based_name} customer reviews")
    
    # Strategy 2: Use ASIN
    if asin:
        search_queries.append(f"amazon {asin} review")
    
    # Strategy 3: Extract brand/model from URL
    if not url_based_name:
        path_parts = url.split('/')
        for part in path_parts:
            if len(part) > 10 and '-' in part:
                clean = part.replace('-', ' ')
                words = clean.split()[:4]  # First 4 words
                if len(words) >= 2:
                    search_queries.append(f"{' '.join(words)} review")
                    break
    
    # If no good query, use a generic one
    if not search_queries:
        search_queries.append("product review india")
    
    # Try each search query
    reviews = []
    product_details = {}
    
    for query in search_queries[:2]:  # Try max 2 queries
        logger.info(f"🔍 Trying query: {query}")
        reviews, product_details = _fetch_reviews_serpapi(query)
        if reviews:
            break
    
    # Initialize result
    result = {
        'reviews': [],
        'total_reviews': 0,
        'average_rating': 3.0,
        'platform': 'Google Search',
        'product_name': url_based_name or 'Unknown Product',
        'product_image': None,
        'product_description': None,
        'product_price': None,
        'product_currency': None,
    }
    
    # Update with found details
    if product_details:
        result['product_name'] = product_details.get('name') or result['product_name']
        result['product_image'] = product_details.get('image_url')
        result['product_description'] = product_details.get('description')
        result['product_price'] = product_details.get('price')
        result['product_currency'] = product_details.get('currency')
    
    # Handle no reviews case
    if not reviews:
        logger.warning("⚠️ No reviews found, using fallback data")
        reviews = [{
            "text": "Limited review data available. Product may be new or have few reviews. Check the product page directly for latest reviews.",
            "title": "Data Availability Notice",
            "rating": 3.0
        }]
    
    # Finalize
    result['reviews'] = reviews[:Config.MAX_REVIEWS]
    result['total_reviews'] = len(reviews)
    result['average_rating'] = _compute_average(reviews)
    
    logger.info(f"✅ Complete: {len(result['reviews'])} reviews, {result['average_rating']:.2f}★, '{result['product_name']}'")
    
    return result
