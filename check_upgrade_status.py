"""
Check the status of the embedding model upgrade.
This script verifies:
1. Model configuration in vector_search.py
2. Database schema (embedding dimensions)
3. Existing embeddings and their dimensions
4. Readiness for upgrade
"""
import os
import sys
from pathlib import Path

def check_model_config():
    """Check if vector_search.py is configured for 768d model."""
    print("=" * 60)
    print("1. CHECKING MODEL CONFIGURATION")
    print("=" * 60)
    
    try:
        from vector_search import get_vector_search_engine
        engine = get_vector_search_engine()
        
        print(f"✓ Model loaded: {engine.LOCAL_MODEL}")
        print(f"✓ Dimensions: {engine.dimensions}")
        
        if engine.dimensions == 768:
            print("✅ Model configuration is READY for upgrade")
            return True
        elif engine.dimensions == 384:
            print("⚠️  Model still configured for 384d (old model)")
            print("   Expected: all-mpnet-base-v2 (768d)")
            return False
        else:
            print(f"❌ Unexpected dimensions: {engine.dimensions}")
            return False
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False


def check_database_schema():
    """Check if database schema supports 768d embeddings."""
    print("\n" + "=" * 60)
    print("2. CHECKING DATABASE SCHEMA")
    print("=" * 60)
    
    try:
        from supabase_storage import SupabaseStorage
        storage = SupabaseStorage()
        
        # Try to query a sample embedding to check dimensions
        response = storage.client.table('cv_intelligence').select(
            'anonymized_id, embedding'
        ).limit(1).execute()
        
        if not response.data:
            print("⚠️  No candidates in database yet")
            return None
        
        sample = response.data[0]
        embedding = sample.get('embedding')
        
        if not embedding:
            print("⚠️  Sample candidate has no embedding")
            print("   Database schema may not be initialized")
            return None
        
        # Check embedding dimensions
        if isinstance(embedding, str):
            import json
            embedding = json.loads(embedding)
        
        dims = len(embedding)
        print(f"✓ Connected to Supabase")
        print(f"✓ Sample embedding dimensions: {dims}")
        
        if dims == 768:
            print("✅ Database schema is READY (768d)")
            return True
        elif dims == 384:
            print("⚠️  Database schema is OLD (384d)")
            print("   Need to run: supabase_upgrade_to_768d.sql")
            return False
        else:
            print(f"❌ Unexpected dimensions: {dims}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return None


def check_embeddings_status():
    """Check how many candidates have embeddings."""
    print("\n" + "=" * 60)
    print("3. CHECKING EMBEDDINGS STATUS")
    print("=" * 60)
    
    try:
        from supabase_storage import SupabaseStorage
        storage = SupabaseStorage()
        
        # Count total candidates
        total_response = storage.client.table('cv_intelligence').select(
            'anonymized_id', count='exact'
        ).execute()
        total_count = total_response.count
        
        # Count candidates with embeddings
        embedded_response = storage.client.table('cv_intelligence').select(
            'anonymized_id', count='exact'
        ).not_.is_('embedding', 'null').execute()
        embedded_count = embedded_response.count
        
        print(f"✓ Total candidates: {total_count}")
        print(f"✓ Candidates with embeddings: {embedded_count}")
        print(f"✓ Missing embeddings: {total_count - embedded_count}")
        
        if embedded_count == 0:
            print("⚠️  No embeddings generated yet")
            print("   Need to run: python regenerate_embeddings.py --force")
            return False
        elif embedded_count < total_count:
            print("⚠️  Some candidates missing embeddings")
            print("   Need to run: python regenerate_embeddings.py --force")
            return False
        else:
            print("✅ All candidates have embeddings")
            return True
            
    except Exception as e:
        print(f"❌ Error checking embeddings: {e}")
        return None


def print_upgrade_instructions(model_ready, db_ready, embeddings_ready):
    """Print next steps based on current status."""
    print("\n" + "=" * 60)
    print("UPGRADE STATUS & NEXT STEPS")
    print("=" * 60)
    
    if model_ready and db_ready and embeddings_ready:
        print("✅ UPGRADE COMPLETE!")
        print("\nAll systems ready:")
        print("  ✓ Model configured for 768d")
        print("  ✓ Database schema upgraded")
        print("  ✓ All embeddings regenerated")
        print("\nNext steps:")
        print("  1. Test with: python test_15_real_jds.py")
        print("  2. Restart Flask app")
        print("  3. Test semantic search in web interface")
        return
    
    print("⚠️  UPGRADE IN PROGRESS\n")
    
    step = 1
    
    if not model_ready:
        print(f"Step {step}: Update Model Configuration")
        print("  Status: ❌ NOT DONE")
        print("  Action: Model should already be updated in vector_search.py")
        print("  Verify: Check vector_search.py lines 30-31")
        step += 1
    else:
        print(f"✓ Model Configuration: READY (768d)")
    
    if not db_ready:
        print(f"\nStep {step}: Upgrade Database Schema")
        print("  Status: ❌ NOT DONE")
        print("  Action: Run SQL migration in Supabase SQL Editor")
        print("  File: supabase_upgrade_to_768d.sql")
        print("  Time: ~30 seconds")
        step += 1
    else:
        print(f"✓ Database Schema: READY (768d)")
    
    if not embeddings_ready:
        print(f"\nStep {step}: Regenerate All Embeddings")
        print("  Status: ❌ NOT DONE")
        print("  Action: python regenerate_embeddings.py --force")
        print("  Time: ~15-20 minutes for 139 candidates")
        step += 1
    else:
        print(f"✓ Embeddings: ALL REGENERATED")
    
    print("\n" + "=" * 60)
    print("📚 Full guide: EMBEDDING_MODEL_UPGRADE_GUIDE.md")
    print("=" * 60)


def main():
    """Run all checks and provide upgrade guidance."""
    print("\n🔍 EMBEDDING MODEL UPGRADE STATUS CHECK")
    print("Checking upgrade from 384d to 768d model...\n")
    
    # Run checks
    model_ready = check_model_config()
    db_ready = check_database_schema()
    embeddings_ready = check_embeddings_status()
    
    # Provide guidance
    print_upgrade_instructions(
        model_ready,
        db_ready if db_ready is not None else False,
        embeddings_ready if embeddings_ready is not None else False
    )
    
    # Exit code
    if model_ready and db_ready and embeddings_ready:
        return 0
    else:
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
