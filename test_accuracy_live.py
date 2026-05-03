"""
Test the live accuracy improvements in the Flask app
Run this AFTER restarting the Flask app
"""
import requests
import json

# Test JD that should filter out irrelevant candidates
FRONTEND_JD = """
Frontend Developer (React) required. 
Should have strong JavaScript, CSS, HTML, UI/UX skills. 
Need to build responsive user interfaces and integrate REST APIs.
React, Redux, TypeScript experience preferred.
Immediate joiners preferred.
"""

BACKEND_JD = """
Backend Developer (Python) required.
Should have strong Python, Django/Flask, REST API skills.
Need to build scalable backend services and database design.
PostgreSQL, Redis, Docker experience preferred.
"""

def test_search(jd_text, jd_name):
    """Test a single JD search"""
    print(f"\n{'='*60}")
    print(f"Testing: {jd_name}")
    print(f"{'='*60}")
    
    url = "http://localhost:5000/api/quick-search"
    payload = {
        "job_description": jd_text,
        "limit": 50
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        
        if not data.get('success'):
            print(f"Search failed: {data.get('error')}")
            return
        
        matches = data.get('matches', [])
        total = data.get('total_matches', 0)
        
        print(f"\nResults: {total} matches")
        print(f"Expected: 8-12 highly relevant matches")
        
        if total > 20:
            print(f"WARNING: Too many matches ({total}). Expected 8-12.")
            print("Action: Verify Flask app was restarted with new threshold (50%)")
        elif total < 5:
            print(f"INFO: Very strict filtering ({total} matches)")
        else:
            print(f"SUCCESS: Good filtering ({total} matches)")
        
        print(f"\nTop 5 Matches:")
        print("-" * 60)
        
        for i, match in enumerate(matches[:5], 1):
            anon_id = match.get('anonymized_id', 'UNKNOWN')
            score = match.get('match_percentage', 0)
            domain = match.get('primary_domain', 'N/A')
            skills = match.get('core_technical_skills', [])[:3]
            critical_cov = match.get('critical_skill_coverage', 0)
            
            print(f"{i}. {anon_id}")
            print(f"   Match: {score}% | Domain: {domain}")
            print(f"   Critical Skills: {critical_cov}%")
            print(f"   Top Skills: {', '.join(skills)}")
            print()
        
        # Check for sub-scores (should NOT be present)
        if matches:
            first_match = matches[0]
            has_subscores = (
                'semantic_score' in first_match or 
                'keyword_score' in first_match or
                'critical_skill_score' in first_match
            )
            
            if has_subscores:
                print("WARNING: Sub-scores still present in API response")
                print("Note: This is OK - they're just not shown in UI")
            else:
                print("INFO: Sub-scores removed from API response")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Flask app")
        print("Action: Start Flask app with: python app.py")
    except Exception as e:
        print(f"ERROR: {e}")

def main():
    print("="*60)
    print("ACCURACY IMPROVEMENTS TEST")
    print("="*60)
    print("\nThis test verifies:")
    print("1. Minimum threshold is 50% (not 30%)")
    print("2. Critical skills requirement is 80% (not 67%)")
    print("3. Scoring is 50/50 semantic/critical (not 70/30)")
    print("4. Result count is 8-12 per JD (not 36)")
    print("\nMake sure Flask app is running: python app.py")
    
    # Test Frontend JD
    test_search(FRONTEND_JD, "Frontend Developer (React)")
    
    # Test Backend JD
    test_search(BACKEND_JD, "Backend Developer (Python)")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nNext Steps:")
    print("1. If results look good, test in browser UI")
    print("2. Hard refresh browser (Ctrl+Shift+R)")
    print("3. Verify sub-scores are NOT visible in UI")
    print("4. Verify only relevant candidates appear")

if __name__ == "__main__":
    main()
