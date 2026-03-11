#!/usr/bin/env python3
"""
Verify if the fixes were actually applied to your files
"""

import os
import sys

print("=" * 70)
print("SAFEBASKET FIX VERIFICATION")
print("=" * 70)
print()

# Check if we're in the right directory
if not os.path.exists("app.py"):
    print("❌ ERROR: Not in backend directory!")
    print("   Run: cd C:\\Users\\vinay\\sb3\\backend")
    sys.exit(1)

print("✅ In backend directory")
print()

# Check game_theory_engine.py for SCENARIO 3.5
print("1. Checking game_theory_engine.py for SCENARIO 3.5 fix...")
try:
    with open("game_theory_engine.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    if "SCENARIO 3.5" in content or "trust_score >= 65 and rating >= 3.3" in content:
        print("   ✅ SCENARIO 3.5 FOUND - Game theory fix is applied")
        
        # Check if it's in the right place
        if "elif trust_score >= 65 and rating >= 3.3:" in content:
            print("   ✅ Correct logic: trust >= 65 and rating >= 3.3")
        else:
            print("   ⚠️  WARNING: SCENARIO 3.5 exists but might not have correct logic")
    else:
        print("   ❌ SCENARIO 3.5 NOT FOUND - Game theory fix is NOT applied!")
        print("   → You need to replace game_theory_engine.py with game_theory_engine_FIXED.py")
except FileNotFoundError:
    print("   ❌ game_theory_engine.py not found!")

print()

# Check app.py for new price comparison endpoint
print("2. Checking app.py for GET /price-comparison/<id> endpoint...")
try:
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    if '@app.get("/price-comparison/<int:analysis_id>")' in content:
        print("   ✅ GET endpoint FOUND - Price comparison fix is applied")
        
        if "def price_comparison_by_id(analysis_id):" in content:
            print("   ✅ Function name correct: price_comparison_by_id")
        else:
            print("   ⚠️  WARNING: Endpoint exists but function name might be wrong")
    else:
        print("   ❌ GET endpoint NOT FOUND - Price comparison fix is NOT applied!")
        print("   → You need to replace app.py with app_FINAL_FIXED.py")
        
        # Check if old POST endpoint exists
        if '@app.post("/price-comparison")' in content:
            print("   ℹ️  Old POST endpoint found (this is normal, both should exist)")
except FileNotFoundError:
    print("   ❌ app.py not found!")

print()

# Check generate_smart_recommendation call
print("3. Checking app.py for generate_smart_recommendation fix...")
try:
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for the correct call
    if "generate_smart_recommendation(" in content:
        # Count parameters
        import re
        pattern = r'generate_smart_recommendation\((.*?)\)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            params = matches[0]
            # Should have: trust_result.score, detailed_grievances, sentiment_result.to_dict(), fake_result.risk_score
            
            if "detailed_grievances" in params and "sentiment_result.to_dict()" in params:
                print("   ✅ Correct parameters: using detailed_grievances and sentiment_result")
            elif "game_theory_result" in params:
                print("   ❌ WRONG parameters: still has game_theory_result (causes crash!)")
                print("   → You need to replace app.py with app_FINAL_FIXED.py")
            else:
                print("   ⚠️  WARNING: Parameters might be incorrect")
    else:
        print("   ⚠️  generate_smart_recommendation not found")
except FileNotFoundError:
    print("   ❌ app.py not found!")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)

# Read both files and check
fixes_applied = 0
fixes_needed = 0

try:
    with open("game_theory_engine.py", "r") as f:
        if "trust_score >= 65 and rating >= 3.3" in f.read():
            fixes_applied += 1
        else:
            fixes_needed += 1
            print("❌ MISSING: game_theory_engine.py fix")
except:
    pass

try:
    with open("app.py", "r") as f:
        content = f.read()
        if '@app.get("/price-comparison/<int:analysis_id>")' in content:
            fixes_applied += 1
        else:
            fixes_needed += 1
            print("❌ MISSING: app.py price comparison endpoint")
        
        if "detailed_grievances" in content and "generate_smart_recommendation(" in content:
            fixes_applied += 1
        else:
            fixes_needed += 1
            print("❌ MISSING: app.py generate_smart_recommendation fix")
except:
    pass

print()
if fixes_needed == 0:
    print("✅ ALL FIXES APPLIED!")
    print()
    print("Next steps:")
    print("1. Restart Flask (Ctrl+C then python app.py)")
    print("2. Test again")
else:
    print(f"❌ {fixes_needed} FIX(ES) MISSING!")
    print()
    print("Action required:")
    print("1. Stop Flask (Ctrl+C)")
    print("2. Replace files:")
    print("   copy app_FINAL_FIXED.py app.py")
    print("   copy game_theory_engine_FIXED.py game_theory_engine.py")
    print("3. Restart Flask: python app.py")

print("=" * 70)
