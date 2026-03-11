"""price_comparison_ENHANCED.py - Enhanced Price Comparison with Smart Product Name Extraction

IMPROVEMENTS:
1. Extracts product name from review_extractor if not provided
2. Better error handling and logging
3. Supports multiple scraping APIs
4. Graceful fallbacks
"""
from __future__ import annotations
import re
import logging
from typing import Any
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from config import Config

logger = logging.getLogger("safebasket.price")

@dataclass
class SellerListing:
    """Price listing from a seller"""
    seller_name: str
    price: float
    currency: str
    link: str
    platform: str
    shipping: str = "Unknown"
    rating: float = None
    reviews_count: int = None
    in_stock: bool = True
    
    def to_dict(self):
        return {
            "seller_name": self.seller_name,
            "price": self.price,
            "currency": self.currency,
            "link": self.link,
            "platform": self.platform,
            "shipping": self.shipping,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "in_stock": self.in_stock,
        }


def _extract_platform(link: str) -> str:
    """Extract platform from URL"""
    link_lower = link.lower()
    
    platforms = {
        "amazon": "Amazon",
        "flipkart": "Flipkart",
        "myntra": "Myntra",
        "ajio": "Ajio",
        "snapdeal": "Snapdeal",
        "tatacliq": "Tata CLiQ",
        "croma": "Croma",
        "jiomart": "JioMart",
        "meesho": "Meesho",
        "nykaa": "Nykaa",
    }
    
    for key, name in platforms.items():
        if key in link_lower:
            return name
    
    return "Other"


def _clean_product_name(name: str) -> str:
    """Clean product name for search - Enhanced to extract key identifiers"""
    if not name:
        return ""
    
    # Remove review text and common noise
    clean = re.sub(r'\b(review|hands.?on|unboxing|buy|online|price|shop|deal|charging|upgrades)\b', '', name, flags=re.I)
    # Remove special chars but keep brand/model info
    clean = re.sub(r'[:|"\'!?]+', ' ', clean)
    # Clean whitespace
    clean = ' '.join(clean.split())
    
    return clean.strip()[:60]


def _extract_product_identifiers(name: str) -> dict:
    """
    Extract key product identifiers for better matching
    Returns: {brand, model, category, key_features}
    """
    name_lower = name.lower()
    
    identifiers = {
        "brand": None,
        "model": None,
        "category": None,
        "key_features": []
    }
    
    # Common brands
    brands = {
        "samsung": "Samsung",
        "apple": "Apple",
        "xiaomi": "Xiaomi",
        "redmi": "Redmi",
        "oneplus": "OnePlus",
        "realme": "Realme",
        "oppo": "Oppo",
        "vivo": "Vivo",
        "nokia": "Nokia",
        "motorola": "Motorola",
        "asus": "Asus",
        "lenovo": "Lenovo",
        "hp": "HP",
        "dell": "Dell",
        "sony": "Sony",
        "lg": "LG",
        "nike": "Nike",
        "adidas": "Adidas",
        "puma": "Puma",
    }
    
    for key, brand_name in brands.items():
        if key in name_lower:
            identifiers["brand"] = brand_name
            break
    
    # Extract model numbers (alphanumeric patterns)
    model_patterns = [
        r'\b([A-Z]\d{2,}[A-Z]?)\b',  # Like M31, A52, etc.
        r'\b(Galaxy [A-Z]\d{2})\b',  # Galaxy S21, etc.
        r'\b(iPhone \d{1,2}( Pro)?( Max)?)\b',  # iPhone patterns
    ]
    
    for pattern in model_patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            identifiers["model"] = match.group(1)
            break
    
    # Detect categories
    categories = {
        "smartphone|mobile|phone": "Smartphone",
        "laptop|notebook": "Laptop",
        "tablet": "Tablet",
        "headphone|earphone|earbud": "Audio",
        "watch|smartwatch": "Wearable",
        "shoe|sneaker": "Footwear",
        "shirt|tshirt|dress": "Apparel",
    }
    
    for pattern, category in categories.items():
        if re.search(pattern, name_lower):
            identifiers["category"] = category
            break
    
    # Extract key features
    features = {
        r'\b(\d+gb)\b': 'storage',
        r'\b(\d+mp)\b': 'camera',
        r'\b(5g|4g)\b': 'network',
        r'\b(\d+mah)\b': 'battery',
        r'\b(amoled|oled|lcd)\b': 'display',
    }
    
    for pattern, feature_type in features.items():
        matches = re.findall(pattern, name_lower)
        for match in matches:
            identifiers["key_features"].append(match.upper())
    
    return identifiers


def _build_search_queries(product_name: str) -> list[str]:
    """
    Generate multiple search queries for better coverage
    Returns list of search queries from most specific to most general
    """
    queries = []
    
    # Extract identifiers
    ids = _extract_product_identifiers(product_name)
    clean_name = _clean_product_name(product_name)
    
    # Query 1: Full cleaned name
    if clean_name:
        queries.append(clean_name)
    
    # Query 2: Brand + Model (most specific)
    if ids["brand"] and ids["model"]:
        queries.append(f"{ids['brand']} {ids['model']}")
    
    # Query 3: Brand + Category + Key Features
    if ids["brand"] and ids["category"]:
        feature_str = " ".join(ids["key_features"][:2])  # Top 2 features
        queries.append(f"{ids['brand']} {ids['category']} {feature_str}".strip())
    
    # Query 4: Just Brand + Model without extra words
    if ids["brand"] and ids["model"]:
        queries.append(f"{ids['brand']} {ids['model']} price india")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        q_clean = q.strip().lower()
        if q_clean and q_clean not in seen and len(q_clean) >= 3:
            seen.add(q_clean)
            unique_queries.append(q)
    
    return unique_queries[:3]  # Limit to 3 queries to avoid API limits


def _parse_price_from_text(text: str) -> float:
    """Extract price from text"""
    # Try different patterns
    patterns = [
        r'₹\s*([\d,]+(?:\.\d{2})?)',
        r'Rs\.?\s*([\d,]+(?:\.\d{2})?)',
        r'INR\s*([\d,]+(?:\.\d{2})?)',
        r'\$\s*([\d,]+(?:\.\d{2})?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                continue
    
    return None


def _fetch_prices_scrapingdog(product_name: str) -> list[dict]:
    """
    Fetch prices using Scrapingdog - Google Shopping scraping
    Now uses the product_name as-is (already cleaned by caller)
    """
    if not Config.SCRAPINGDOG_KEY:
        logger.warning("⚠️ Scrapingdog API key not configured")
        return []
    
    try:
        # Use product_name as-is (caller already cleaned it)
        if not product_name or len(product_name) < 3:
            logger.warning("❌ Product name too short")
            return []
        
        logger.info(f"🔍 Scrapingdog: Searching for '{product_name}'")
        
        # Build Google Shopping URL
        import urllib.parse
        search_query = urllib.parse.quote_plus(f"{product_name} buy online india")
        target_url = f'https://www.google.com/search?tbm=shop&q={search_query}&hl=en&gl=in'
        
        # Scrapingdog request
        params = {
            'api_key': Config.SCRAPINGDOG_KEY,
            'url': target_url,
            'dynamic': 'false'  # Static is faster
        }
        
        logger.info(f"📡 Calling Scrapingdog API...")
        response = requests.get('https://api.scrapingdog.com/scrape', params=params, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ Scrapingdog returned status {response.status_code}")
            logger.error(f"Response: {response.text[:200]}")
            return []
        
        html = response.text
        logger.info(f"✅ Got HTML response ({len(html)} bytes)")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        sellers = []
        
        # Strategy 1: Look for shopping result containers
        product_divs = soup.find_all('div', class_=re.compile(r'sh-dgr__content|KZmu8e'))
        
        if not product_divs:
            # Try alternative selectors
            product_divs = soup.find_all('div', attrs={'data-docid': True})
        
        logger.info(f"🔍 Found {len(product_divs)} potential product containers")
        
        for div in product_divs[:15]:
            try:
                # Extract price
                price_elem = div.find(['span', 'b'], class_=re.compile(r'price|a8Pemb'))
                if not price_elem:
                    price_elem = div.find(string=re.compile(r'₹|Rs'))
                
                if not price_elem:
                    continue
                
                price = _parse_price_from_text(str(price_elem))
                if not price:
                    continue
                
                # Extract link
                link_elem = div.find('a', href=True)
                if not link_elem:
                    continue
                
                link = link_elem['href']
                
                # Clean Google redirect URL
                if link.startswith('/url?q='):
                    link = link.replace('/url?q=', '').split('&')[0]
                elif link.startswith('/aclk?'):
                    match = re.search(r'adurl=([^&]+)', link)
                    if match:
                        import urllib.parse
                        link = urllib.parse.unquote(match.group(1))
                
                # Skip if not a valid product URL
                if not link.startswith('http'):
                    continue
                
                # Get platform
                platform = _extract_platform(link)
                
                # Extract title/seller name
                title_elem = div.find(['div', 'span'], class_=re.compile(r'title|tAxDx'))
                if not title_elem:
                    title_elem = div.find('h3')
                
                seller_name = title_elem.get_text(strip=True)[:50] if title_elem else platform
                
                seller = SellerListing(
                    seller_name=seller_name,
                    price=price,
                    currency="INR",
                    link=link,
                    platform=platform,
                    shipping="Check website"
                )
                
                sellers.append(seller)
                logger.debug(f"   Found: {platform} - ₹{price}")
                
            except Exception as e:
                logger.debug(f"⚠️ Skipping entry: {e}")
                continue
        
        if not sellers:
            # Fallback: Simple regex extraction
            logger.info("🔄 Trying fallback regex extraction...")
            
            prices = re.findall(r'₹\s*([\d,]+(?:\.\d{2})?)', html)
            links = re.findall(r'href="(/url\?q=https?://[^"]+)"', html)
            
            logger.debug(f"📊 Fallback found {len(prices)} prices, {len(links)} links")
            
            for i in range(min(len(prices), len(links), 10)):
                try:
                    price = float(prices[i].replace(',', ''))
                    link = links[i].replace('/url?q=', '').split('&')[0]
                    
                    if not link.startswith('http'):
                        continue
                    
                    platform = _extract_platform(link)
                    
                    seller = SellerListing(
                        seller_name=platform,
                        price=price,
                        currency="INR",
                        link=link,
                        platform=platform,
                        shipping="Check website"
                    )
                    
                    sellers.append(seller)
                    
                except (ValueError, IndexError):
                    continue
        
        if sellers:
            logger.info(f"   ✅ Scrapingdog found {len(sellers)} prices")
        else:
            logger.debug("   ⚠️ No prices extracted")
        
        return [s.to_dict() for s in sellers]
        
    except requests.exceptions.Timeout:
        logger.error("⏱️ Scrapingdog request timed out")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"🌐 Scrapingdog network error: {e}")
        return []
    except Exception as e:
        logger.exception(f"❌ Unexpected Scrapingdog error: {e}")
        return []


def _fetch_prices_serpapi_fallback(product_name: str) -> list[dict]:
    """
    Fallback to SerpAPI if Scrapingdog fails or has no results
    Now uses product_name as-is (already cleaned by caller)
    """
    if not Config.SERPAPI_KEY:
        logger.warning("⚠️ SerpAPI key not configured")
        return []
    
    try:
        logger.info(f"🔄 SerpAPI fallback: '{product_name}'")
        
        params = {
            "api_key": Config.SERPAPI_KEY,
            "engine": "google_shopping",
            "q": f"{product_name} buy online india",
            "num": 20,
            "gl": "in",
            "hl": "en",
        }
        
        response = requests.get("https://serpapi.com/search", params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            logger.error(f"SerpAPI error: {data['error']}")
            return []
        
        shopping_results = data.get("shopping_results", [])
        
        if not shopping_results:
            logger.debug("   ⚠️ No SerpAPI shopping results")
            return []
        
        sellers = []
        
        for result in shopping_results[:15]:
            try:
                price = result.get("extracted_price")
                link = result.get("link")
                source = result.get("source")
                
                if not price or not link:
                    continue
                
                platform = _extract_platform(link)
                shipping = result.get("shipping", "Check website")
                
                seller = SellerListing(
                    seller_name=source or platform,
                    price=float(price),
                    currency=result.get("currency", "INR"),
                    link=link,
                    platform=platform,
                    shipping=str(shipping) if shipping else "Unknown",
                    rating=result.get("rating"),
                    reviews_count=result.get("reviews"),
                )
                
                sellers.append(seller)
                
            except (ValueError, KeyError, TypeError):
                continue
        
        logger.info(f"   ✅ SerpAPI found {len(sellers)} prices")
        return [s.to_dict() for s in sellers]
        
    except Exception as e:
        logger.exception(f"❌ SerpAPI error: {e}")
        return []


def fetch_price_comparison(product_name: str, product_url: str = None) -> list[dict]:
    """
    Fetch prices from multiple sellers - ULTRA ENHANCED
    
    Uses multiple search strategies to find similar products across platforms
    
    Args:
        product_name: Product name to search for
        product_url: Optional product URL for context
    
    Returns:
        List of price listings or empty list on error
    """
    try:
        # Validate and clean input
        if not product_name or len(product_name.strip()) < 3:
            logger.warning("❌ Product name too short or empty")
            return []
        
        logger.info(f"🛒 Fetching prices for: '{product_name}'")
        
        # Generate multiple search queries
        search_queries = _build_search_queries(product_name)
        logger.info(f"🔍 Generated {len(search_queries)} search queries")
        
        all_sellers = []
        
        # Try each query with Scrapingdog
        for i, query in enumerate(search_queries, 1):
            logger.info(f"📊 Query {i}/{len(search_queries)}: '{query}'")
            
            sellers = _fetch_prices_scrapingdog(query)
            if sellers:
                logger.info(f"   ✅ Found {len(sellers)} results")
                all_sellers.extend(sellers)
            else:
                logger.info(f"   ⚠️ No results")
            
            # Stop if we have enough results
            if len(all_sellers) >= 10:
                logger.info(f"✅ Collected {len(all_sellers)} results, stopping search")
                break
        
        # Fallback to SerpAPI if still no results
        if not all_sellers and search_queries:
            logger.info("🔄 Trying SerpAPI fallback...")
            for query in search_queries[:2]:  # Try first 2 queries
                sellers = _fetch_prices_serpapi_fallback(query)
                if sellers:
                    all_sellers.extend(sellers)
                    break
        
        if not all_sellers:
            logger.warning("⚠️ No price listings found from any source")
            return []
        
        # Deduplicate by URL and platform (keep lowest price per platform)
        platform_map = {}
        seen_urls = set()
        
        for seller in all_sellers:
            # Skip duplicates by URL
            url_key = seller["link"].split('?')[0]  # Remove query params
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)
            
            platform = seller["platform"]
            
            # Keep lowest price per platform
            if platform not in platform_map or seller["price"] < platform_map[platform]["price"]:
                platform_map[platform] = seller
        
        unique_sellers = list(platform_map.values())
        unique_sellers.sort(key=lambda x: x["price"])
        
        logger.info(f"✅ Final: {len(unique_sellers)} unique sellers across {len(platform_map)} platforms")
        if unique_sellers:
            logger.info(f"💰 Best price: ₹{unique_sellers[0]['price']} from {unique_sellers[0]['seller_name']}")
            logger.info(f"💰 Highest price: ₹{unique_sellers[-1]['price']} from {unique_sellers[-1]['seller_name']}")
            if len(unique_sellers) > 1:
                savings = unique_sellers[-1]['price'] - unique_sellers[0]['price']
                logger.info(f"💸 Potential savings: ₹{savings:.2f} ({(savings/unique_sellers[-1]['price']*100):.1f}%)")
        
        return unique_sellers
        
    except Exception as e:
        logger.exception(f"❌ Unexpected error in price comparison: {e}")
        return []


def get_price_statistics(sellers: list[dict]) -> dict:
    """Calculate price statistics"""
    if not sellers:
        return {
            "lowest_price": 0,
            "highest_price": 0,
            "average_price": 0,
            "price_range": 0,
            "total_sellers": 0,
            "platforms_count": 0,
        }
    
    prices = [s["price"] for s in sellers]
    
    return {
        "lowest_price": min(prices),
        "highest_price": max(prices),
        "average_price": round(sum(prices) / len(prices), 2),
        "price_range": max(prices) - min(prices),
        "savings_vs_highest": max(prices) - min(prices),
        "total_sellers": len(sellers),
        "platforms_count": len(set(s["platform"] for s in sellers)),
    }
