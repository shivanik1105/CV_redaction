#!/usr/bin/env python3
"""
Clean database: Remove CV entries that don't have files on disk
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("Database Cleanup Tool")
print("=" * 80)
print("This will remove CV entries from database that don't have files on disk")
print("=" * 80)

# Get confirmation
response = input("\nDo you want to proceed? (yes/no): ").strip().lower()
if response not in ['yes', 'y']:
    print("Cancelled.")
    exit(0)

# Connect to Supabase
print("\nConnecting to Supabase...")
try:
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("ERROR: Supabase credentials not set")
        exit(1)
    
    client = create_client(url, key)
    print("✓ Connected")
    
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

# Get all candidates
print("\nFetching candidates from database...")
try:
    result = client.table('cv_intelligence').select('anonymized_id').execute()
    db_candidates = result.data
    print(f"✓ Found {len(db_candidates)} candidates")
    
    # Get filename mappings
    mappings_result = client.table('cv_filename_mapping').select('anonymized_id, original_filename').execute()
    filename_mappings = {m['anonymized_id']: m['original_filename'] for m in mappings_result.data}
    print(f"✓ Found {len(filename_mappings)} filename mappings")
    
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

# Check which files exist
print("\nChecking which files exist on disk...")
uploads_dir = Path("uploads")
to_delete = []

for candidate in db_candidates:
    anon_id = candidate.get('anonymized_id')
    original_filename = filename_mappings.get(anon_id, 'unknown')
    
    # Check if file exists
    found = False
    if uploads_dir.exists():
        # Try to find the file
        for pattern in [original_filename, f"*{original_filename}*"]:
            if list(uploads_dir.glob(pattern)):
                found = True
                break
    
    if not found:
        to_delete.append(anon_id)

print(f"\n✓ Analysis complete:")
print(f"  - Total CVs in database: {len(db_candidates)}")
print(f"  - CVs with files on disk: {len(db_candidates) - len(to_delete)}")
print(f"  - CVs to delete (no files): {len(to_delete)}")

if not to_delete:
    print("\n✓ All CVs have files on disk. Nothing to delete.")
    exit(0)

# Confirm deletion
print(f"\nThis will DELETE {len(to_delete)} CV entries from the database.")
response = input("Are you sure? (yes/no): ").strip().lower()
if response not in ['yes', 'y']:
    print("Cancelled.")
    exit(0)

# Delete entries
print(f"\nDeleting {len(to_delete)} entries...")
deleted_count = 0
failed_count = 0

for anon_id in to_delete:
    try:
        # Delete from cv_intelligence
        client.table('cv_intelligence').delete().eq('anonymized_id', anon_id).execute()
        
        # Delete from cv_filename_mapping
        try:
            client.table('cv_filename_mapping').delete().eq('anonymized_id', anon_id).execute()
        except:
            pass  # Mapping might not exist
        
        # Delete from cv_embeddings (if exists)
        try:
            client.table('cv_embeddings').delete().eq('anonymized_id', anon_id).execute()
        except:
            pass  # Embeddings might not exist
        
        deleted_count += 1
        if deleted_count % 50 == 0:
            print(f"  Deleted {deleted_count}/{len(to_delete)}...")
            
    except Exception as e:
        print(f"  ERROR deleting {anon_id}: {e}")
        failed_count += 1

print(f"\n✓ Cleanup complete!")
print(f"  - Successfully deleted: {deleted_count}")
print(f"  - Failed: {failed_count}")
print(f"  - Remaining CVs in database: {len(db_candidates) - deleted_count}")

print("\n" + "=" * 80)
print("Database cleanup complete!")
print("=" * 80)
print("\nNext steps:")
print("1. Restart the Flask app: python app.py")
print("2. Search should now only show CVs with files on disk")
print("3. All CVs should be downloadable")
