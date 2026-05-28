#!/usr/bin/env python3
"""
Download missing CV files from Supabase storage to local disk.
This will sync your local uploads/ folder with the database.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("DOWNLOAD MISSING CVS FROM SUPABASE")
print("=" * 80)

print("\nThis will:")
print("1. Check which CVs are in the database")
print("2. Check which files are missing on disk")
print("3. Download missing files from Supabase storage")
print("4. Make all CVs accessible")
print("\n" + "=" * 80)

# Step 1: Connect to Supabase
print("\n[1/5] Connecting to Supabase...")
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

# Step 2: Get all CVs from database
print("\n[2/5] Fetching CV list from database...")
try:
    # Get all CV IDs
    result = client.table('cv_intelligence').select('anonymized_id').execute()
    db_candidates = result.data
    
    # Get filename mappings
    try:
        mappings_result = client.table('cv_filename_mapping').select('anonymized_id, original_filename').execute()
        filename_map = {m['anonymized_id']: m['original_filename'] for m in mappings_result.data}
    except:
        filename_map = {}
    
    # Combine data
    for candidate in db_candidates:
        anon_id = candidate['anonymized_id']
        candidate['original_filename'] = filename_map.get(anon_id, 'unknown')
    
    print(f"✓ Found {len(db_candidates)} CVs in database")
    print(f"✓ Found {len(filename_map)} filename mappings")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# Step 3: Check which files are missing
print("\n[3/5] Checking which files are missing on disk...")

uploads_dir = Path("uploads")
if not uploads_dir.exists():
    print(f"Creating {uploads_dir} directory...")
    uploads_dir.mkdir(parents=True, exist_ok=True)

missing_cvs = []
existing_cvs = []

for candidate in db_candidates:
    anon_id = candidate.get('anonymized_id')
    original_filename = candidate.get('original_filename', 'unknown')
    
    # Check if file exists on disk
    found = False
    
    # Try exact match
    if original_filename and original_filename != 'unknown':
        file_path = uploads_dir / original_filename
        if file_path.exists():
            found = True
        else:
            # Try pattern match (timestamped files)
            matches = list(uploads_dir.glob(f"*{original_filename}"))
            if matches:
                found = True
    
    if not found:
        missing_cvs.append({
            'anonymized_id': anon_id,
            'original_filename': original_filename
        })
    else:
        existing_cvs.append(anon_id)

print(f"\n✓ Analysis complete:")
print(f"  Total CVs in database: {len(db_candidates)}")
print(f"  CVs with files on disk: {len(existing_cvs)}")
print(f"  CVs missing files: {len(missing_cvs)}")

if not missing_cvs:
    print("\n✓ All CVs already have files on disk!")
    print("Your system is already in sync.")
    sys.exit(0)

# Step 4: Try to download from Supabase storage
print(f"\n[4/5] Attempting to download {len(missing_cvs)} missing files from Supabase storage...")

# Check if Supabase storage is configured
storage_bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "cv-uploads")

downloaded = 0
not_in_storage = 0
failed = 0

print(f"\nChecking Supabase storage bucket: {storage_bucket}")

for i, cv in enumerate(missing_cvs):
    anon_id = cv['anonymized_id']
    original_filename = cv['original_filename']
    
    if (i + 1) % 10 == 0:
        print(f"  Progress: {i + 1}/{len(missing_cvs)} checked...")
    
    try:
        # Try different possible storage paths
        possible_paths = [
            f"originals/{anon_id}.pdf",
            f"originals/{anon_id}.docx",
            f"uploads/{original_filename}",
            f"{anon_id}.pdf",
            f"{anon_id}.docx",
            original_filename
        ]
        
        file_downloaded = False
        
        for storage_path in possible_paths:
            try:
                # Try to download from storage
                response = client.storage.from_(storage_bucket).download(storage_path)
                
                if response:
                    # Determine file extension
                    ext = Path(storage_path).suffix or '.pdf'
                    local_filename = f"{anon_id}{ext}"
                    local_path = uploads_dir / local_filename
                    
                    # Save file
                    with open(local_path, 'wb') as f:
                        f.write(response)
                    
                    downloaded += 1
                    file_downloaded = True
                    print(f"  ✓ Downloaded: {anon_id} → {local_filename}")
                    break
                    
            except Exception:
                continue
        
        if not file_downloaded:
            not_in_storage += 1
            
    except Exception as e:
        failed += 1
        if failed <= 5:  # Show first 5 errors
            print(f"  ⚠️  Error downloading {anon_id}: {e}")

# Step 5: Summary
print(f"\n[5/5] Download complete!")
print(f"\n✓ Results:")
print(f"  Successfully downloaded: {downloaded}")
print(f"  Not found in storage: {not_in_storage}")
print(f"  Failed to download: {failed}")
print(f"  Already on disk: {len(existing_cvs)}")
print(f"  Total accessible: {len(existing_cvs) + downloaded}")

print("\n" + "=" * 80)

if downloaded > 0:
    print("✓ DOWNLOAD SUCCESSFUL!")
    print("=" * 80)
    print(f"\n{downloaded} CV files have been downloaded to uploads/")
else:
    print("⚠️  NO FILES DOWNLOADED")
    print("=" * 80)
    print("\nPossible reasons:")
    print("1. Files are not stored in Supabase storage")
    print("2. Storage bucket name is incorrect")
    print("3. Files were uploaded on a different machine")
    print("4. Files were imported from archive but archive is not available")

if not_in_storage > 0:
    print(f"\n⚠️  {not_in_storage} CVs are in the database but files are not in Supabase storage.")
    print("\nOptions:")
    print("1. Upload these CVs again using the Upload CV feature")
    print("2. Remove these entries from database: python fix_everything.py")
    print("3. If you have the original files, copy them to uploads/ folder")

print("\nNext steps:")
print("1. Restart the Flask app:")
print("   python app.py")
print("\n2. Test search:")
print("   Go to http://127.0.0.1:5000")
print("   Search for CVs")
print(f"   {len(existing_cvs) + downloaded} CVs should be downloadable")

if not_in_storage > 0:
    print(f"\n3. For the {not_in_storage} missing CVs:")
    print("   - Re-upload them using the Upload CV feature, OR")
    print("   - Clean database: python fix_everything.py")

