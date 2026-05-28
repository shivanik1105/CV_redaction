#!/usr/bin/env python3
"""
Sync CVs: Show what's in database vs what's on disk
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("CV Sync Analysis")
print("=" * 80)

# Check Supabase
print("\n1. Checking Supabase database...")
try:
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("   ERROR: Supabase credentials not set")
        exit(1)
    
    client = create_client(url, key)
    
    # Get candidates from main table
    result = client.table('cv_intelligence').select('anonymized_id').execute()
    db_candidates = result.data
    print(f"   Found {len(db_candidates)} candidates in cv_intelligence table")
    
    # Get filename mappings
    try:
        mappings_result = client.table('cv_filename_mapping').select('anonymized_id, original_filename').execute()
        filename_mappings = {m['anonymized_id']: m['original_filename'] for m in mappings_result.data}
        print(f"   Found {len(filename_mappings)} filename mappings")
    except Exception as e:
        print(f"   WARNING: Could not get filename mappings: {e}")
        filename_mappings = {}
    
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# Check local files
print("\n2. Checking local files...")
uploads_dir = Path("uploads")
redacted_dir = Path("redacted_output")
intelligence_dir = Path("llm_analysis")

if not uploads_dir.exists():
    print(f"   WARNING: {uploads_dir} directory not found")
    uploads_count = 0
else:
    uploads_count = len(list(uploads_dir.glob("*.pdf"))) + len(list(uploads_dir.glob("*.docx")))
    print(f"   Found {uploads_count} files in uploads/")

if not redacted_dir.exists():
    print(f"   WARNING: {redacted_dir} directory not found")
    redacted_count = 0
else:
    redacted_count = len(list(redacted_dir.glob("REDACTED_*.txt")))
    print(f"   Found {redacted_count} redacted files in redacted_output/")

if not intelligence_dir.exists():
    print(f"   WARNING: {intelligence_dir} directory not found")
    intelligence_count = 0
else:
    intelligence_count = len(list(intelligence_dir.glob("*_intelligence.json")))
    print(f"   Found {intelligence_count} intelligence files in llm_analysis/")

# Analysis
print("\n3. Analysis:")
print("   " + "-" * 76)

# CVs in database but not on disk
print(f"\n   CVs in database: {len(db_candidates)}")
print(f"   CVs on disk (uploads): {uploads_count}")
print(f"   CVs processed (redacted): {redacted_count}")
print(f"   CVs with intelligence: {intelligence_count}")

missing_files = []
for candidate in db_candidates:
    anon_id = candidate.get('anonymized_id')
    original_filename = filename_mappings.get(anon_id, 'unknown')
    
    # Check if file exists
    if uploads_dir.exists():
        # Try to find the file
        found = False
        for ext in ['.pdf', '.docx']:
            # Try exact match first
            if list(uploads_dir.glob(f"{original_filename}")):
                found = True
                break
            # Try pattern match
            if list(uploads_dir.glob(f"*{original_filename}*")):
                found = True
                break
        
        if not found:
            missing_files.append({
                'anonymized_id': anon_id,
                'original_filename': original_filename
            })

if missing_files:
    print(f"\n   ⚠️  {len(missing_files)} CVs in database but files missing on disk:")
    for item in missing_files[:10]:  # Show first 10
        print(f"      - {item['anonymized_id']}: {item['original_filename']}")
    if len(missing_files) > 10:
        print(f"      ... and {len(missing_files) - 10} more")
else:
    print(f"\n   ✓ All database CVs have files on disk")

print("\n4. Solutions:")
print("   " + "-" * 76)

if missing_files:
    print("\n   Option 1: Re-upload missing CVs")
    print("   - Upload the original CV files again through the web interface")
    print("   - They will get new anonymized IDs")
    print("   - Old database entries will remain but won't be accessible")
    
    print("\n   Option 2: Clean database (remove entries without files)")
    print("   - Run: python clean_database.py")
    print("   - This will remove database entries for missing files")
    print("   - Only CVs with files on disk will remain")
    
    print("\n   Option 3: Keep database as-is")
    print("   - CVs without files will show error when trying to download")
    print("   - Search will still work")
    print("   - You can filter them out in the UI")

print("\n" + "=" * 80)
print("Sync analysis complete!")
print("=" * 80)
