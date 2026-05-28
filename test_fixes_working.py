#!/usr/bin/env python3
"""
Quick test to verify all fixes are working
Run this AFTER restarting Flask
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:5000"

print("=" * 70)
print("TESTING FIXES FOR MASKED PDF & SUPABASE ISSUES")
print("=" * 70)

# Test 1: Health endpoint
print("\n1. Testing /health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    data = response.json()
    
    print(f"   Status: {data.get('status')}")
    print(f"   Supabase: {data.get('supabase')}")
    print(f"   Redacted CVs: {data.get('redacted_cvs')}")
    print(f"   Intelligence files: {data.get('intelligence_files')}")
    
    if data.get('status') == 'healthy':
        print("   ✓ Health check passed")
    else:
        print("   ⚠ Health check not fully healthy")
        
except Exception as e:
    print(f"   ✗ Error: {e}")
    print("   ℹ Make sure Flask is running: python app.py")

# Test 2: Local files
print("\n2. Checking local candidate files...")
local_files = list(Path("llm_analysis").glob("*_intelligence.json"))
print(f"   Found {len(local_files)} local intelligence files")
if local_files:
    print(f"   ✓ Local fallback data available")
else:
    print(f"   ⚠ No local files yet - upload a CV first")

masked_pdfs = list(Path("redacted_output").glob("MASKED_*.pdf"))
print(f"   Found {len(masked_pdfs)} masked PDF files")
if masked_pdfs:
    print(f"   ✓ Masked PDFs are being created")
    # Show most recent
    recent = sorted(masked_pdfs)[-1]
    print(f"   Most recent: {recent.name}")
else:
    print(f"   ⚠ No masked PDFs yet - upload a CV first")

# Test 3: Search endpoint
print("\n3. Testing /api/search-candidates endpoint...")
try:
    response = requests.post(
        f"{BASE_URL}/api/search-candidates",
        json={"limit": 5},
        timeout=10
    )
    data = response.json()
    
    if response.status_code == 200:
        count = data.get('count', 0)
        source = data.get('data_source', 'unknown')
        print(f"   ✓ Search successful")
        print(f"   Found {count} candidates from {source}")
    else:
        error = data.get('error', 'Unknown error')
        print(f"   Status: {response.status_code}")
        print(f"   Error: {error}")
        print(f"   Message: {data.get('message', 'N/A')}")
        
except Exception as e:
    print(f"   ✗ Search error: {e}")

# Test 4: Sample download
print("\n4. Testing masked PDF download...")
masked_pdfs = list(Path("redacted_output").glob("MASKED_*.pdf"))
if masked_pdfs:
    test_pdf = masked_pdfs[-1].name  # Most recent
    try:
        response = requests.get(
            f"{BASE_URL}/download/{test_pdf}",
            timeout=5
        )
        
        if response.status_code == 200:
            size_mb = len(response.content) / (1024 * 1024)
            print(f"   ✓ Download works")
            print(f"   Downloaded: {test_pdf} ({size_mb:.2f} MB)")
        else:
            print(f"   ✗ Download failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ✗ Download error: {e}")
else:
    print(f"   ℹ No masked PDFs to test - upload a CV first")

# Test 5: Intelligence file
print("\n5. Testing intelligence JSON files...")
intel_files = list(Path("llm_analysis").glob("*_intelligence.json"))
if intel_files:
    try:
        with open(intel_files[-1]) as f:
            data = json.load(f)
            anon_id = data.get('anonymized_id', 'N/A')
            skills = data.get('core_technical_skills', [])
            print(f"   ✓ Intelligence file readable")
            print(f"   ID: {anon_id}")
            print(f"   Skills: {', '.join(skills[:3]) if skills else 'None'}")
    except Exception as e:
        print(f"   ✗ Error reading intelligence: {e}")
else:
    print(f"   ℹ No intelligence files - upload a CV first")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
print("""
If all tests passed (✓):
- Flask app is running correctly
- Supabase connection is working
- Masked PDFs are being created
- Search fallback is functional
- Downloads are working

If you got ⚠ or ✗:
1. Make sure Flask is running: python app.py
2. Upload a CV if no candidates found
3. Check /health endpoint manually
4. Run: python diagnose_connection.py

Next: Test the web UI by going to http://127.0.0.1:5000
""")
