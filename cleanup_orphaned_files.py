"""
Clean up orphaned files in uploads, redacted_output, and llm_analysis folders.
Removes files that don't have corresponding database records.
"""
import os
from pathlib import Path
from supabase_storage import SupabaseStorage
import re

def get_all_valid_filenames_from_db():
    """Get all filenames that should exist based on database records."""
    storage = SupabaseStorage()
    
    # Get all anonymized IDs from database
    intel_response = storage.client.table('cv_intelligence').select('anonymized_id').execute()
    valid_ids = {record['anonymized_id'] for record in intel_response.data}
    
    # Get all filenames from mapping table
    mapping_response = storage.client.table('cv_filename_mapping').select(
        'anonymized_id, original_filename, anonymized_filename'
    ).execute()
    
    valid_filenames = set()
    
    for mapping in mapping_response.data:
        anon_id = mapping['anonymized_id']
        
        # Only include if the ID exists in cv_intelligence
        if anon_id in valid_ids:
            original = mapping.get('original_filename', '')
            anonymized = mapping.get('anonymized_filename', '')
            
            if original:
                valid_filenames.add(original)
            if anonymized:
                valid_filenames.add(anonymized)
    
    return valid_filenames, valid_ids

def extract_timestamp_from_filename(filename: str) -> str:
    """Extract timestamp prefix from filename (e.g., 20260406_220335)."""
    match = re.match(r'^(\d{8}_\d{6})_', filename)
    return match.group(1) if match else ''

def cleanup_folder(folder_path: str, valid_filenames: set, valid_ids: set, dry_run: bool = True):
    """Clean up orphaned files in a folder."""
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"  ⚠ Folder not found: {folder_path}")
        return 0, 0
    
    files = list(folder.glob('*'))
    if not files:
        print(f"  ✓ Folder is empty: {folder_path}")
        return 0, 0
    
    orphaned = []
    kept = []
    
    for file_path in files:
        if file_path.is_dir():
            continue
        
        filename = file_path.name
        
        # Check if filename is in valid set
        if filename in valid_filenames:
            kept.append(filename)
            continue
        
        # Check if any valid ID is in the filename
        found_valid_id = False
        for valid_id in valid_ids:
            if valid_id in filename:
                kept.append(filename)
                found_valid_id = True
                break
        
        if not found_valid_id:
            orphaned.append(file_path)
    
    print(f"\n  📁 {folder_path}:")
    print(f"     Total files: {len(files)}")
    print(f"     Valid files: {len(kept)}")
    print(f"     Orphaned files: {len(orphaned)}")
    
    if orphaned and not dry_run:
        print(f"\n     Deleting {len(orphaned)} orphaned files...")
        deleted = 0
        for file_path in orphaned:
            try:
                file_path.unlink()
                deleted += 1
            except Exception as e:
                print(f"       ❌ Failed to delete {file_path.name}: {e}")
        print(f"     ✓ Deleted {deleted} files")
        return deleted, len(orphaned) - deleted
    
    return 0, 0

def main():
    print("="*80)
    print("ORPHANED FILE CLEANUP")
    print("="*80)
    
    print("\n📊 Fetching valid filenames from database...")
    valid_filenames, valid_ids = get_all_valid_filenames_from_db()
    
    print(f"✓ Found {len(valid_ids)} valid candidate IDs")
    print(f"✓ Found {len(valid_filenames)} valid filenames")
    
    # Folders to clean
    folders = [
        'uploads',
        'redacted_output',
        'llm_analysis',
        'final_output'
    ]
    
    print(f"\n{'='*80}")
    print("DRY RUN - Scanning for orphaned files...")
    print(f"{'='*80}")
    
    total_orphaned = 0
    
    for folder in folders:
        deleted, errors = cleanup_folder(folder, valid_filenames, valid_ids, dry_run=True)
        # Count orphaned files
        folder_path = Path(folder)
        if folder_path.exists():
            files = [f for f in folder_path.glob('*') if f.is_file()]
            orphaned_count = 0
            for file_path in files:
                filename = file_path.name
                if filename not in valid_filenames:
                    found_valid_id = any(valid_id in filename for valid_id in valid_ids)
                    if not found_valid_id:
                        orphaned_count += 1
            total_orphaned += orphaned_count
    
    if total_orphaned == 0:
        print(f"\n✅ No orphaned files found! All files have corresponding database records.")
        return
    
    print(f"\n{'='*80}")
    print(f"⚠️  WARNING: Found {total_orphaned} orphaned files across all folders")
    print(f"{'='*80}")
    
    response = input("\nDelete orphaned files? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Cleanup cancelled.")
        return
    
    print(f"\n{'='*80}")
    print("DELETING ORPHANED FILES...")
    print(f"{'='*80}")
    
    total_deleted = 0
    total_errors = 0
    
    for folder in folders:
        deleted, errors = cleanup_folder(folder, valid_filenames, valid_ids, dry_run=False)
        total_deleted += deleted
        total_errors += errors
    
    print(f"\n{'='*80}")
    print("CLEANUP COMPLETE")
    print(f"{'='*80}")
    print(f"✓ Deleted: {total_deleted} orphaned files")
    print(f"❌ Errors: {total_errors}")
    
    if total_deleted > 0:
        print(f"\n🎉 Cleanup successful! Removed {total_deleted} orphaned files.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
