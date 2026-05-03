"""
Test 15 real-world job descriptions against the candidate database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

from supabase_storage import SupabaseStorage
from vector_search import get_vector_search_engine
from app import compute_semantic_candidate_match, _candidate_has_searchable_signal
import time

# 15 Real-world JDs
JDS = {
    "1. Software Engineer (Backend)": """
        We are hiring Software Engineer (Backend) with 1-3 yrs experience. 
        Candidate should be strong in Java/Python, APIs, DB concepts. 
        You will work on product features, debugging issues, improving performance. 
        Good to have cloud exp (AWS). Immediate joiners preferred. 
        Code repo experience like GitHub is expected.
    """,
    
    "2. Data Scientist": """
        Looking for Data Scientist – must have experience in Python, ML, SQL. 
        Role includes data analysis, model building, dashboards. 
        Should be able to explain insights to business team. 
        Freshers with strong projects can apply.
    """,
    
    "3. Full Stack Developer": """
        Urgent hiring Full Stack Dev (React + Node). 
        Need someone who can handle both frontend and backend. 
        Should know APIs, DB, deployment basics. 
        Startup environment, fast-paced work.
    """,
    
    "4. DevOps Engineer": """
        Hiring DevOps Engineer – exp in Docker, Kubernetes, CI/CD pipelines. 
        AWS knowledge preferred. 
        Role includes infra setup, deployment automation, monitoring systems.
    """,
    
    "5. Backend Developer": """
        Backend Developer needed – Node.js / Java. 
        Must have experience in API development, DB handling. 
        Good understanding of system design is a plus.
    """,
    
    "6. Frontend Developer": """
        Frontend Developer (React) required. 
        Should have strong JS, CSS, UI skills. 
        Need to build responsive UI, integrate APIs. 
        Immediate joiners preferred.
    """,
    
    "7. ML Engineer": """
        Looking for ML Engineer with exp in TensorFlow/PyTorch. 
        Should work on model building, deployment, optimization. 
        Knowledge of MLOps is bonus.
    """,
    
    "8. Data Analyst": """
        Hiring Data Analyst – SQL, Excel, Power BI required. 
        Role includes reporting, dashboard creation, business insights. 
        Communication skills important.
    """,
    
    "9. AI Engineer": """
        AI Engineer required – LLM, NLP, Python. 
        Experience with OpenAI APIs preferred. 
        Build AI-based features and integrate into products.
    """,
    
    "10. Technical Recruiter": """
        Looking for IT recruiter – sourcing candidates, screening, coordination. 
        Experience with LinkedIn and job portals required.
    """,
    
    "11. Cloud Engineer": """
        Cloud Engineer – AWS/Azure experience required. 
        Infra setup, monitoring, scaling systems. 
        Terraform knowledge is plus.
    """,
    
    "12. QA Engineer": """
        QA Tester needed – manual + automation testing. 
        Selenium knowledge preferred. 
        Should identify bugs and ensure quality.
    """,
    
    "13. Mobile Developer": """
        Hiring Android/iOS dev – Flutter/React Native. 
        Build mobile apps, fix bugs, improve performance.
    """,
    
    "14. Cybersecurity Analyst": """
        Security Analyst required – vulnerability testing, monitoring threats, securing systems. 
        Knowledge of security tools required.
    """,
    
    "15. Product Manager": """
        Product Manager needed – define roadmap, work with engineering, prioritize features. 
        Startup experience preferred.
    """
}

def test_single_jd(jd_name: str, jd_text: str, candidates: list, engine, show_top: int = 3):
    """Test a single JD and return results"""
    try:
        # Generate JD embedding
        jd_embedding = engine.generate_embedding(jd_text)
        
        # Search candidates
        matches = []
        
        for intel in candidates:
            if 'error' in intel and not intel.get('verdict'):
                continue
            if not _candidate_has_searchable_signal(intel):
                continue
            
            try:
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
                    'core_skills': intel.get('core_technical_skills', [])[:5],
                    'seniority': intel.get('seniority_level', 'N/A')
                })
            except Exception as e:
                continue
        
        # Sort by semantic score
        matches.sort(key=lambda x: x['semantic_score'], reverse=True)
        
        return {
            'jd_name': jd_name,
            'total_matches': len(matches),
            'top_matches': matches[:show_top]
        }
        
    except Exception as e:
        return {
            'jd_name': jd_name,
            'error': str(e),
            'total_matches': 0,
            'top_matches': []
        }

def main():
    print("="*100)
    print("TESTING 15 REAL-WORLD JOB DESCRIPTIONS")
    print("="*100)
    
    # Initialize
    print("\n📊 Initializing...")
    storage = SupabaseStorage()
    engine = get_vector_search_engine()
    
    # Fetch candidates
    print("📥 Fetching candidates from database...")
    all_candidates = storage.client.table('cv_intelligence').select('*').limit(200).execute()
    candidates = all_candidates.data
    print(f"✓ Loaded {len(candidates)} candidates\n")
    
    # Test each JD
    results = []
    total_start = time.time()
    
    for idx, (jd_name, jd_text) in enumerate(JDS.items(), 1):
        print(f"\n{'='*100}")
        print(f"Testing {jd_name}")
        print(f"{'='*100}")
        
        start = time.time()
        result = test_single_jd(jd_name, jd_text, candidates, engine, show_top=3)
        elapsed = time.time() - start
        
        results.append(result)
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
        else:
            print(f"✓ Found {result['total_matches']} matches (in {elapsed:.2f}s)")
            
            if result['top_matches']:
                print(f"\n🏆 Top 3 Matches:")
                for i, match in enumerate(result['top_matches'], 1):
                    print(f"\n   {i}. {match['anonymized_id']}")
                    print(f"      Semantic: {match['semantic_score']:.1f}% | Match: {match['match_percentage']:.1f}%")
                    print(f"      Experience: {match['years_experience']} yrs | Seniority: {match['seniority']}")
                    print(f"      Domain: {match['primary_domain']}")
                    skills_str = ', '.join(match['core_skills'][:3])
                    print(f"      Skills: {skills_str}")
            else:
                print("\n   ⚠ No matches found above 30% threshold")
    
    total_elapsed = time.time() - total_start
    
    # Summary
    print(f"\n\n{'='*100}")
    print("📊 SUMMARY REPORT")
    print(f"{'='*100}")
    print(f"\nTotal Time: {total_elapsed:.2f}s")
    print(f"Candidates Searched: {len(candidates)}")
    print(f"\n{'JD':<45} {'Matches':<10} {'Status'}")
    print("-"*100)
    
    total_matches = 0
    successful_jds = 0
    
    for result in results:
        jd_name = result['jd_name']
        matches = result['total_matches']
        total_matches += matches
        
        if matches > 0:
            successful_jds += 1
            status = "✓ SUCCESS"
        else:
            status = "⚠ NO MATCHES"
        
        print(f"{jd_name:<45} {matches:<10} {status}")
    
    print("-"*100)
    print(f"\n📈 Statistics:")
    print(f"   • JDs with matches: {successful_jds}/15 ({successful_jds/15*100:.0f}%)")
    print(f"   • Total matches found: {total_matches}")
    print(f"   • Average matches per JD: {total_matches/15:.1f}")
    
    if successful_jds == 15:
        print(f"\n🎉 EXCELLENT: All 15 JDs returned results!")
    elif successful_jds >= 12:
        print(f"\n✓ GOOD: {successful_jds}/15 JDs returned results")
    elif successful_jds >= 8:
        print(f"\n⚠ FAIR: {successful_jds}/15 JDs returned results")
    else:
        print(f"\n❌ NEEDS IMPROVEMENT: Only {successful_jds}/15 JDs returned results")
    
    print("\n" + "="*100)

if __name__ == '__main__':
    main()
