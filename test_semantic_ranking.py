#!/usr/bin/env python3
"""
Test Semantic Ranking vs Keyword Ranking
Shows the difference between contextual understanding and keyword matching
"""

import requests
import json
from typing import List, Dict

# API endpoint
API_URL = "http://localhost:5000/api/quick-search"

# Test JDs
TEST_JDS = [
    {
        "name": "Scalable Microservices (Semantic Test)",
        "jd": "Looking for a developer to build scalable microservices architecture with containerization and orchestration",
        "expected_keywords": ["microservices", "scalable", "containerization", "orchestration"],
        "semantic_matches": ["docker", "kubernetes", "distributed systems", "cloud native"]
    },
    {
        "name": "Backend API Development",
        "jd": "Need a backend engineer with experience in RESTful API development and database optimization",
        "expected_keywords": ["backend", "api", "restful", "database"],
        "semantic_matches": ["django", "flask", "fastapi", "postgresql", "mongodb"]
    },
    {
        "name": "Data Pipeline Engineering",
        "jd": "Seeking someone to build data pipelines for processing large datasets",
        "expected_keywords": ["data", "pipeline", "processing", "datasets"],
        "semantic_matches": ["spark", "airflow", "etl", "data engineering"]
    }
]


def test_search(jd_text: str, use_semantic: bool = True) -> Dict:
    """Test search with given JD"""
    try:
        response = requests.post(
            API_URL,
            json={
                "job_description": jd_text,
                "limit": 10,
                "use_semantic": use_semantic
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None


def compare_results(jd_name: str, jd_text: str, expected_keywords: List[str], semantic_matches: List[str]):
    """Compare semantic vs keyword ranking"""
    print("\n" + "="*80)
    print(f"TEST: {jd_name}")
    print("="*80)
    print(f"\nJD: {jd_text}")
    print(f"\nExpected Keywords: {', '.join(expected_keywords)}")
    print(f"Semantic Matches: {', '.join(semantic_matches)}")
    
    # Test with semantic ranking
    print("\n" + "-"*80)
    print("SEMANTIC RANKING (Contextual Understanding)")
    print("-"*80)
    semantic_results = test_search(jd_text, use_semantic=True)
    
    if semantic_results and semantic_results.get('success'):
        matches = semantic_results.get('matches', [])
        ranking_method = semantic_results.get('ranking_method', 'unknown')
        search_time = semantic_results.get('search_time', 'N/A')
        
        print(f"Ranking Method: {ranking_method}")
        print(f"Search Time: {search_time}")
        print(f"Total Matches: {len(matches)}")
        print(f"\nTop 5 Candidates:")
        
        for i, match in enumerate(matches[:5], 1):
            print(f"\n{i}. {match['anonymized_id']}")
            print(f"   Match: {match['match_percentage']}%")
            if 'semantic_score' in match:
                print(f"   Semantic Score: {match['semantic_score']}%")
            print(f"   Skills: {', '.join(match['core_technical_skills'][:5])}")
            print(f"   Domain: {match['primary_domain']}")
            print(f"   Reason: {match['match_reason']}")
    else:
        print("No results or error occurred")
    
    # Test with keyword ranking
    print("\n" + "-"*80)
    print("KEYWORD RANKING (Keyword Matching)")
    print("-"*80)
    keyword_results = test_search(jd_text, use_semantic=False)
    
    if keyword_results and keyword_results.get('success'):
        matches = keyword_results.get('matches', [])
        ranking_method = keyword_results.get('ranking_method', 'unknown')
        search_time = keyword_results.get('search_time', 'N/A')
        
        print(f"Ranking Method: {ranking_method}")
        print(f"Search Time: {search_time}")
        print(f"Total Matches: {len(matches)}")
        print(f"\nTop 5 Candidates:")
        
        for i, match in enumerate(matches[:5], 1):
            print(f"\n{i}. {match['anonymized_id']}")
            print(f"   Match: {match['match_percentage']}%")
            print(f"   Skills: {', '.join(match['core_technical_skills'][:5])}")
            print(f"   Domain: {match['primary_domain']}")
            print(f"   Reason: {match['match_reason']}")
    else:
        print("No results or error occurred")
    
    # Compare top candidates
    if semantic_results and keyword_results:
        semantic_top = [m['anonymized_id'] for m in semantic_results.get('matches', [])[:5]]
        keyword_top = [m['anonymized_id'] for m in keyword_results.get('matches', [])[:5]]
        
        print("\n" + "-"*80)
        print("COMPARISON")
        print("-"*80)
        print(f"Semantic Top 5: {', '.join(semantic_top)}")
        print(f"Keyword Top 5:  {', '.join(keyword_top)}")
        
        overlap = set(semantic_top) & set(keyword_top)
        print(f"\nOverlap: {len(overlap)}/5 candidates")
        
        if len(overlap) < 5:
            print("\nDifferences:")
            semantic_only = set(semantic_top) - set(keyword_top)
            keyword_only = set(keyword_top) - set(semantic_top)
            
            if semantic_only:
                print(f"  Semantic found: {', '.join(semantic_only)}")
            if keyword_only:
                print(f"  Keyword found: {', '.join(keyword_only)}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("SEMANTIC vs KEYWORD RANKING TEST")
    print("="*80)
    print("\nThis test compares:")
    print("  1. SEMANTIC: Uses vector embeddings for contextual understanding")
    print("  2. KEYWORD: Uses keyword matching and weighted scoring")
    print("\nSemantic ranking should find candidates that match the MEANING,")
    print("not just the exact keywords.")
    
    for test in TEST_JDS:
        compare_results(
            jd_name=test['name'],
            jd_text=test['jd'],
            expected_keywords=test['expected_keywords'],
            semantic_matches=test['semantic_matches']
        )
        input("\nPress Enter to continue to next test...")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\nKey Observations:")
    print("  • Semantic ranking finds candidates based on CONTEXT")
    print("  • Keyword ranking finds candidates based on EXACT WORDS")
    print("  • Semantic is better for understanding intent")
    print("  • Keyword is faster but less accurate")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
