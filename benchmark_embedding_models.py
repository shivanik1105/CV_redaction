"""
Benchmark different embedding models for CV-JD matching.
Tests 4 models and recommends the best for production.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import time
import numpy as np
from sentence_transformers import SentenceTransformer
from supabase_storage import SupabaseStorage

# Models to test
MODELS = {
    'all-MiniLM-L6-v2': {
        'name': 'sentence-transformers/all-MiniLM-L6-v2',
        'dimensions': 384,
        'description': 'Current model - Fast, lightweight',
        'size': '80MB'
    },
    'all-mpnet-base-v2': {
        'name': 'sentence-transformers/all-mpnet-base-v2',
        'dimensions': 768,
        'description': 'Better accuracy, still fast',
        'size': '420MB'
    },
    'all-MiniLM-L12-v2': {
        'name': 'sentence-transformers/all-MiniLM-L12-v2',
        'dimensions': 384,
        'description': 'Deeper MiniLM, better than L6',
        'size': '120MB'
    },
    'paraphrase-multilingual-mpnet-base-v2': {
        'name': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        'dimensions': 768,
        'description': 'Multilingual support, great for diverse CVs',
        'size': '970MB'
    }
}

# Test JDs (from your real tests)
TEST_JDS = {
    'Backend Developer': """
        Backend Developer needed – Node.js / Java. 
        Must have experience in API development, DB handling. 
        Good understanding of system design is a plus.
    """,
    
    'Data Scientist': """
        Looking for Data Scientist – must have experience in Python, ML, SQL. 
        Role includes data analysis, model building, dashboards. 
        Should be able to explain insights to business team.
    """,
    
    'Full Stack Developer': """
        Urgent hiring Full Stack Dev (React + Node). 
        Need someone who can handle both frontend and backend. 
        Should know APIs, DB, deployment basics.
    """,
    
    'DevOps Engineer': """
        Hiring DevOps Engineer – exp in Docker, Kubernetes, CI/CD pipelines. 
        AWS knowledge preferred. 
        Role includes infra setup, deployment automation, monitoring systems.
    """,
    
    'Mobile Developer': """
        Hiring Android/iOS dev – Flutter/React Native. 
        Build mobile apps, fix bugs, improve performance.
    """
}

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot_product / (norm1 * norm2))

def test_model(model_key, model_info, candidates):
    """Test a single model against all JDs and candidates."""
    print(f"\n{'='*80}")
    print(f"Testing: {model_key}")
    print(f"{'='*80}")
    print(f"Description: {model_info['description']}")
    print(f"Dimensions: {model_info['dimensions']}")
    print(f"Size: {model_info['size']}")
    
    # Load model
    print(f"\nLoading model...")
    start_load = time.time()
    try:
        model = SentenceTransformer(model_info['name'])
        load_time = time.time() - start_load
        print(f"✓ Loaded in {load_time:.2f}s")
    except Exception as e:
        print(f"❌ Failed to load: {e}")
        return None
    
    results = {
        'model_key': model_key,
        'load_time': load_time,
        'jd_results': {},
        'avg_matches': 0,
        'avg_top_score': 0,
        'avg_search_time': 0,
        'total_relevant_found': 0
    }
    
    # Test each JD
    for jd_name, jd_text in TEST_JDS.items():
        print(f"\n  Testing JD: {jd_name}")
        
        # Generate JD embedding
        start_embed = time.time()
        jd_embedding = model.encode(jd_text, convert_to_numpy=True)
        embed_time = time.time() - start_embed
        
        # Search candidates
        start_search = time.time()
        matches = []
        
        for candidate in candidates:
            # Build candidate text (handle None values)
            skills = candidate.get('core_technical_skills') or []
            domain = candidate.get('primary_domain') or 'General'
            years = candidate.get('years_experience') or 0
            seniority = candidate.get('seniority_level') or 'N/A'
            
            candidate_text = f"""
            Domain: {domain}
            Skills: {', '.join(skills[:10])}
            Experience: {years} years
            Seniority: {seniority}
            """
            
            # Generate candidate embedding
            candidate_embedding = model.encode(candidate_text, convert_to_numpy=True)
            
            # Compute similarity
            similarity = cosine_similarity(jd_embedding, candidate_embedding)
            
            if similarity >= 0.30:  # 30% threshold
                skills_list = candidate.get('core_technical_skills') or []
                matches.append({
                    'anonymized_id': candidate.get('anonymized_id'),
                    'similarity': similarity * 100,
                    'domain': candidate.get('primary_domain') or 'N/A',
                    'skills': skills_list[:3]
                })
        
        search_time = time.time() - start_search
        
        # Sort by similarity
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        top_score = matches[0]['similarity'] if matches else 0
        
        print(f"    Matches: {len(matches)}")
        print(f"    Top score: {top_score:.1f}%")
        print(f"    Search time: {search_time:.3f}s")
        
        if matches:
            print(f"    Top 3:")
            for i, match in enumerate(matches[:3], 1):
                skills_str = ', '.join(match['skills'])
                print(f"      {i}. {match['anonymized_id']} - {match['similarity']:.1f}% - {skills_str}")
        
        results['jd_results'][jd_name] = {
            'matches': len(matches),
            'top_score': top_score,
            'search_time': search_time,
            'embed_time': embed_time
        }
    
    # Calculate averages
    jd_count = len(TEST_JDS)
    results['avg_matches'] = sum(r['matches'] for r in results['jd_results'].values()) / jd_count
    results['avg_top_score'] = sum(r['top_score'] for r in results['jd_results'].values()) / jd_count
    results['avg_search_time'] = sum(r['search_time'] for r in results['jd_results'].values()) / jd_count
    
    # Count how many JDs found good matches (>50% top score)
    results['total_relevant_found'] = sum(1 for r in results['jd_results'].values() if r['top_score'] > 50)
    
    return results

def main():
    print("="*80)
    print("EMBEDDING MODEL BENCHMARK FOR CV-JD MATCHING")
    print("="*80)
    print("\nThis will test 4 different embedding models to find the best for production.")
    print("Testing against 5 real JDs and your candidate database.\n")
    
    # Load candidates
    print("Loading candidates from database...")
    storage = SupabaseStorage()
    response = storage.client.table('cv_intelligence').select(
        'anonymized_id, primary_domain, core_technical_skills, years_experience, seniority_level'
    ).limit(100).execute()
    
    candidates = response.data
    print(f"✓ Loaded {len(candidates)} candidates\n")
    
    # Test each model
    all_results = []
    
    for model_key, model_info in MODELS.items():
        result = test_model(model_key, model_info, candidates)
        if result:
            all_results.append(result)
    
    # Compare results
    print(f"\n\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"{'Model':<40} {'Avg Matches':<12} {'Avg Top Score':<15} {'Avg Time':<12} {'Relevant JDs'}")
    print("-"*80)
    
    for result in all_results:
        model_name = result['model_key']
        avg_matches = result['avg_matches']
        avg_top_score = result['avg_top_score']
        avg_time = result['avg_search_time']
        relevant = result['total_relevant_found']
        
        print(f"{model_name:<40} {avg_matches:<12.1f} {avg_top_score:<15.1f}% {avg_time:<12.3f}s {relevant}/5")
    
    # Recommend best model
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}\n")
    
    # Score each model
    scored_results = []
    for result in all_results:
        # Scoring criteria:
        # - Avg top score (40%): Higher is better
        # - Relevant JDs found (30%): More is better
        # - Speed (20%): Faster is better (inverse)
        # - Avg matches (10%): More is better
        
        score = (
            0.40 * (result['avg_top_score'] / 100) +
            0.30 * (result['total_relevant_found'] / 5) +
            0.20 * (1 / (result['avg_search_time'] + 0.1)) * 0.1 +  # Normalize speed
            0.10 * min(result['avg_matches'] / 20, 1.0)  # Cap at 20 matches
        )
        
        scored_results.append({
            'model': result['model_key'],
            'score': score,
            'result': result
        })
    
    # Sort by score
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Show rankings
    print("Rankings (by overall score):\n")
    for i, item in enumerate(scored_results, 1):
        model_key = item['model']
        score = item['score']
        result = item['result']
        
        print(f"{i}. {model_key}")
        print(f"   Overall Score: {score:.3f}")
        print(f"   Avg Top Match: {result['avg_top_score']:.1f}%")
        print(f"   Relevant JDs: {result['total_relevant_found']}/5")
        print(f"   Avg Speed: {result['avg_search_time']:.3f}s")
        print(f"   Avg Matches: {result['avg_matches']:.1f}")
        print()
    
    # Best model
    best = scored_results[0]
    best_model = best['model']
    best_info = MODELS[best_model]
    
    print(f"{'='*80}")
    print(f"🏆 RECOMMENDED MODEL: {best_model}")
    print(f"{'='*80}\n")
    
    print(f"Model: {best_info['name']}")
    print(f"Dimensions: {best_info['dimensions']}")
    print(f"Size: {best_info['size']}")
    print(f"Description: {best_info['description']}\n")
    
    print("Why this model:")
    print(f"  ✓ Best overall score: {best['score']:.3f}")
    print(f"  ✓ Average top match: {best['result']['avg_top_score']:.1f}%")
    print(f"  ✓ Found relevant matches for {best['result']['total_relevant_found']}/5 JDs")
    print(f"  ✓ Fast search: {best['result']['avg_search_time']:.3f}s per JD")
    print(f"  ✓ Good match count: {best['result']['avg_matches']:.1f} candidates per JD\n")
    
    print("To use this model:")
    print(f"  1. Update vector_search.py:")
    print(f"     DEFAULT_MODEL = '{best_info['name']}'")
    print(f"  2. Regenerate embeddings:")
    print(f"     python regenerate_embeddings.py")
    print(f"  3. Test with your JDs")
    print(f"  4. Deploy to production\n")
    
    # Show comparison with current
    current_result = next((r for r in all_results if r['model_key'] == 'all-MiniLM-L6-v2'), None)
    if current_result and best_model != 'all-MiniLM-L6-v2':
        improvement = ((best['result']['avg_top_score'] - current_result['avg_top_score']) / 
                      current_result['avg_top_score'] * 100)
        print(f"Improvement over current model:")
        print(f"  • {improvement:+.1f}% better top match scores")
        print(f"  • {best['result']['total_relevant_found'] - current_result['total_relevant_found']:+d} more relevant JDs")
        print(f"  • {(best['result']['avg_search_time'] - current_result['avg_search_time'])*1000:+.0f}ms speed difference\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
