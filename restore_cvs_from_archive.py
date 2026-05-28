#!/usr/bin/env python3
"""
Restore CV files from archive/samples to uploads/ folder.
This will make all CVs in the database accessible.
"""

import os
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("RESTORE CVS FROM ARCHIVE TO UPLOADS")
print("=" * 80)

print("\nThis will:")
print("1. Find all CV files in archive/samples")
print("2. Copy them to uploads/ folder")
print("3. Make all CVs in database accessible")
print("\n" + "=" * 80)

# Check if archive exists
archive_dir = Path("archive/samples")
if not archive_dir.exists():
    print(f"❌ ERROR: {archive_dir} directory not found")
    print("\nThe archive folder is missing. Options:")
    print("1. Download CVs from Supabase: python download_missing_cvs.py")
    print("2. Clean database: python fix_everything.py")
    sys.exit(1)

# Create uploads directory if it doesn't exist
uploads_dir = Path("uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)

print(f"\n[1/3] Scanning archive/samples for CV files...")

# Find all PDF and DOCX files in archive
cv_files = []
cv_files.extend(archive_dir.glob("**/*.pdf"))
cv_files.extend(archive_dir.glob("**/*.docx"))

# Filter out redacted/output files
original_files = [
    f for f in cv_files 
    if not any(x in f.name.lower() for x in ['redacted', 'masked', 'output', '_intelligence'])
]

print(f"✓ Found {len(original_files)} CV files in archive")

if not original_files:
    print("\n❌ No CV files found in archive/samples")
    sys.exit(1)

# Show what will be copied
print(f"\n[2/3] Files to copy:")
for i, file in enumerate(original_files[:10], 1):
    print(f"  {i}. {file.name}")
if len(original_files) > 10:
    print(f"  ... and {len(original_files) - 10} more")

# Ask for confirmation
print(f"\nThis will copy {len(original_files)} files to uploads/")
response = input("\nProceed? (yes/no): ").strip().lower()
if response not in ['yes', 'y']:
    print("\n❌ Cancelled. No files copied.")
    sys.exit(0)

# Copy files
print(f"\n[3/3] Copying files to uploads/...")

copied = 0
skipped = 0
failed = 0

for i, source_file in enumerate(original_files):
    try:
        dest_file = uploads_dir / source_file.name
        
        # Skip if file already exists
        if dest_file.exists():
            skipped += 1
            continue
        
        # Copy file
        shutil.copy2(source_file, dest_file)
        copied += 1
        
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{len(original_files)} processed...")
            
    except Exception as e:
        failed += 1
        if failed <= 5:  # Show first 5 errors
            print(f"  ⚠️  Error copying {source_file.name}: {e}")

print(f"\n✓ Copy complete!")
print(f"\nResults:")
print(f"  Successfully copied: {copied}")
print(f"  Already existed: {skipped}")
print(f"  Failed: {failed}")
print(f"  Total in uploads/: {copied + skipped}")

print("\n" + "=" * 80)
print("✓ FILES RESTORED FROM ARCHIVE!")
print("=" * 80)

# Now check database sync
print("\n[Bonus] Checking database sync...")

try:
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if url and key:
        client = create_client(url, key)
        result = client.table('cv_intelligence').select('anonymized_id').execute()
        db_count = len(result.data)
        
        files_count = len(list(uploads_dir.glob("*.pdf"))) + len(list(uploads_dir.glob("*.docx")))
        
        print(f"\nDatabase status:")
        print(f"  CVs in database: {db_count}")
        print(f"  Files in uploads/: {files_count}")
        
        if files_count >= db_count:
            print(f"\n✓ Good! You have enough files for all database entries.")
        else:
            print(f"\n⚠️  Still missing {db_count - files_count} files.")
            print("   Some CVs might still show 'file not found' errors.")
            
except Exception as e:
    print(f"\n⚠️  Could not check database: {e}")

print("\nNext steps:")
print("1. Restart the Flask app:")
print("   python app.py")
print("\n2. Test the application:")
print("   Go to http://127.0.0.1:5000")
print("   Search for CVs")
print("   Try downloading CVs")
print("\n3. If some CVs still show errors:")
print("   - Check the filename in the error message")
print("   - Look for that file in archive/samples")
print("   - Copy it manually to uploads/")

print("\n✓ Your CVs have been restored!")

