"""test_price_comparison.py - Test the enhanced price comparison system"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_serpapi_key():
    """Test if SerpAPI key is configured"""
    from config import Config
    
    print("=" * 60)
    print("TEST 1: SerpAPI Key Configuration")
    print("=" * 60)
    
    if not Config.SERPAPI_KEY:
        print("❌ FAIL: SERPAPI_KEY not found in environment")
        print("   Please add it to your .env file:")
        print("   SERPAPI_KEY=your_key_here")
        return False
    
    print(f"✅ PASS: SerpAPI key found (ending in ...{Config.SERPAPI_KEY[-8:]})")
    return True

def test_google_shopping_api():
    """Test Google Shopping API call"""
    from price_comparison import fetch_google_shopping_prices
    
    print("\n" + "=" * 60)
    print("TEST 2: Google Shopping API")
    print("=" * 60)
    
    test_product = "iPhone 15"
    print(f"Searching for: {test_product}")
    
    try:
        sellers = fetch_google_shopping_prices(test_product)
        
        if not sellers:
            print("⚠️  WARNING: No sellers found")
            print("   This might be due to:")
            print("   - API rate limits")
            print("   - Product not available")
            print("   - API key issues")
            return False
        
        print(f"✅ PASS: Found {len(sellers)} sellers")
        
        # Show first 3 results
        for i, seller in enumerate(sellers[:3], 1):
            print(f"\n  {i}. {seller.seller_name}")
            print(f"     Platform: {seller.platform}")
            print(f"     Price: {seller.currency} {seller.price}")
            print(f"     Shipping: {seller.shipping}")
            if seller.rating:
                print(f"     Rating: {seller.rating}/5")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False

def test_price_comparison_full():
    """Test complete price comparison flow"""
    from price_comparison import fetch_price_comparison, get_price_statistics
    
    print("\n" + "=" * 60)
    print("TEST 3: Complete Price Comparison")
    print("=" * 60)
    
    test_product = "Samsung Galaxy S24"
    test_url = "https://www.amazon.in/dp/B0XXXXXXXX"  # Dummy URL
    
    print(f"Product: {test_product}")
    print(f"URL: {test_url}")
    
    try:
        sellers = fetch_price_comparison(test_product, test_url)
        
        if not sellers:
            print("⚠️  WARNING: No sellers found")
            return False
        
        print(f"✅ PASS: Found {len(sellers)} unique sellers")
        
        # Calculate statistics
        stats = get_price_statistics(sellers)
        
        print("\nPrice Statistics:")
        print(f"  Lowest:  {sellers[0]['currency']} {stats['lowest_price']}")
        print(f"  Highest: {sellers[0]['currency']} {stats['highest_price']}")
        print(f"  Average: {sellers[0]['currency']} {stats['average_price']}")
        print(f"  Savings: {sellers[0]['currency']} {stats['savings_vs_highest']}")
        print(f"  Platforms: {stats['platforms_count']}")
        
        # Show platforms
        platforms = set(s['platform'] for s in sellers)
        print(f"\nPlatforms found: {', '.join(platforms)}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_platform_detection():
    """Test platform detection from URLs"""
    from price_comparison import _extract_platform_from_link
    
    print("\n" + "=" * 60)
    print("TEST 4: Platform Detection")
    print("=" * 60)
    
    test_urls = [
        ("https://www.amazon.in/dp/B0XXXXX", "Amazon"),
        ("https://www.flipkart.com/product", "Flipkart"),
        ("https://www.myntra.com/item", "Myntra"),
        ("https://www.snapdeal.com/product", "Snapdeal"),
        ("https://example.com/product", "Other"),
    ]
    
    all_passed = True
    for url, expected in test_urls:
        result = _extract_platform_from_link(url)
        if result == expected:
            print(f"✅ {expected}: {result}")
        else:
            print(f"❌ Expected {expected}, got {result}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("\n🧪 SafeBasket Price Comparison Test Suite\n")
    
    results = []
    
    # Run tests
    results.append(("SerpAPI Key", test_serpapi_key()))
    results.append(("Google Shopping API", test_google_shopping_api()))
    results.append(("Platform Detection", test_platform_detection()))
    results.append(("Full Price Comparison", test_price_comparison_full()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Price comparison is working correctly.")
        print("\nNext steps:")
        print("1. Restart your Flask app: python app.py")
        print("2. Test in browser by analyzing a product")
        print("3. Click 'Compare Prices' button")
    else:
        print("\n⚠️  Some tests failed. Please check:")
        print("1. SERPAPI_KEY is valid in .env file")
        print("2. You haven't exceeded API rate limits (100/month free)")
        print("3. Internet connection is working")
        print("\nRun: python test_api.py to verify API key")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
