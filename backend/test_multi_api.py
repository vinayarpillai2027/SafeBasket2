#!/usr/bin/env python3
"""
Multi-API Integration Test Script
Tests all APIs and shows which ones are working
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from price_comparison import fetch_price_comparison
from services.review_extractor import fetch_reviews


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_api_keys():
    """Check which API keys are configured"""
    print_header("API Configuration Check")
    
    apis = {
        "SerpAPI": Config.SERPAPI_KEY,
        "Scrapingdog": Config.SCRAPINGDOG_KEY,
        "Oxylabs User": Config.OXYLABS_USER,
        "Oxylabs Pass": Config.OXYLABS_PASS,
        "Bright Data": Config.BRIGHTDATA_TOKEN,
    }
    
    for name, key in apis.items():
        status = "✅ Configured" if key else "❌ Not configured"
        masked = f"{key[:10]}..." if key and len(key) > 10 else "Not set"
        print(f"{name:20} {status:20} {masked}")
    
    print()
    configured = sum(1 for key in apis.values() if key)
    print(f"Total configured: {configured}/{len(apis)}")
    
    if configured == 1:  # Only SerpAPI
        print("\n⚠️  Only SerpAPI configured - Everything works but slower")
        print("💡 Add Scrapingdog for 10x faster price comparison")
    elif configured >= 2:
        print("\n✅ Great! Multiple APIs configured for better performance")


def test_price_comparison():
    """Test price comparison functionality"""
    print_header("Price Comparison Test")
    
    test_product = "Samsung Galaxy S23"
    print(f"Searching for: {test_product}\n")
    
    try:
        prices = fetch_price_comparison(test_product)
        
        if prices:
            print(f"✅ Found {len(prices)} price listings:\n")
            for i, price in enumerate(prices[:5], 1):
                print(f"{i}. {price['platform']:15} ₹{price['price']:>8,.2f}  ({price['seller_name'][:30]})")
            
            if len(prices) > 5:
                print(f"\n... and {len(prices) - 5} more")
            
            # Show price range
            prices_list = [p['price'] for p in prices]
            print(f"\n💰 Best price: ₹{min(prices_list):,.2f}")
            print(f"📊 Price range: ₹{min(prices_list):,.2f} - ₹{max(prices_list):,.2f}")
            print(f"💵 Savings: ₹{max(prices_list) - min(prices_list):,.2f}")
            
        else:
            print("❌ No prices found")
            print("💡 Check your API keys in .env file")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_review_extraction():
    """Test review extraction functionality"""
    print_header("Review Extraction Test")
    
    test_url = "https://www.amazon.in/dp/B0CX59XQCT"
    print(f"Analyzing: {test_url}\n")
    
    try:
        data = fetch_reviews(test_url)
        
        print(f"Product Details:")
        print(f"  Name: {data['product_name']}")
        print(f"  Rating: {data['average_rating']}⭐")
        print(f"  Reviews: {data['total_reviews']}")
        
        if data['product_price']:
            print(f"  Price: {data['product_currency']} {data['product_price']}")
        
        if data['reviews']:
            print(f"\n✅ Sample Reviews:")
            for i, review in enumerate(data['reviews'][:3], 1):
                print(f"\n{i}. {review['rating']}⭐ - {review.get('title', 'No title')}")
                print(f"   {review['text'][:100]}...")
        else:
            print("\n❌ No reviews found")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_full_workflow():
    """Test complete analysis workflow"""
    print_header("Full Analysis Workflow Test")
    
    test_url = "https://www.amazon.in/dp/B0CX59XQCT"
    print(f"Running complete analysis on:\n{test_url}\n")
    
    try:
        # Step 1: Extract reviews
        print("Step 1: Extracting reviews and product details...")
        data = fetch_reviews(test_url)
        product_name = data['product_name']
        print(f"✅ Product: {product_name}")
        print(f"✅ Reviews: {data['total_reviews']}")
        print(f"✅ Rating: {data['average_rating']}⭐")
        
        # Step 2: Get prices
        print(f"\nStep 2: Fetching price comparison...")
        prices = fetch_price_comparison(product_name)
        print(f"✅ Found prices from {len(prices)} sellers")
        
        if prices:
            best_price = min(p['price'] for p in prices)
            print(f"💰 Best price: ₹{best_price:,.2f}")
        
        print("\n" + "=" * 60)
        print("✅ FULL WORKFLOW SUCCESSFUL!")
        print("=" * 60)
        print("\nYour SafeBasket backend is working correctly with multi-API integration!")
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        print("\n💡 Check:")
        print("  1. API keys in .env file")
        print("  2. Internet connection")
        print("  3. API quota/limits")


def main():
    """Run all tests"""
    print("\n" + "🚀" * 30)
    print("SafeBasket Multi-API Integration Test")
    print("🚀" * 30)
    
    # Check API configuration
    check_api_keys()
    
    # Run tests
    test_price_comparison()
    test_review_extraction()
    test_full_workflow()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. If tests passed: Start your backend with 'python app.py'")
    print("2. If tests failed: Check MULTI_API_SETUP.md for troubleshooting")
    print("3. Add missing API keys to .env file for better performance")
    print()


if __name__ == "__main__":
    main()
