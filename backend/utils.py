"""utils.py"""
from __future__ import annotations
import logging, re, sys
from urllib.parse import urlparse
from flask import jsonify

def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
    logging.basicConfig(stream=sys.stdout, level=level, format=fmt)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return logging.getLogger("safebasket")

logger = setup_logging()

SUPPORTED_DOMAINS = (
    "amazon.in","amazon.com","amazon.co.uk","amazon.de","amazon.ca","amazon.com.au",
    "flipkart.com","myntra.com","snapdeal.com","meesho.com","nykaa.com","ajio.com",
)

def validate_product_url(url: str):
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string."
    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Malformed URL."
    if parsed.scheme not in ("http", "https"):
        return False, "URL must begin with http:// or https://"
    host = parsed.netloc.lower().lstrip("www.")
    if not any(host == d or host.endswith("." + d) for d in SUPPORTED_DOMAINS):
        return False, f"Unsupported platform. Supported: {', '.join(SUPPORTED_DOMAINS)}"
    return True, ""

def extract_asin(url: str):
    m = re.search(r"/dp/([A-Z0-9]{10})", url)
    return m.group(1) if m else None

def success_response(data: dict, status: int = 200):
    return jsonify({"status": "success", "data": data}), status

def error_response(message: str, status: int = 400, details: str = None):
    body = {"status": "error", "message": message}
    if details:
        body["details"] = details
    return jsonify(body), status

def infer_category(url: str) -> str:
    url_lower = url.lower()
    if any(k in url_lower for k in ["phone","mobile","laptop","computer","tablet","headphone","earphone","speaker","camera","tv","television","electronics"]):
        return "Electronics"
    if any(k in url_lower for k in ["shirt","dress","shoe","clothing","fashion","kurta","saree","jeans","top","wear"]):
        return "Fashion"
    if any(k in url_lower for k in ["book","novel","textbook","magazine"]):
        return "Books"
    if any(k in url_lower for k in ["kitchen","cookware","appliance","refrigerator","washing","microwave"]):
        return "Home & Kitchen"
    if any(k in url_lower for k in ["beauty","skincare","makeup","cosmetic","hair","shampoo","cream"]):
        return "Beauty"
    if any(k in url_lower for k in ["toy","game","sport","fitness","gym","cycle"]):
        return "Sports & Toys"
    return "General"