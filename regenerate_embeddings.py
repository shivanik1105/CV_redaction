"""
Regenerate embeddings for all candidates in Supabase.
Run this after fixing sentence-transformers to enable semantic search.
"""
import sys
from supabase_storage import SupabaseStorage
from vector_search import get_vector_search_engine

def regenerate_all_embeddings():
    """Generate embeddings for all candidates that don't have them."""
    print("=" * 60)
    print("REGENERATE EMBEDDINGS FOR SEMANTIC SEARCH")
    print("=" * 60)
    
    # Initialize
    storage = SupabaseStorage()
    engine = get_vector_search_engine()
    
    print(f"\n✓ Connected to Supabase")
    print(f"✓ Loaded embedding model: {engine.embedding_provider}")
    print(f"  Dimensions: {engine.dimensions}")
    
    # Get all candidates
    print("\nFetching candidates from database...")
    response = storage.client.table('cv_intelligence').select(
        'anonymized_id, cleaned_narrative, core_technical_skills, primary_domain, years_of_experience'
    ).execute()
    
    candidates = response.data
    print(f"✓ Found {len(candidates)} candidates")
    
    # Check which ones have embeddings
    print("\nChecking existing embeddings...")
    embeddings_response = storage.client.table('cv_embeddings').select('anonymized_id').execute()
    existing_embeddings = {row['anonymized_id'] for row in embeddings_response.data}
    print(f"  {len(existing_embeddings)} candidates already have embeddings")
    
    # Generate missing embeddings
    missing = [c for c in candidates if c['anonymized_id'] not in existing_embeddings]
    print(f"  {len(missing)} candidates need embeddings")
    
    if not missing:
        print("\n✅ All candidates already have embeddings!")
        return 0
    
    print(f"\nGenerating embeddings for {len(missing)} candidates...")
    success_count = 0
    error_count = 0
    
    for i, candidate in enumerate(missing, 1):
        anon_id = candidate['anonymized_id']
        
        try:
            # Build text for embedding
            parts = []
            
            if candidate.get('cleaned_narrative'):
                parts.append(candidate['cleaned_narrative'])
            
            if candidate.get('core_technical_skills'):
                skills = candidate['core_technical_skills']
                if isinstance(skills, list):
                    parts.append("Skills: " + ", ".join(skills))
            
            if candidate.get('primary_domain'):
                parts.append(f"Domain: {candidate['primary_domain']}")
            
            if candidate.get('years_of_experience'):
                parts.append(f"{candidate['years_of_experience']} years experience")
            
            text = " ".join(parts)
            
            if not text.strip():
                print(f"  [{i}/{len(missing)}] ⚠️  {anon_id}: No text to embed (skipping)")
                error_count += 1
                continue
            
            # Generate embedding
            embedding = engine.generate_embedding(text)
            
            # Store in database
            storage.store_embedding(
                anonymized_id=anon_id,
                embedding=embedding,
                embedding_model=engine.embedding_provider
            )
            
            print(f"  [{i}/{len(missing)}] ✓ {anon_id}")
            success_count += 1
            
        except Exception as e:
            print(f"  [{i}/{len(missing)}] ❌ {anon_id}: {e}")
            error_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Successfully generated: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total candidates with embeddings: {len(existing_embeddings) + success_count}")
    
    if success_count > 0:
        print("\n🎉 Semantic search is now enabled!")
        print("   Try searching for candidates in the web interface.")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(regenerate_all_embeddings())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

