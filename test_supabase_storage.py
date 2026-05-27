"""
Test script to verify Supabase storage is working.
Run this to debug why data isn't being stored.
"""
import sys
from supabase_storage import SupabaseStorage

def test_supabase_connection():
    """Test Supabase connection."""
    print("=" * 60)
    print("TEST 1: Supabase Connection")
    print("=" * 60)
    
    try:
        storage = SupabaseStorage()
        print("✅ Supabase storage initialized")
        print(f"   Table: {storage.table_name}")
        print(f"   Client: {storage.client is not None}")
        return storage
    except Exception as e:
        print(f"❌ Failed to initialize Supabase: {e}")
        return None


def test_fetch_candidates(storage):
    """Test fetching existing candidates."""
    print("\n" + "=" * 60)
    print("TEST 2: Fetch Existing Candidates")
    print("=" * 60)
    
    try:
        response = storage.client.table(storage.table_name).select("anonymized_id, years_of_experience").limit(5).execute()
        
        if response.data:
            print(f"✅ Found {len(response.data)} candidates in database")
            for candidate in response.data:
                print(f"   - {candidate.get('anonymized_id')}: {candidate.get('years_of_experience')} years")
            return True
        else:
            print("⚠️  No candidates found in database")
            return False
            
    except Exception as e:
        print(f"❌ Failed to fetch candidates: {e}")
        return False


def test_store_dummy_candidate(storage):
    """Test storing a dummy candidate."""
    print("\n" + "=" * 60)
    print("TEST 3: Store Dummy Candidate")
    print("=" * 60)
    
    dummy_intelligence = {
        "anonymized_id": "TEST_12345678",
        "confidence_score": 85,
        "years_experience": 5,
        "seniority_level": "MID",
        "core_technical_skills": ["Python", "Django", "PostgreSQL"],
        "primary_domain": "Software Development",
        "cleaned_narrative": "Test candidate with 5 years of Python development experience.",
        "verdict_reason": "Strong technical skills match requirements.",
        "llm_provider": "test",
        "llm_model": "test-model"
    }

    try:
        print("Attempting to store test candidate...")
        result = storage.store_intelligence(dummy_intelligence)
        print(f"✅ Successfully stored test candidate")
        print(f"   Anonymized ID: {result.get('anonymized_id')}")
        print(f"   Confidence: {result.get('confidence_score')}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to store test candidate: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


def test_delete_dummy_candidate(storage):
    """Delete the test candidate."""
    print("\n" + "=" * 60)
    print("TEST 4: Cleanup Test Candidate")
    print("=" * 60)
    
    try:
        storage.client.table(storage.table_name).delete().eq("anonymized_id", "TEST_12345678").execute()
        print("✅ Test candidate deleted")
        return True
    except Exception as e:
        print(f"⚠️  Could not delete test candidate: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SUPABASE STORAGE TEST SUITE")
    print("=" * 60)
    
    # Test 1: Connection
    storage = test_supabase_connection()
    if not storage:
        print("\n❌ Cannot proceed without Supabase connection")
        return 1
    
    # Test 2: Fetch existing data
    test_fetch_candidates(storage)
    
    # Test 3: Store dummy candidate
    store_success = test_store_dummy_candidate(storage)
    
    # Test 4: Cleanup
    if store_success:
        test_delete_dummy_candidate(storage)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if store_success:
        print("✅ All tests passed! Supabase storage is working correctly.")
        print("\nIf your app isn't storing data, check:")
        print("1. App logs for errors (look for 'Could not store intelligence')")
        print("2. Verify intelligence extraction is successful")
        print("3. Check if 'error' field is present in intelligence data")
        return 0
    else:
        print("❌ Storage test failed. Check error messages above.")
        print("\nCommon issues:")
        print("1. Wrong SUPABASE_URL or SUPABASE_KEY in .env")
        print("2. Table 'cv_intelligence' doesn't exist")
        print("3. Missing required columns in table")
        print("4. RLS policies blocking inserts")
        return 1


if __name__ == "__main__":
    sys.exit(main())

