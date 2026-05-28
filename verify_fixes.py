#!/usr/bin/env python3
"""
Quick syntax check for the fixes
"""
import ast
import sys

print("=" * 60)
print("VERIFYING FIXES ARE SYNTACTICALLY CORRECT")
print("=" * 60)

# Test 1: Check cv_intelligence_extractor.py syntax
print("\n1. Checking cv_intelligence_extractor.py syntax...")
try:
    with open("cv_intelligence_extractor.py", "r", encoding="utf-8") as f:
        code = f.read()
    ast.parse(code)
    print("   ✓ Syntax is valid")
    
    # Check for specific fixes
    if "encode('utf-8').decode('utf-8')" in code:
        print("   ✓ UTF-8 encoding fix is present")
    if "errors='replace'" in code:
        print("   ✓ Error handling for encoding is present")
        
except SyntaxError as e:
    print(f"   ✗ Syntax error: {e}")
    sys.exit(1)

# Test 2: Check supabase_storage.py syntax
print("\n2. Checking supabase_storage.py syntax...")
try:
    with open("supabase_storage.py", "r", encoding="utf-8") as f:
        code = f.read()
    ast.parse(code)
    print("   ✓ Syntax is valid")
    
    # Check for the new method
    if "def get_upload_job" in code:
        print("   ✓ get_upload_job() method is present")
    if "'upload_jobs'" in code:
        print("   ✓ upload_jobs table reference is present")
        
except SyntaxError as e:
    print(f"   ✗ Syntax error: {e}")
    sys.exit(1)

# Test 3: Check app.py syntax
print("\n3. Checking app.py syntax...")
try:
    with open("app.py", "r", encoding="utf-8") as f:
        code = f.read()
    ast.parse(code)
    print("   ✓ Syntax is valid")
    
    # Check for ensure_ascii=False
    count = code.count("ensure_ascii=False")
    print(f"   ✓ Found {count} instances of ensure_ascii=False")
        
except SyntaxError as e:
    print(f"   ✗ Syntax error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL SYNTAX CHECKS PASSED ✓")
print("=" * 60)
