"""
Check for duplicate candidates in the database.
Identifies duplicates based on CV content hash or similar data.
"""
from supabase_storage import SupabaseStorage
from collections import defaultdict

def check_duplicates():
    """Find and report duplicate candidates."""
    print("=" * 60)
    print("DUPLICATE CANDIDATE CHECK")
    print("=" * 60)
    
    storage = SupabaseStorage()
    
    # Get all candidates
    print("\nFetching all candidates...")
    response = storage.client.table('cv_intelligence').select(
        'anonymized_id, original_cv_hash, created_at, llm_raw_response'
    ).execute()
    
    candidates = response.data
    print(f"✓ Found {len(candidates)} total candidates")
    
    # Group by CV hash
    hash_groups = defaultdict(list)
    no_hash_count = 0
    
    for candidate in candidates:
        cv_hash = candidate.get('original_cv_hash')
        if cv_hash:
            hash_groups[cv_hash].append(candidate)
        else:
            no_hash_count += 1
    
    # Find duplicates
    duplicates = {h: cands for h, cands in hash_groups.items() if len(cands) > 1}
    
    print(f"\n📊 Analysis:")
    print(f"   Unique CV hashes: {len(hash_groups)}")
    print(f"   Candidates without hash: {no_hash_count}")
    print(f"   Duplicate groups: {len(duplicates)}")
    
    if duplicates:
        print(f"\n⚠️  Found {len(duplicates)} groups of duplicates:")
        
        total_duplicates = 0
        for i, (cv_hash, cands) in enumerate(duplicates.items(), 1):
            print(f"\n  Group {i} (Hash: {cv_hash[:16]}...):")
            print(f"    Count: {len(cands)} duplicates")
            
            # Sort by creation date
            cands_sorted = sorted(cands, key=lambda x: x.get('created_at', ''))
            
            for j, cand in enumerate(cands_sorted):
                marker = "KEEP" if j == 0 else "DELETE"
                created = cand.get('created_at', 'unknown')[:19]
                print(f"      [{marker}] {cand['anonymized_id']} (created: {created})")
            
            total_duplicates += len(cands) - 1  # -1 because we keep one
        
        print(f"\n📊 Summary:")
        print(f"   Total candidates: {len(candidates)}")
        print(f"   Duplicates to remove: {total_duplicates}")
        print(f"   After cleanup: {len(candidates) - total_duplicates}")
        
        # Ask if user wants to delete
        print(f"\n⚠️  Do you want to delete {total_duplicates} duplicate candidates?")
        print("   (This will keep the oldest upload of each CV)")
        response = input("   Delete duplicates? (yes/no): ").strip().lower()
        
        if response == 'yes':
            delete_duplicates(storage, duplicates)
        else:
            print("\n❌ Cleanup cancelled. No changes made.")
    else:
        print("\n✅ No duplicates found! All candidates are unique.")
    
    return 0


def delete_duplicates(storage, duplicates):
    """Delete duplicate candidates, keeping the oldest one."""
    print("\n" + "=" * 60)
    print("DELETING DUPLICATES")
    print("=" * 60)
    
    deleted_count = 0
    error_count = 0
    
    for cv_hash, cands in duplicates.items():
        # Sort by creation date, keep the first (oldest)
        cands_sorted = sorted(cands, key=lambda x: x.get('created_at', ''))
        to_delete = cands_sorted[1:]  # Delete all except the first
        
        for cand in to_delete:
            anon_id = cand['anonymized_id']
            try:
                # CRITICAL: Delete in correct order to avoid foreign key constraint errors
                # 1. Delete from cv_filename_mapping FIRST (has FK to cv_intelligence)
                try:
                    storage.client.table('cv_filename_mapping').delete().eq(
                        'anonymized_id', anon_id
                    ).execute()
                except Exception as e:
                    # Only log if it's not a "not found" error
                    if 'not found' not in str(e).lower():
                        print(f"    ⚠️  Warning deleting from cv_filename_mapping: {e}")
                
                # 2. Delete from cv_embeddings (no FK constraints)
                try:
                    storage.client.table('cv_embeddings').delete().eq(
                        'anonymized_id', anon_id
                    ).execute()
                except Exception as e:
                    if 'not found' not in str(e).lower():
                        print(f"    ⚠️  Warning deleting from cv_embeddings: {e}")
                
                # 3. Finally delete from cv_intelligence (parent table)
                storage.client.table('cv_intelligence').delete().eq(
                    'anonymized_id', anon_id
                ).execute()
                
                print(f"  ✓ Deleted: {anon_id}")
                deleted_count += 1
                
            except Exception as e:
                print(f"  ❌ Failed to delete {anon_id}: {e}")
                error_count += 1
    
    print("\n" + "=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"✓ Deleted: {deleted_count} duplicates")
    print(f"❌ Errors: {error_count}")
    
    if deleted_count > 0:
        print("\n🎉 Duplicate cleanup complete!")
        print("   Your database now contains only unique candidates.")


if __name__ == "__main__":
    try:
        check_duplicates()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

