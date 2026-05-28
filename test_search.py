#!/usr/bin/env python
import requests
import time
import sys
import json

url = 'http://localhost:5000/api/quick-search'
jd = 'Senior Python Developer with DevOps, Docker, Kubernetes, AWS, CI/CD pipelines, Terraform, Ansible, Linux admin. 5+ years development, 3+ years DevOps.'

try:
    print(f"Testing FILTERED search API (50% minimum match)...")
    print(f"Job Description: {jd[:60]}...")
    print()
    
    start = time.time()
    response = requests.post(url, json={'job_description': jd}, timeout=60)
    elapsed = time.time() - start
    
    print(f'✓ Status: {response.status_code}')
    print(f'✓ Response time: {elapsed:.1f}s')
    
    if response.status_code == 200:
        data = response.json()
        
        # Check both 'candidates' and 'matches' fields
        candidates = data.get('candidates', [])
        matches = data.get('matches', [])
        num_results = max(len(candidates), len(matches))
        
        total_candidates_searched = data.get('total_candidates_searched', 0)
        total_matches = data.get('total_matches', 0)
        
        print(f'\n✓ RESULTS SUMMARY:')
        print(f'  Candidates searched: {total_candidates_searched}')
        print(f'  Matches found (>50%): {total_matches}')
        print(f'  Shown on page: {num_results}')
        print(f'  Data source: {data.get("data_source")}')
        print(f'  Ranking method: {data.get("ranking_method")}')
        
        # Show first few results from whichever field has data
        results = matches if matches else candidates
        if results:
            print(f'\n--- QUALITY MATCHES (Descending by Score) ---\n')
            for i, result in enumerate(results[:10]):
                print(f'{i+1}. {result.get("anonymized_id")} | Match: {result.get("match_percentage"):>5}% | Semantic: {result.get("semantic_score"):>5.1f}% | Years: {result.get("years_experience"):>2} | {result.get("seniority_level")}')
                print(f'   Skills: {", ".join(result.get("core_technical_skills", [])[:3])}...')
                print(f'   Why: {result.get("selection_basis", "")[0:80]}...\n')
        else:
            print(f'\n✗ No matches found')
    else:
        print(f'✗ Error: {response.text[:300]}')
except requests.exceptions.Timeout:
    print(f'✗ Request timed out after 60 seconds')
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()



