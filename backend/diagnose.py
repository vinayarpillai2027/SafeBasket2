#!/usr/bin/env python3
"""
SafeBasket Backend Diagnostic Tool
Checks configuration, dependencies, and server connectivity
"""

import sys
import os
import subprocess
import importlib.util

def check_item(name, passed, details=""):
    """Print check result"""
    symbol = "✅" if passed else "❌"
    print(f"{symbol} {name}")
    if details:
        print(f"   → {details}")
    return passed

def main():
    print("=" * 60)
    print("SafeBasket Backend Diagnostic Tool")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # 1. Check Python version
    print("1. Python Version")
    py_version = sys.version_info
    passed = py_version >= (3, 8)
    all_passed &= check_item(
        "Python 3.8+",
        passed,
        f"Found: {py_version.major}.{py_version.minor}.{py_version.micro}"
    )
    print()
    
    # 2. Check required files
    print("2. Required Files")
    required_files = [
        "app.py", "config.py", "database.py", "models.py",
        "utils.py", "requirements.txt"
    ]
    
    for filename in required_files:
        exists = os.path.exists(filename)
        all_passed &= check_item(filename, exists)
    print()
    
    # 3. Check services directory
    print("3. Services Package")
    services_exists = os.path.isdir("services")
    all_passed &= check_item("services/ directory", services_exists)
    
    if services_exists:
        service_files = [
            "__init__.py", "review_extractor.py", "sentiment_analyzer.py",
            "grievance_detector.py", "fake_review_detector.py",
            "trust_scorer.py", "price_comparison.py"
        ]
        
        for filename in service_files:
            path = os.path.join("services", filename)
            exists = os.path.exists(path)
            all_passed &= check_item(f"  services/{filename}", exists)
    print()
    
    # 4. Check Python dependencies
    print("4. Python Dependencies")
    dependencies = [
        "flask", "flask_cors", "flask_limiter", "flask_sqlalchemy",
        "sqlalchemy", "vaderSentiment", "requests", "bcrypt",
        "jwt", "dotenv"
    ]
    
    for dep in dependencies:
        # Special case for PyJWT
        module_name = "jwt" if dep == "jwt" else dep
        spec = importlib.util.find_spec(module_name)
        installed = spec is not None
        all_passed &= check_item(dep, installed)
    print()
    
    # 5. Check environment file
    print("5. Environment Configuration")
    env_exists = os.path.exists(".env")
    check_item(".env file", env_exists, "Not required but recommended" if not env_exists else "")
    
    if env_exists:
        with open(".env", "r") as f:
            env_content = f.read()
            
        has_serpapi = "SERPAPI_KEY" in env_content and "SERPAPI_KEY=" in env_content
        has_secret = "SECRET_KEY" in env_content
        
        check_item("  SERPAPI_KEY", has_serpapi, "REQUIRED for review extraction")
        check_item("  SECRET_KEY", has_secret, "Optional (has default)")
    else:
        print("   ⚠️  Create .env file with SERPAPI_KEY for full functionality")
    print()
    
    # 6. Check database
    print("6. Database")
    db_exists = os.path.exists("safebasket.db")
    check_item("Database file", db_exists, "Will be created on first run" if not db_exists else "")
    print()
    
    # 7. Try importing main modules
    print("7. Module Imports")
    try:
        from config import Config
        check_item("config.Config", True)
    except ImportError as e:
        check_item("config.Config", False, str(e))
        all_passed = False
    
    try:
        from database import db
        check_item("database.db", True)
    except ImportError as e:
        check_item("database.db", False, str(e))
        all_passed = False
    
    try:
        from models import User, Analysis, Purchase
        check_item("models", True)
    except ImportError as e:
        check_item("models", False, str(e))
        all_passed = False
    print()
    
    # 8. Check if server is running
    print("8. Server Status")
    try:
        import requests
        response = requests.get("http://localhost:5000/health", timeout=2)
        server_running = response.status_code == 200
        check_item("Server running", server_running, f"Status: {response.status_code}")
        
        if server_running:
            data = response.json()
            db_health = data.get("data", {}).get("database") == "healthy"
            check_item("  Database connection", db_health)
            
            api_key = data.get("data", {}).get("serpapi_key") == "configured"
            check_item("  SerpAPI key", api_key, "REQUIRED" if not api_key else "")
    except Exception as e:
        check_item("Server running", False, "Not reachable at http://localhost:5000")
        print("   → Start server with: python3 app.py")
    print()
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✅ All checks passed! Backend should work correctly.")
    else:
        print("❌ Some checks failed. Review the issues above.")
        print()
        print("Common fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Create .env file with SERPAPI_KEY")
        print("3. Ensure services/ directory exists with all files")
        print("4. Start server: python3 app.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
