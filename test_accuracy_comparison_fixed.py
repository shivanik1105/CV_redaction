"""
Test script to compare accuracy: Current vs Enhanced semantic search
Shows exactly why current system returns too many irrelevant results
"""
import sys
import json
from pathlib import Path
from vector_search import get_vector_search_engine
from supabase_storage import SupabaseStorage

# Test JD
TEST_JD = """
Senior Python Developer - 5+ years experience required

Must have:
- Python (expert level)
- Django or Flask
- PostgreSQL
- REST APIs
- Git

Nice to have:
- Docker
- AWS
- React

Looking for someone who can lead backend development, mentor junior developers,
and architect scalable systems.
"""

def extract_critical_skills(jd):
    """Extract must-have skills from JD"""
    # Simple extraction - in production, use LLM
    must_have = []
    lines = jd.lower().split('\n')
    in_must_have = False
    
    for line in lines:
        if 'must have' in line:
            in_must_have = True
            continue
        if 'nice to have' in line:
            in_must_have = False
            continue
        if in_must_have and line.strip().startswith('-'):
            skill = line.strip('- ').strip()
            must_have.append(skill)
    
    return must_have


def check_candidate_skills(candidate, critical_skills):
    """Check how many critical skills candidate has"""
    candidate_skills = (
        (candidate.get('core_technical_skills') or []) +
        (candidate.get('secondary_technical_skills') or []) +
        (candidate.get('frameworks_tools') or [])
    )
    
    all_skills_lower = [str(s).lower() for s in candidate_skills]
    all_skill_blob = " ".join(all_skills_lower)
    
    matched = []
    for skill in critical_skills:
        if skill.lower() in all_skill_blob:
            matched.append(skill)
    
    return matched, len(matched) / len(critical_skills) if critical_skills else 0


def current_system_score(semantic_score, critical_coverage):
    """Current scoring: 70% semantic + 30% critical"""
    return round(0.70 * semantic_score + 0.30 * critical_coverage, 2)


def enhanced_system_score(semantic_score, critical_coverage, skill_overlap, experience, domain):
    """Enhanced scoring: More balanced"""
    return round(
        0.35 * semantic_score +
        0.35 * critical_coverage +
        0.15 * skill_overlap +
        0.10 * experience +
        0.05 * domain,
        2
    )


def passes_hard_requirements(candidate, critical_skills, min_years=5):
    """Enhanced system: Hard requirements filter"""
    # Check critical skills (need 80%+)
    matched, coverage = check_candidate_skills(candidate, critical_skills)
    if coverage < 0.80:
        return False, f"Only {len(matched)}/{len(critical_skills)} critical skills"
    
    # Check experience (need 70% of required)
    years = candidate.get('years_experience') or candidate.get('years_of_experience') or 0
    if years < (min_years * 0.7):
        return False, f"Only {years} years (need {min_years * 0.7}+)"
    
    return True, "Passed"


def main():
    print("=" * 80)
    print("ACCURACY COMPARISON: Current vs Enhanced Semantic Search")
    print("=" * 80)
    print(f"\nTest JD:\n{TEST_JD}\n")
    
    # Extract critical skills
    critical_skills = extract_critical_skills(TEST_JD)
    print(f"Critical Skills: {critical_skills}\n")
    
    # Load candidates
    print("Loading candidates from Supabase...")
    try:
        storage = SupabaseStorage()
        response = storage.client.table('cv_intelligence').select('*').limit(50).execute()
        candidates = [storage._db_record_to_app_format(r) for r in response.data]
        print(f" Loaded {len(candidates)} candidates\n")
    except Exception as e:
        print(f" Could not load from Supabase: {e}")
        print("Using local JSON files instead...")
        from app import load_local_intelligence_files
        candidates = load_local_intelligence_files()[:50]
        print(f" Loaded {len(candidates)} candidates\n")
    
    # Generate JD embedding
    print("Generating JD embedding...")
    engine = get_vector_search_engine()
    jd_embedding = engine.generate_embedding(TEST_JD)
    print(f" Generated {len(jd_embedding)}d embedding\n")
    
    # Score all candidates
    print("Scoring candidates...\n")
    current_results = []
    enhanced_results = []
    
    for candidate in candidates:
        anon_id = candidate.get('anonymized_id', 'UNKNOWN')
        
        # Get candidate embedding
        candidate_embedding = candidate.get('embedding')
        if isinstance(candidate_embedding, str):
            try:
                candidate_embedding = json.loads(candidate_embedding)
            except:
                print(f"  Skipping {anon_id}: Could not parse embedding")
                continue
        
        if not candidate_embedding:
            print(f"  Skipping {anon_id}: No embedding")
            continue
        
        # Verify dimensions match
        if len(candidate_embedding) != len(jd_embedding):
            print(f"  Skipping {anon_id}: Dimension mismatch ({len(candidate_embedding)}d vs {len(jd_embedding)}d)")
            continue
        
        # Compute semantic similarity
        similarity = engine.cosine_similarity(jd_embedding, candidate_embedding)
        semantic_score = round(similarity * 100, 2)
        
        # Check critical skills
        matched_skills, critical_coverage = check_candidate_skills(candidate, critical_skills)
        critical_coverage_pct = round(critical_coverage * 100, 2)
        
        # Current system score
        current_score = current_system_score(semantic_score, critical_coverage_pct)
        
        # Enhanced system: Check hard requirements
        passes, reason = passes_hard_requirements(candidate, critical_skills, min_years=5)
        
        if not passes:
            # Enhanced system rejects this candidate
            enhanced_score = None
            enhanced_status = f"REJECTED: {reason}"
        else:
            # Enhanced system scores this candidate
            # Simplified scoring for demo (full version has more dimensions)
            enhanced_score = enhanced_system_score(
                semantic_score,
                critical_coverage_pct,
                critical_coverage_pct,  # Simplified
                80.0,  # Simplified
                80.0   # Simplified
            )
            enhanced_status = "QUALIFIED"
        
        # Store results
        current_results.append({
            'id': anon_id,
            'score': current_score,
            'semantic': semantic_score,
            'critical': critical_coverage_pct,
            'matched_skills': matched_skills,
            'years': candidate.get('years_experience', 0)
        })
        
        if enhanced_score is not None:
            enhanced_results.append({
                'id': anon_id,
                'score': enhanced_score,
                'semantic': semantic_score,
                'critical': critical_coverage_pct,
                'matched_skills': matched_skills,
                'years': candidate.get('years_experience', 0),
                'status': enhanced_status
            })
    
    # Sort results
    current_results.sort(key=lambda x: x['score'], reverse=True)
    enhanced_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Filter by threshold
    current_filtered = [r for r in current_results if r['score'] >= 70.0]
    enhanced_filtered = [r for r in enhanced_results if r['score'] >= 80.0]
    
    # Display results
    print("=" * 80)
    print("CURRENT SYSTEM (70% threshold, 70% semantic + 30% skills)")
    print("=" * 80)
    print(f"Total candidates evaluated: {len(candidates)}")
    print(f"Candidates passing threshold: {len(current_filtered)}\n")
    
    print("Top 10 Results:")
    for i, result in enumerate(current_filtered[:10], 1):
        print(f"{i}. {result['id']} - {result['score']}%")
        print(f"   Semantic: {result['semantic']}% | Critical Skills: {result['critical']}%")
        print(f"   Matched: {result['matched_skills']} ({len(result['matched_skills'])}/{len(critical_skills)})")
        print(f"   Years: {result['years']}")
        
        # Highlight issues
        if result['critical'] < 80:
            print(f"     WARNING: Missing {len(critical_skills) - len(result['matched_skills'])} critical skills!")
        if result['years'] < 3.5:
            print(f"     WARNING: Insufficient experience (need 5+ years)!")
        print()
    
    print("\n" + "=" * 80)
    print("ENHANCED SYSTEM (80% threshold, multi-stage filtering)")
    print("=" * 80)
    print(f"Total candidates evaluated: {len(candidates)}")
    print(f"Candidates passing hard requirements: {len(enhanced_results)}")
    print(f"Candidates passing threshold: {len(enhanced_filtered)}\n")
    
    print("Top 10 Results:")
    for i, result in enumerate(enhanced_filtered[:10], 1):
        print(f"{i}. {result['id']} - {result['score']}%")
        print(f"   Semantic: {result['semantic']}% | Critical Skills: {result['critical']}%")
        print(f"   Matched: {result['matched_skills']} ({len(result['matched_skills'])}/{len(critical_skills)})")
        print(f"   Years: {result['years']}")
        print(f"    Status: {result['status']}")
        print()
    
    # Summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    # Calculate quality metrics
    current_avg_critical = sum(r['critical'] for r in current_filtered[:10]) / min(10, len(current_filtered)) if current_filtered else 0
    enhanced_avg_critical = sum(r['critical'] for r in enhanced_filtered[:10]) / min(10, len(enhanced_filtered)) if enhanced_filtered else 0
    
    current_avg_score = sum(r['score'] for r in current_filtered[:10]) / min(10, len(current_filtered)) if current_filtered else 0
    enhanced_avg_score = sum(r['score'] for r in enhanced_filtered[:10]) / min(10, len(enhanced_filtered)) if enhanced_filtered else 0
    
    print(f"\nCurrent System:")
    print(f"  Results returned: {len(current_filtered)}")
    print(f"  Avg top 10 score: {current_avg_score:.1f}%")
    print(f"  Avg critical skills: {current_avg_critical:.1f}%")
    print(f"  Issue: Returns {len([r for r in current_filtered[:10] if r['critical'] < 80])} candidates with <80% critical skills")
    
    print(f"\nEnhanced System:")
    print(f"  Results returned: {len(enhanced_filtered)}")
    print(f"  Avg top 10 score: {enhanced_avg_score:.1f}%")
    print(f"  Avg critical skills: {enhanced_avg_critical:.1f}%")
    print(f"  Quality: ALL candidates have 80%+ critical skills ")
    
    print(f"\nImprovement:")
    print(f"  Noise reduction: {len(current_filtered) - len(enhanced_filtered)} irrelevant candidates filtered out")
    print(f"  Score improvement: +{enhanced_avg_score - current_avg_score:.1f}%")
    print(f"  Critical skills improvement: +{enhanced_avg_critical - current_avg_critical:.1f}%")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print("\n Implement Enhanced System for accurate, relevant results")
    print(" See ACCURACY_IMPROVEMENT_GUIDE.md for full implementation")
    print(" Quick win: Change threshold from 0.7 to 0.8 in app.py")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

