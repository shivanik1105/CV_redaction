#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot Supabase connection and masked PDF issues
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

print("=" * 70)
print("CV UPLOAD SYSTEM - DIAGNOSTIC CHECK")
print("=" * 70)

# Load environment
load_dotenv()

# 1. Check Supabase credentials
print("\n1. SUPABASE CONFIGURATION CHECK")
print("-" * 70)
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url:
    print("   ✗ SUPABASE_URL is not set")
else:
    print(f"   ✓ SUPABASE_URL: {supabase_url[:50]}...")

if not supabase_key:
    print("   ✗ SUPABASE_KEY is not set")
else:
    key_preview = supabase_key[:20] + "..." + supabase_key[-20:] if len(supabase_key) > 40 else "***"
    print(f"   ✓ SUPABASE_KEY: {key_preview}")

# 2. Test Supabase connection
print("\n2. SUPABASE CONNECTION TEST")
print("-" * 70)
try:
    from supabase import create_client
    
    if supabase_url and supabase_key:
        client = create_client(supabase_url, supabase_key)
        response = client.table('cv_intelligence').select('anonymized_id').limit(1).execute()
        print(f"   ✓ Connection successful")
        print(f"   ✓ Sample records found: {len(response.data) if response.data else 0}")
        if response.data:
            print(f"   ✓ Sample ID: {response.data[0].get('anonymized_id', 'N/A')}")
    else:
        print("   ✗ Missing credentials - cannot test connection")
        
except Exception as e:
    print(f"   ✗ Connection failed: {e}")
    print(f"   → Check if Supabase project is active and credentials are valid")
    print(f"   → Verify network connectivity to {supabase_url}")

# 3. Check Groq API
print("\n3. GROQ API CHECK")
print("-" * 70)
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    print("   ✗ GROQ_API_KEY is not set")
else:
    key_preview = groq_key[:20] + "..." if len(groq_key) > 20 else "***"
    print(f"   ✓ GROQ_API_KEY: {key_preview}")
    
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        print(f"   ✓ Groq API connection successful")
    except Exception as e:
        print(f"   ✗ Groq API connection failed: {e}")

# 4. Check local files
print("\n4. LOCAL FILES CHECK")
print("-" * 70)
output_folder = Path("redacted_output")
intelligence_folder = Path("llm_analysis")

redacted_files = list(output_folder.glob("REDACTED_*.txt"))
masked_files = list(output_folder.glob("MASKED_*.pdf"))
intelligence_files = list(intelligence_folder.glob("*_intelligence.json"))

print(f"   Redacted text files: {len(redacted_files)}")
print(f"   Masked PDF files: {len(masked_files)}")
print(f"   Intelligence JSON files: {len(intelligence_files)}")

if masked_files:
    print(f"\n   Recent masked PDFs:")
    for pdf_file in sorted(masked_files)[-3:]:
        size_kb = pdf_file.stat().st_size / 1024
        print(f"   - {pdf_file.name} ({size_kb:.1f} KB)")

# 5. Check if masked PDFs are actually being created during upload
print("\n5. MASKED PDF CREATION TEST")
print("-" * 70)
try:
    from app import mask_document_to_pdf
    test_pdf = Path("redacted_output/test_mask.pdf")
    
    # Create a test masked PDF
    test_input = Path("uploads")
    if list(test_input.glob("*.pdf")):
        test_file = list(test_input.glob("*.pdf"))[0]
        print(f"   Testing with: {test_file.name}")
        try:
            mask_document_to_pdf(str(test_file), str(test_pdf), "config")
            if test_pdf.exists():
                print(f"   ✓ Masked PDF created successfully ({test_pdf.stat().st_size / 1024:.1f} KB)")
                test_pdf.unlink()  # Clean up
            else:
                print(f"   ✗ Masked PDF creation failed - file not created")
        except Exception as e:
            print(f"   ✗ Masked PDF creation error: {e}")
    else:
        print(f"   ℹ No test PDFs found in uploads folder")
        
except ImportError as e:
    print(f"   ℹ Cannot test masked PDF creation: {e}")

# 6. Recommendations
print("\n6. RECOMMENDATIONS")
print("-" * 70)
print("""
For Supabase Connection Issues:
1. Verify Supabase project is not paused
   → Go to https://app.supabase.com/projects
2. Check credentials are correct
   → Project URL: https://dashboard.supabase.com/project/xxx/settings/api
3. Test network connectivity
   → Try: ping dpnvwxsslvasyufwqzwr.supabase.co
4. Check firewall/VPN not blocking connection
5. If connection still fails, use local fallback (already enabled)

For Masked PDF Download:
1. Upload a CV through web UI and check logs
2. Look for "MASKED_*.pdf" files in redacted_output folder
3. If masked PDF not created:
   → Check logs for "Visual PDF masking" messages
   → Verify reportlab is installed: pip install reportlab
4. The masked_pdf_download_url should be provided in the upload response

To Fix Issues Now:
1. Restart Flask: Press CTRL+C and run "python app.py"
2. Test upload with local fallback enabled
3. Check /health endpoint for current status
""")

print("\n" + "=" * 70)
