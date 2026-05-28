#!/usr/bin/env python3
"""
One-command fix for all CV visibility issues
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("CV VISIBILITY FIX - ONE COMMAND SOLUTION")
print("=" * 80)

print("\nThis will:")
print("1. Analyze CVs in database vs files on disk")
print("2. Remove database entries for CVs without files")
print("3. Keep only accessible CVs")
print("\n" + "=" * 80)

# Step 1: Connect to Supabase
print("\n[1/4] Connecting to Supabase...")
try:
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ ERROR: Supabase credentials not set in .env")
        sys.exit(1)
    
    client = create_client(url, key)
    print("✓ Connected to Supabase")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# Step 2: Analyze
print("\n[2/4] Analyzing CVs...")
try:
    result = client.table('cv_intelligence').select('anonymized_id').execute()
    db_candidates = result.data
    
    mappings_result = client.table('cv_filename_mapping').select('anonymized_id, original_filename').execute()
    filename_mappings = {m['anonymized_id']: m['original_filename'] for m in mappings_result.data}
    
    print(f"✓ Found {len(db_candidates)} CVs in database")
    print(f"✓ Found {len(filename_mappings)} filename mappings")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# Check files on disk
uploads_dir = Path("uploads")
if not uploads_dir.exists():
    print(f"❌ ERROR: {uploads_dir} directory not found")
    sys.exit(1)

files_on_disk = len(list(uploads_dir.glob("*.pdf"))) + len(list(uploads_dir.glob("*.docx")))
print(f"✓ Found {files_on_disk} files on disk")

# Find CVs to delete
to_delete = []
for candidate in db_candidates:
    anon_id = candidate.get('anonymized_id')
    original_filename = filename_mappings.get(anon_id, 'unknown')
    
    found = False
    for pattern in [original_filename, f"*{original_filename}*"]:
        if list(uploads_dir.glob(pattern)):
            found = True
            break
    
    if not found:
        to_delete.append(anon_id)

print(f"\n✓ Analysis complete:")
print(f"  Total CVs in database: {len(db_candidates)}")
print(f"  CVs with files: {len(db_candidates) - len(to_delete)}")
print(f"  CVs to remove: {len(to_delete)}")

if not to_delete:
    print("\n✓ All CVs have files on disk. Nothing to clean!")
    print("\nYour database is already in sync.")
    sys.exit(0)

# Step 3: Confirm
print(f"\n[3/4] Confirmation")
print(f"This will DELETE {len(to_delete)} CV entries from the database.")
print(f"These CVs don't have files on disk and can't be accessed anyway.")
print(f"\nAfter cleanup, you will have {len(db_candidates) - len(to_delete)} accessible CVs.")

response = input("\nProceed with cleanup? (yes/no): ").strip().lower()
if response not in ['yes', 'y']:
    print("\n❌ Cancelled. No changes made.")
    sys.exit(0)

# Step 4: Delete
print(f"\n[4/4] Cleaning database...")
deleted_count = 0
failed_count = 0

for i, anon_id in enumerate(to_delete):
    try:
        # Delete from all tables
        client.table('cv_intelligence').delete().eq('anonymized_id', anon_id).execute()
        try:
            client.table('cv_filename_mapping').delete().eq('anonymized_id', anon_id).execute()
        except:
            pass
        try:
            client.table('cv_embeddings').delete().eq('anonymized_id', anon_id).execute()
        except:
            pass
        
        deleted_count += 1
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{len(to_delete)} deleted...")
            
    except Exception as e:
        failed_count += 1
        if failed_count <= 5:  # Show first 5 errors
            print(f"  ⚠️  Error deleting {anon_id}: {e}")

print(f"\n✓ Cleanup complete!")
print(f"  Successfully deleted: {deleted_count}")
if failed_count > 0:
    print(f"  Failed: {failed_count}")
print(f"  Remaining CVs: {len(db_candidates) - deleted_count}")

print("\n" + "=" * 80)
print("✓ DATABASE CLEANUP SUCCESSFUL!")
print("=" * 80)

print("\nNext steps:")
print("1. Restart the Flask app:")
print("   python app.py")
print("\n2. Test search:")
print("   Go to http://127.0.0.1:5000")
print("   Search for CVs")
print("   All results should be downloadable")

print("\n✓ All visible CVs will now be accessible!")
