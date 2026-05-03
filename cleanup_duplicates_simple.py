"""
Simple duplicate cleanup - removes confirmed duplicates based on filename
"""
from supabase_storage import SupabaseStorage
from collections import defaultdict
import re

def extract_base_filename(filename: str) -> str:
    """Extract base filename without timestamps and prefixes."""
    if not filename:
        return ""
    
    # Remove timestamp prefixes
    name = re.sub(r'^\d{8}_\d{6}_', '', filename)
    name = re.sub(r'^REDACTED_\d{8}_\d{6}_', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^REDACTED_', '', name, flags=re.IGNORECASE)
    
    # Remove file extensions
    name = re.sub(r'\.(pdf|docx|doc|txt)$', '', name, flags=re.IGNORECASE)
    
    return name.lower().strip()

def main():
    print("="*80)
    print("SIMPLE DUPLICATE CLEANUP")
    print("="*80)
    
    storage = SupabaseStorage()
    
    # Get all candidates
    print("\nFetching candidates...")
    intel_response = storage.client.table('cv_intelligence').select(
        'anonymized_id, created_at'
    ).execute()
    
    mapping_response = storage.client.table('cv_filename_mapping').select(
        'anonymized_id, original_filename, anonymized_filename'
    ).execute()
    
    # Create mapping
    filename_map = {
        m['anonymized_id']: {
            'original': m.get('original_filename', ''),
            'anonymized': m.get('anonymized_filename', '')
        }
        for m in mapping_response.data
    }
    
    # Group by base filename
    file_groups = defaultdict(list)
    
    for intel in intel_response.data:
        anon_id = intel['anonymized_id']
        filenames = filename_map.get(anon_id, {'original': '', 'anonymized': ''})
        filename = filenames['original'] or filenames['anonymized']
        
        if not filename:
            continue
        
        base_name = extract_base_filename(filename)
        if base_name and len(base_name) > 5:
            file_groups[base_name].append({
                'anonymized_id': anon_id,
                'created_at': intel.get('created_at', ''),
                'filename': filename
            })
    
    # Find duplicates
    duplicates = {name: cands for name, cands in file_groups.items() if len(cands) > 1}
    
    print(f"✓ Total candidates: {len(intel_response.data)}")
    print(f"✓ Duplicate groups found: {len(duplicates)}")
    
    if not duplicates:
        print("\n✅ No duplicates found!")
        return
    
    # Calculate total duplicates to remove
    total_to_remove = sum(len(cands) - 1 for cands in duplicates.values())
    
    print(f"\n📊 Summary:")
    print(f"   Candidates to keep: {len(duplicates)}")
    print(f"   Duplicates to remove: {total_to_remove}")
    print(f"   After cleanup: {len(intel_response.data) - total_to_remove}")
    
    # Show top 10 duplicate groups
    print(f"\n🔍 Top 10 Duplicate Groups:")
    sorted_dupes = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
    
    for i, (name, cands) in enumerate(sorted_dupes[:10], 1):
        print(f"\n  {i}. {name[:50]}... ({len(cands)} copies)")
        cands_sorted = sorted(cands, key=lambda x: x.get('created_at', ''))
        print(f"     KEEP: {cands_sorted[0]['anonymized_id']} (created: {cands_sorted[0]['created_at'][:19]})")
        print(f"     DELETE: {len(cands)-1} duplicates")
    
    # Ask for confirmation
    print(f"\n{'='*80}")
    print(f"⚠️  WARNING: This will delete {total_to_remove} duplicate candidates!")
    print(f"   (Keeping the oldest upload of each CV)")
    print(f"{'='*80}")
    
    response = input("\nProceed with deletion? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Cleanup cancelled.")
        return
    
    # Delete duplicates
    print(f"\n{'='*80}")
    print("DELETING DUPLICATES...")
    print(f"{'='*80}\n")
    
    deleted_count = 0
    error_count = 0
    
    for name, cands in duplicates.items():
        # Sort by creation date, keep the first (oldest)
        cands_sorted = sorted(cands, key=lambda x: x.get('created_at', ''))
        to_delete = cands_sorted[1:]  # Delete all except the first
        
        for cand in to_delete:
            anon_id = cand['anonymized_id']
            try:
                # Delete in correct order
                try:
                    storage.client.table('cv_filename_mapping').delete().eq(
                        'anonymized_id', anon_id
                    ).execute()
                except Exception:
                    pass
                
                try:
                    storage.client.table('cv_embeddings').delete().eq(
                        'anonymized_id', anon_id
                    ).execute()
                except Exception:
                    pass
                
                storage.client.table('cv_intelligence').delete().eq(
                    'anonymized_id', anon_id
                ).execute()
                
                print(f"  ✓ Deleted: {anon_id}")
                deleted_count += 1
                
            except Exception as e:
                print(f"  ❌ Failed: {anon_id} - {e}")
                error_count += 1
    
    print(f"\n{'='*80}")
    print("CLEANUP COMPLETE")
    print(f"{'='*80}")
    print(f"✓ Deleted: {deleted_count} duplicates")
    print(f"❌ Errors: {error_count}")
    print(f"\n🎉 Your database now has {len(intel_response.data) - deleted_count} unique candidates!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
