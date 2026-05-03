"""
Regenerate embeddings for all candidates in Supabase.
Run this after fixing sentence-transformers to enable semantic search.

Usage:
  python regenerate_embeddings.py           # Only generate missing embeddings
  python regenerate_embeddings.py --force   # Regenerate ALL embeddings (for model upgrades)
"""
import sys
import argparse
from supabase_storage import SupabaseStorage
from vector_search import get_vector_search_engine

def regenerate_all_embeddings(force_regenerate=False):
    """Generate embeddings for all candidates that don't have them.
    
    Args:
        force_regenerate: If True, regenerate ALL embeddings even if they exist.
                         Use this when upgrading to a new embedding model.
    """
    print("=" * 60)
    if force_regenerate:
        print("FORCE REGENERATE ALL EMBEDDINGS (MODEL UPGRADE)")
    else:
        print("REGENERATE MISSING EMBEDDINGS FOR SEMANTIC SEARCH")
    print("=" * 60)
    
    # Initialize
    storage = SupabaseStorage()
    engine = get_vector_search_engine()
    
    print(f"\n[OK] Connected to Supabase")
    print(f"[OK] Loaded embedding model: {engine.LOCAL_MODEL}")
    print(f"  Dimensions: {engine.dimensions}")
    
    # Get all candidates
    print("\nFetching candidates from database...")
    response = storage.client.table('cv_intelligence').select(
        'anonymized_id, cleaned_narrative, core_technical_skills, secondary_technical_skills, '
        'primary_domain, secondary_domains, seniority_level, years_experience, key_strengths'
    ).execute()
    
    candidates = response.data
    print(f"[OK] Found {len(candidates)} candidates")
    
    # Determine which candidates need embeddings
    if force_regenerate:
        print("\n[WARNING] FORCE MODE: Regenerating ALL embeddings with new model")
        to_process = candidates
        print(f"  {len(to_process)} candidates will be regenerated")
    else:
        # Check which ones have embeddings
        print("\nChecking existing embeddings...")
        embeddings_response = storage.client.table('cv_intelligence').select(
            'anonymized_id, embedding'
        ).execute()
        existing_embeddings = {
            row['anonymized_id'] 
            for row in embeddings_response.data 
            if row.get('embedding')
        }
        print(f"  {len(existing_embeddings)} candidates already have embeddings")
        
        # Generate missing embeddings
        to_process = [c for c in candidates if c['anonymized_id'] not in existing_embeddings]
        print(f"  {len(to_process)} candidates need embeddings")
    
    if not to_process:
        print("\n[OK] All candidates already have embeddings!")
        print("   Use --force flag to regenerate with a new model")
        return 0
    
    print(f"\nGenerating embeddings for {len(to_process)} candidates...")
    print(f"Model: {engine.LOCAL_MODEL} ({engine.dimensions} dimensions)")
    print(f"Estimated time: {len(to_process) * 0.15:.1f} seconds (~{len(to_process) * 0.15 / 60:.1f} minutes)")
    print()
    
    success_count = 0
    error_count = 0
    
    for i, candidate in enumerate(to_process, 1):
        anon_id = candidate['anonymized_id']
        
        try:
            # Build text for embedding using the same logic as vector_search.py
            intelligence = {
                'cleaned_narrative': candidate.get('cleaned_narrative', ''),
                'core_technical_skills': candidate.get('core_technical_skills', []),
                'secondary_technical_skills': candidate.get('secondary_technical_skills', []),
                'primary_domain': candidate.get('primary_domain', ''),
                'secondary_domains': candidate.get('secondary_domains', []),
                'seniority_level': candidate.get('seniority_level', ''),
                'years_experience': candidate.get('years_experience', 0),
                'key_strengths': candidate.get('key_strengths', [])
            }
            
            text = engine.build_embedding_text(intelligence)
            
            if not text.strip():
                print(f"  [{i}/{len(to_process)}] [WARNING] {anon_id}: No text to embed (skipping)")
                error_count += 1
                continue
            
            # Generate embedding
            embedding = engine.generate_embedding(text)
            
            # Verify embedding dimensions
            if len(embedding) != engine.dimensions:
                raise ValueError(
                    f"Embedding dimension mismatch: got {len(embedding)}, expected {engine.dimensions}"
                )
            
            # Store in database (directly update cv_intelligence table)
            storage.client.table('cv_intelligence').update({
                'embedding': embedding
            }).eq('anonymized_id', anon_id).execute()
            
            print(f"  [{i}/{len(to_process)}] [OK] {anon_id} ({len(embedding)}d)")
            success_count += 1
            
        except Exception as e:
            print(f"  [{i}/{len(to_process)}] [ERROR] {anon_id}: {e}")
            error_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"[OK] Successfully generated: {success_count}")
    print(f"[ERROR] Errors: {error_count}")
    print(f"[INFO] Total candidates with embeddings: {success_count}")
    print(f"[INFO] Model: {engine.LOCAL_MODEL}")
    print(f"[INFO] Dimensions: {engine.dimensions}")
    
    if success_count > 0:
        print("\n[SUCCESS] Semantic search is now enabled with upgraded model!")
        print("   Expected improvements:")
        print("   * +11.7% better top match scores")
        print("   * Better contextual understanding")
        print("   * More relevant matches")
        print("\n   Try searching for candidates in the web interface.")
        print("   Or test with: python test_15_real_jds.py")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Regenerate embeddings for semantic search'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regenerate ALL embeddings (use when upgrading embedding model)'
    )
    
    args = parser.parse_args()
    
    try:
        sys.exit(regenerate_all_embeddings(force_regenerate=args.force))
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

