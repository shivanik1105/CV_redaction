"""
Test if the application actually returns search results with real JDs
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

from supabase_storage import SupabaseStorage
from vector_search import get_vector_search_engine
from app import compute_semantic_candidate_match, _candidate_has_searchable_signal

# Real JDs from test_jd_scoring_fix.py
JD_DATA_SCIENTIST = (
    "We are looking for a Data Scientist to analyze complex datasets, build predictive models, "
    "and generate actionable insights to support business decisions, using tools like Python, "
    "Pandas, NumPy, and Scikit-learn, along with SQL for data extraction; the role includes "
    "performing exploratory data analysis, feature engineering, model evaluation, and data "
    "visualization using tools such as Power BI or Tableau, with familiarity in machine learning "
    "and deep learning techniques and experience working with large datasets and cloud platforms preferred."
)

JD_FULLSTACK = (
    "We are seeking a Full Stack Developer to build end-to-end web applications, working on "
    "both frontend (React, Angular, or Vue) and backend (Node.js, Java, or Python), with "
    "responsibilities including UI development, API integration, database management, and "
    "ensuring application performance and responsiveness; candidates should have experience "
    "with RESTful services, modern JavaScript frameworks, relational or NoSQL databases, "
    "and version control tools like GitHub."
)

def test_search(jd_text: str, jd_name: str):
    """Test search with a real JD"""
    print(f"\n{'='*80}")
    print(f"Testing: {jd_name}")
    print(f"{'='*80}")
    
    try:
        # Initialize storage
        storage = SupabaseStorage()
        
        # Check if we have candidates
        print("\n1. Checking database for candidates...")
        response = storage.client.table('cv_intelligence').select('anonymized_id').limit(5).execute()
        
        if not response.data:
            print("   ❌ No candidates found in database!")
            return
        
        print(f"   ✓ Found {len(response.data)} candidates (showing first 5)")
        for c in response.data:
            print(f"     - {c['anonymized_id']}")
        
        # Get all candidates for search
        print("\n2. Fetching all candidates...")
        all_candidates = storage.client.table('cv_intelligence').select('*').limit(100).execute()
        candidates = all_candidates.data
        print(f"   ✓ Fetched {len(candidates)} candidates")
        
        # Generate JD embedding
        print("\n3. Generating JD embedding...")
        engine = get_vector_search_engine()
        jd_embedding = engine.generate_embedding(jd_text)
        print(f"   ✓ Generated embedding ({len(jd_embedding)} dimensions)")
        
        # Search candidates
        print("\n4. Searching candidates...")
        matches = []
        
        for intel in candidates:
            if 'error' in intel and not intel.get('verdict'):
                continue
            if not _candidate_has_searchable_signal(intel):
                continue
            
            # Compute semantic match
            ranked = compute_semantic_candidate_match(
                candidate=intel,
                jd_embedding=jd_embedding,
                job_description=jd_text
            )
            
            match_percentage = ranked['match_percentage']
            semantic_score = ranked.get('semantic_score', 0)
            
            # Apply threshold
            if match_percentage < 30:
                continue
            
            matches.append({
                'anonymized_id': intel.get('anonymized_id'),
                'match_percentage': match_percentage,
                'semantic_score': semantic_score,
                'years_experience': intel.get('years_experience', 0),
                'primary_domain': intel.get('primary_domain', ''),
                'core_skills': intel.get('core_technical_skills', [])[:3]
            })
        
        # Sort by semantic score
        matches.sort(key=lambda x: x['semantic_score'], reverse=True)
        
        print(f"\n5. Results:")
        print(f"   Total candidates searched: {len(candidates)}")
        print(f"   Matches found (>30% threshold): {len(matches)}")
        
        if matches:
            print(f"\n   Top 5 matches:")
            for i, match in enumerate(matches[:5], 1):
                print(f"\n   {i}. {match['anonymized_id']}")
                print(f"      Semantic Score: {match['semantic_score']:.1f}%")
                print(f"      Match Score: {match['match_percentage']:.1f}%")
                print(f"      Years Exp: {match['years_experience']}")
                print(f"      Domain: {match['primary_domain']}")
                print(f"      Skills: {', '.join(match['core_skills'][:3])}")
        else:
            print("\n   ❌ NO MATCHES FOUND!")
            print("   This means the search is returning 0 results.")
        
        return len(matches)
        
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == '__main__':
    print("Testing real JD search in the application...")
    
    ds_count = test_search(JD_DATA_SCIENTIST, "Data Scientist JD")
    fs_count = test_search(JD_FULLSTACK, "Full Stack Developer JD")
    
    print(f"\n{'='*80}")
    print("FINAL RESULTS")
    print(f"{'='*80}")
    print(f"Data Scientist JD: {ds_count} matches")
    print(f"Full Stack Developer JD: {fs_count} matches")
    
    if ds_count > 0 and fs_count > 0:
        print("\n✓ SUCCESS: Both JDs return results!")
    elif ds_count > 0 or fs_count > 0:
        print("\n⚠ PARTIAL: Only one JD returns results")
    else:
        print("\n❌ FAILURE: Both JDs return 0 results")
