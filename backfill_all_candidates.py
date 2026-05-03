"""
Backfill all candidate data from llm_raw_response JSON backup.
This recovers data for candidates uploaded before columns were added.
"""
import json
import sys
from supabase_storage import SupabaseStorage

def backfill_all_candidates():
    """Extract data from llm_raw_response and update all columns."""
    print("=" * 60)
    print("BACKFILL ALL CANDIDATE DATA")
    print("=" * 60)
    
    storage = SupabaseStorage()
    
    # Get all candidates with their raw JSON
    print("\nFetching all candidates...")
    response = storage.client.table('cv_intelligence').select(
        'anonymized_id, llm_raw_response'
    ).execute()
    
    candidates = response.data
    print(f"✓ Found {len(candidates)} candidates")
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    print("\nBackfilling data...")
    for i, candidate in enumerate(candidates, 1):
        anon_id = candidate['anonymized_id']
        raw_json = candidate.get('llm_raw_response')
        
        if not raw_json:
            print(f"  [{i}/{len(candidates)}] ⚠️  {anon_id}: No raw data (skipping)")
            skipped_count += 1
            continue
        
        try:
            # Parse JSON backup
            if isinstance(raw_json, str):
                data = json.loads(raw_json)
            else:
                data = raw_json
            
            # Re-store using the storage function (it will populate all columns)
            storage.store_intelligence(data)
            
            print(f"  [{i}/{len(candidates)}] ✓ {anon_id}")
            success_count += 1
            
        except Exception as e:
            print(f"  [{i}/{len(candidates)}] ❌ {anon_id}: {e}")
            error_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("BACKFILL SUMMARY")
    print("=" * 60)
    print(f"✓ Successfully backfilled: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"⚠️  Skipped (no data): {skipped_count}")
    print(f"📊 Total: {len(candidates)}")
    
    if success_count > 0:
        print("\n🎉 Data recovery complete!")
        print("   All candidate data has been restored.")
        print("   Search should now work properly.")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    try:
        # First, remind user to run SQL migration
        print("\n⚠️  IMPORTANT: Make sure you've run the SQL migration first!")
        print("   File: supabase_add_missing_columns.sql")
        print("   Run it in Supabase SQL Editor before proceeding.")
        
        response = input("\nHave you run the SQL migration? (yes/no): ").strip().lower()
        if response != 'yes':
            print("\n❌ Please run the SQL migration first, then run this script.")
            sys.exit(1)
        
        print("\n⚠️  This will update all 367 candidates. Continue? (yes/no): ")
        response = input().strip().lower()
        if response != 'yes':
            print("\n❌ Backfill cancelled.")
            sys.exit(1)
        
        sys.exit(backfill_all_candidates())
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

