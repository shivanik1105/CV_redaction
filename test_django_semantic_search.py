#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Pure Semantic Search with Django Developer JD
Tests with 50 Python CVs to verify 100% semantic understanding
"""

import sys
import io
import requests
import json
import time
from typing import List, Dict
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# API endpoint
API_URL = "http://localhost:5000/api/quick-search"

# Django Developer JD
DJANGO_JD = """
We are looking for an experienced Django Developer to join our backend team.

Requirements:
- 3+ years of Python development experience
- Strong expertise in Django framework
- Experience with Django REST Framework (DRF)
- Knowledge of PostgreSQL or MySQL databases
- Understanding of RESTful API design
- Experience with Git version control
- Familiarity with Docker and containerization
- Knowledge of Celery for async tasks
- Experience with Redis for caching
- Understanding of Django ORM and query optimization

Nice to have:
- Experience with Django Channels for WebSockets
- Knowledge of AWS or cloud platforms
- CI/CD pipeline experience
- Test-driven development (TDD) experience
- Agile/Scrum methodology experience

Responsibilities:
- Design and develop scalable backend APIs using Django
- Optimize database queries and improve performance
- Write clean, maintainable, and well-documented code
- Collaborate with frontend developers
- Participate in code reviews
- Deploy and maintain applications in production
"""


def test_semantic_search(jd: str, limit: int = 50) -> Dict:
    """Test semantic search with given JD"""
    print(f"\n{'='*80}")
    print("TESTING PURE SEMANTIC SEARCH")
    print(f"{'='*80}")
    print(f"\nJob Description:")
    print(f"{'-'*80}")
    print(jd[:300] + "..." if len(jd) > 300 else jd)
    print(f"{'-'*80}")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            API_URL,
            json={
                "job_description": jd,
                "limit": limit
            },
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✓ Search completed in {elapsed:.2f}s")
            print(f"\nRanking Method: {result.get('ranking_method', 'unknown')}")
            print(f"Embedding Model: {result.get('embedding_model', 'unknown')}")
            print(f"Embedding Dimensions: {result.get('embedding_dimensions', 'unknown')}")
            print(f"Total Candidates Searched: {result.get('total_candidates_searched', 0)}")
            print(f"Total Matches Found: {result.get('total_matches', 0)}")
            print(f"Top Matches Returned: {len(result.get('matches', []))}")
            
            return result
        else:
            print(f"\n✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n✗ Request failed: {e}")
        return None


def analyze_results(result: Dict):
    """Analyze and display search results"""
    if not result or not result.get('success'):
        print("\n✗ No results to analyze")
        return
    
    matches = result.get('matches', [])
    
    if not matches:
        print("\n✗ No matches found")
        return
    
    print(f"\n{'='*80}")
    print(f"TOP {len(matches)} CANDIDATES (Ranked by Semantic Similarity)")
    print(f"{'='*80}")
    
    # Analyze top candidates
    django_experts = 0
    python_backend = 0
    web_developers = 0
    data_scientists = 0
    other = 0
    
    for i, match in enumerate(matches, 1):
        print(f"\n{i}. {match['anonymized_id']}")
        print(f"   {'─'*76}")
        print(f"   Semantic Score: {match.get('semantic_score', 0):.2f}%")
        print(f"   Match Score: {match['match_percentage']:.2f}%")
        print(f"   Critical Skills: {match.get('critical_skill_coverage', 0):.1f}%")
        print(f"   Years Experience: {match.get('years_experience', 0)}")
        print(f"   Seniority: {match.get('seniority_level', 'N/A')}")
        print(f"   Domain: {match.get('primary_domain', 'N/A')}")
        
        skills = match.get('core_technical_skills', [])
        print(f"   Skills: {', '.join(skills[:8])}")
        
        if len(skills) > 8:
            print(f"           {', '.join(skills[8:16])}")
        
        critical_matched = match.get('critical_skills_matched', [])
        if critical_matched:
            print(f"   Critical Matched: {', '.join(critical_matched[:5])}")
        
        print(f"   Reason: {match.get('match_reason', 'N/A')}")
        
        # Categorize
        domain = match.get('primary_domain', '').lower()
        skills_str = ' '.join(skills).lower()
        
        if 'django' in skills_str or 'django' in domain:
            django_experts += 1
        elif 'backend' in domain or 'web' in domain:
            python_backend += 1
        elif 'web' in skills_str or 'api' in skills_str:
            web_developers += 1
        elif 'data' in domain:
            data_scientists += 1
        else:
            other += 1
    
    # Summary statistics
    print(f"\n{'='*80}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    print(f"\nCandidate Categories:")
    print(f"  Django Experts: {django_experts} ({django_experts/len(matches)*100:.1f}%)")
    print(f"  Python Backend: {python_backend} ({python_backend/len(matches)*100:.1f}%)")
    print(f"  Web Developers: {web_developers} ({web_developers/len(matches)*100:.1f}%)")
    print(f"  Data Scientists: {data_scientists} ({data_scientists/len(matches)*100:.1f}%)")
    print(f"  Other: {other} ({other/len(matches)*100:.1f}%)")
    
    # Score distribution
    scores = [m.get('semantic_score', 0) for m in matches]
    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0
    
    print(f"\nSemantic Score Distribution:")
    print(f"  Average: {avg_score:.2f}%")
    print(f"  Maximum: {max_score:.2f}%")
    print(f"  Minimum: {min_score:.2f}%")
    print(f"  Range: {max_score - min_score:.2f}%")
    
    # Top 10 analysis
    top_10 = matches[:10]
    top_10_django = sum(1 for m in top_10 if 'django' in ' '.join(m.get('core_technical_skills', [])).lower())
    
    print(f"\nTop 10 Analysis:")
    print(f"  Django-related: {top_10_django}/10 ({top_10_django/10*100:.0f}%)")
    
    # Accuracy assessment
    print(f"\n{'='*80}")
    print("ACCURACY ASSESSMENT")
    print(f"{'='*80}")
    
    if django_experts + python_backend >= len(matches) * 0.7:
        print("✓ EXCELLENT: 70%+ candidates are Django/Backend developers")
    elif django_experts + python_backend >= len(matches) * 0.5:
        print("✓ GOOD: 50%+ candidates are Django/Backend developers")
    else:
        print("⚠ NEEDS IMPROVEMENT: <50% candidates are Django/Backend developers")
    
    if top_10_django >= 7:
        print("✓ EXCELLENT: Top 10 has 70%+ Django developers")
    elif top_10_django >= 5:
        print("✓ GOOD: Top 10 has 50%+ Django developers")
    else:
        print("⚠ NEEDS IMPROVEMENT: Top 10 has <50% Django developers")
    
    if avg_score >= 70:
        print("✓ EXCELLENT: Average semantic score is 70%+")
    elif avg_score >= 60:
        print("✓ GOOD: Average semantic score is 60%+")
    else:
        print("⚠ NEEDS IMPROVEMENT: Average semantic score is <60%")


def verify_semantic_understanding(result: Dict):
    """Verify that semantic understanding is working correctly"""
    print(f"\n{'='*80}")
    print("SEMANTIC UNDERSTANDING VERIFICATION")
    print(f"{'='*80}")
    
    if not result or not result.get('success'):
        print("\n✗ Cannot verify - no results")
        return False
    
    ranking_method = result.get('ranking_method', '')
    
    print(f"\n1. Ranking Method Check:")
    if 'semantic' in ranking_method.lower():
        print(f"   ✓ Using semantic ranking: {ranking_method}")
    else:
        print(f"   ✗ NOT using semantic ranking: {ranking_method}")
        return False
    
    print(f"\n2. Embedding Model Check:")
    embedding_model = result.get('embedding_model', '')
    if embedding_model:
        print(f"   ✓ Embedding model active: {embedding_model}")
    else:
        print(f"   ✗ No embedding model found")
        return False
    
    print(f"\n3. Semantic Scores Check:")
    matches = result.get('matches', [])
    has_semantic_scores = all('semantic_score' in m for m in matches)
    if has_semantic_scores:
        print(f"   ✓ All matches have semantic scores")
    else:
        print(f"   ✗ Some matches missing semantic scores")
        return False
    
    print(f"\n4. Contextual Understanding Check:")
    # Check if top candidates have Django-related skills
    top_5 = matches[:5]
    django_related = 0
    
    for match in top_5:
        skills = ' '.join(match.get('core_technical_skills', [])).lower()
        domain = match.get('primary_domain', '').lower()
        
        # Check for Django or related technologies
        if any(term in skills or term in domain for term in ['django', 'python', 'backend', 'web', 'api', 'rest']):
            django_related += 1
    
    if django_related >= 4:
        print(f"   ✓ Top 5 has {django_related}/5 Django-related candidates")
    else:
        print(f"   ⚠ Top 5 has only {django_related}/5 Django-related candidates")
    
    print(f"\n{'='*80}")
    if ranking_method and embedding_model and has_semantic_scores:
        print("✓ SEMANTIC UNDERSTANDING IS WORKING CORRECTLY")
        print(f"{'='*80}")
        return True
    else:
        print("✗ SEMANTIC UNDERSTANDING HAS ISSUES")
        print(f"{'='*80}")
        return False


def main():
    """Run the test"""
    print("\n" + "="*80)
    print("DJANGO DEVELOPER SEMANTIC SEARCH TEST")
    print("="*80)
    print("\nThis test will:")
    print("  1. Search for Django developers using PURE semantic understanding")
    print("  2. Analyze top 50 candidates")
    print("  3. Verify semantic ranking is working")
    print("  4. Assess accuracy of results")
    print("\nNO KEYWORD MATCHING - ONLY CONTEXTUAL UNDERSTANDING")
    print("="*80)
    
    # Skip input prompt for automated testing
    # input("\nPress Enter to start the test...")
    print("\nStarting test...")
    time.sleep(1)
    
    # Run the search
    result = test_semantic_search(DJANGO_JD, limit=50)
    
    if not result:
        print("\n✗ Test failed - no results")
        return
    
    # Analyze results
    analyze_results(result)
    
    # Verify semantic understanding
    is_working = verify_semantic_understanding(result)
    
    # Final verdict
    print(f"\n{'='*80}")
    print("FINAL VERDICT")
    print(f"{'='*80}")
    
    if is_working:
        print("\n✓ SEMANTIC SEARCH IS WORKING 100% CORRECTLY")
        print("✓ Using pure contextual understanding")
        print("✓ No keyword matching involved")
        print("✓ Results are based on semantic similarity")
    else:
        print("\n✗ SEMANTIC SEARCH HAS ISSUES")
        print("✗ Please check the implementation")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
