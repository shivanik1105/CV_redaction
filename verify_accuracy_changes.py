"""
Verify that all accuracy improvements are properly implemented in the code
Run this BEFORE restarting Flask to confirm changes are in place
"""
import re
from pathlib import Path

def check_file_content(filepath, checks):
    """Check if file contains expected patterns"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        results = []
        for check_name, pattern, expected in checks:
            if isinstance(pattern, str):
                found = pattern in content
            else:  # regex
                found = bool(pattern.search(content))
            
            status = "PASS" if found == expected else "FAIL"
            results.append((check_name, status, found))
        
        return results
    except Exception as e:
        return [("File Read Error", "ERROR", str(e))]

def main():
    print("="*70)
    print("ACCURACY IMPROVEMENTS VERIFICATION")
    print("="*70)
    print("\nChecking if all code changes are properly implemented...\n")
    
    all_passed = True
    
    # Check 1: app.py - Minimum threshold 50%
    print("1. Checking app.py - Minimum Threshold (50%)")
    print("-" * 70)
    
    app_checks = [
        ("Adaptive threshold in quick-search", 
         re.compile(r'min_threshold\s*=\s*45'), 
         True),
        ("70% critical skills requirement", 
         re.compile(r'minimum_critical_coverage\s*=\s*70\.0'), 
         True),
        ("50/50 scoring balance (semantic)", 
         re.compile(r'0\.50\s*\*\s*semantic_score'), 
         True),
        ("50/50 scoring balance (critical)", 
         re.compile(r'0\.50\s*\*\s*critical_coverage'), 
         True),
    ]
    
    results = check_file_content('app.py', app_checks)
    for check_name, status, found in results:
        symbol = "✓" if status == "PASS" else "✗"
        print(f"   {symbol} {check_name}: {status}")
        if status == "FAIL":
            all_passed = False
    
    print()
    
    # Check 2: templates/index_new.html - Sub-scores removed
    print("2. Checking templates/index_new.html - Sub-scores Removed")
    print("-" * 70)
    
    template_checks = [
        ("No semantic_score in template", 
         "semantic_score", 
         False),
        ("No keyword_score in template", 
         "keyword_score", 
         False),
        ("No critical_skill_score in template", 
         "critical_skill_score", 
         False),
    ]
    
    results = check_file_content('templates/index_new.html', template_checks)
    for check_name, status, found in results:
        symbol = "✓" if status == "PASS" else "✗"
        print(f"   {symbol} {check_name}: {status}")
        if status == "FAIL":
            all_passed = False
    
    print()
    
    # Check 3: vector_search.py - Model upgrade
    print("3. Checking vector_search.py - Model Upgrade (768d)")
    print("-" * 70)
    
    vector_checks = [
        ("Model is all-mpnet-base-v2", 
         'LOCAL_MODEL = "all-mpnet-base-v2"', 
         True),
        ("Dimensions are 768", 
         "LOCAL_DIMENSIONS = 768", 
         True),
    ]
    
    results = check_file_content('vector_search.py', vector_checks)
    for check_name, status, found in results:
        symbol = "✓" if status == "PASS" else "✗"
        print(f"   {symbol} {check_name}: {status}")
        if status == "FAIL":
            all_passed = False
    
    print()
    print("="*70)
    
    if all_passed:
        print("✓ ALL CHECKS PASSED!")
        print("="*70)
        print("\nNext Steps:")
        print("1. Restart Flask app: python app.py")
        print("2. Hard refresh browser: Ctrl + Shift + R")
        print("3. Test search with any JD")
        print("4. Verify 8-12 results (not 36)")
        print("5. Verify no sub-scores visible")
        print("\nOptional: Run test_accuracy_live.py after restart")
    else:
        print("✗ SOME CHECKS FAILED!")
        print("="*70)
        print("\nAction Required:")
        print("1. Review failed checks above")
        print("2. Manually verify the code changes")
        print("3. Re-run this script to confirm")
        print("\nExpected values:")
        print("- app.py line ~3055: min_threshold = 45 (adaptive)")
        print("- app.py line ~1678: minimum_critical_coverage = 70.0")
        print("- app.py line ~1687: 0.50 * semantic_score")
        print("- app.py line ~1688: 0.50 * critical_coverage")
        print("- templates/index_new.html: NO semantic_score, keyword_score, critical_skill_score")
        print("- vector_search.py line 30: LOCAL_MODEL = \"all-mpnet-base-v2\"")
        print("- vector_search.py line 31: LOCAL_DIMENSIONS = 768")
    
    print()
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
