"""
End-to-End Testing Script
Tests the entire CV processing and search pipeline
"""
import os
import sys
import json
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quick_search import quick_search


def test_end_to_end():
    """Run comprehensive end-to-end tests"""
    print("=" * 80)
    print("END-TO-END TESTING")
    print("=" * 80)
    print()
    
    # Test scenarios with different job descriptions
    test_scenarios = [
        {
            'name': 'Java Developer',
            'jd': 'Senior Java Developer with Spring Boot, Microservices, AWS, Docker, Kubernetes. 5+ years experience required.',
            'expected_skills': ['java', 'spring', 'aws', 'docker']
        },
        {
            'name': 'Python Developer',
            'jd': 'Python Developer with Django, Flask, PostgreSQL, REST APIs. Experience with AWS and Docker preferred.',
            'expected_skills': ['python', 'django', 'flask', 'postgresql']
        },
        {
            'name': 'Frontend Developer',
            'jd': 'Frontend Developer with React, TypeScript, JavaScript, HTML, CSS. Experience with Redux and Next.js.',
            'expected_skills': ['react', 'typescript', 'javascript']
        },
        {
            'name': 'DevOps Engineer',
            'jd': 'DevOps Engineer with Kubernetes, Docker, AWS, CI/CD, Jenkins, Terraform. Linux administration required.',
            'expected_skills': ['kubernetes', 'docker', 'aws', 'jenkins']
        },
        {
            'name': 'Data Scientist',
            'jd': 'Data Scientist with Python, Machine Learning, TensorFlow, PyTorch, SQL. Experience with NLP and Computer Vision.',
            'expected_skills': ['python', 'machine', 'learning', 'tensorflow']
        }
    ]
    
    # Check database status
    print("1. Checking Database Status")
    print("-" * 80)
    intelligence_dir = Path('llm_analysis')
    processed_cvs = list(intelligence_dir.glob('*_intelligence.json'))
    print(f"   Processed CVs: {len(processed_cvs)}")
    
    if len(processed_cvs) == 0:
        print("   ❌ No processed CVs found!")
        print("   Run 'Process All Sample CVs' first")
        return False
    
    print(f"   ✓ Found {len(processed_cvs)} processed CVs")
    print()
    
    # Run tests for each scenario
    all_passed = True
    results = []
    
    for idx, scenario in enumerate(test_scenarios, 1):
        print(f"{idx}. Testing: {scenario['name']}")
        print("-" * 80)
        print(f"   JD: {scenario['jd'][:80]}...")
        print()
        
        try:
            # Run search
            start_time = time.time()
            matches = quick_search(scenario['jd'], top_n=10)
            elapsed = time.time() - start_time
            
            # Validate results
            if not matches:
                print(f"   ❌ No matches found")
                all_passed = False
                results.append({
                    'scenario': scenario['name'],
                    'status': 'FAILED',
                    'reason': 'No matches found'
                })
                continue
            
            # Check if top matches have expected skills
            top_match = matches[0]
            match_pct = top_match['match_percentage']
            matched_keywords = [k.lower() for k in top_match['matched_keywords']]
            
            # Count how many expected skills are in matched keywords
            found_skills = sum(1 for skill in scenario['expected_skills'] 
                             if any(skill in kw for kw in matched_keywords))
            
            print(f"   Top Match: {top_match['anonymized_id']} ({match_pct:.1f}%)")
            print(f"   Matched Keywords: {', '.join(matched_keywords[:10])}")
            print(f"   Expected Skills Found: {found_skills}/{len(scenario['expected_skills'])}")
            print(f"   Search Time: {elapsed:.3f}s")
            
            # Pass if at least 1 expected skill found or match > 20%
            if found_skills > 0 or match_pct > 20:
                print(f"   ✓ PASSED")
                results.append({
                    'scenario': scenario['name'],
                    'status': 'PASSED',
                    'top_match': top_match['anonymized_id'],
                    'match_pct': match_pct,
                    'search_time': elapsed
                })
            else:
                print(f"   ⚠️ WARNING: Low relevance")
                all_passed = False
                results.append({
                    'scenario': scenario['name'],
                    'status': 'WARNING',
                    'reason': 'Low relevance matches'
                })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            all_passed = False
            results.append({
                'scenario': scenario['name'],
                'status': 'ERROR',
                'reason': str(e)
            })
        
        print()
    
    # Performance test
    print("6. Performance Test")
    print("-" * 80)
    print("   Testing search speed with multiple queries...")
    
    perf_times = []
    for i in range(5):
        start = time.time()
        quick_search("Software Engineer with Python and AWS", top_n=10)
        elapsed = time.time() - start
        perf_times.append(elapsed)
    
    avg_time = sum(perf_times) / len(perf_times)
    print(f"   Average search time: {avg_time:.3f}s")
    print(f"   Min: {min(perf_times):.3f}s, Max: {max(perf_times):.3f}s")
    
    if avg_time < 2.0:
        print(f"   ✓ PASSED (< 2 seconds)")
    else:
        print(f"   ⚠️ WARNING: Slow search (> 2 seconds)")
        all_passed = False
    
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r['status'] == 'PASSED')
    failed = sum(1 for r in results if r['status'] in ['FAILED', 'ERROR'])
    warnings = sum(1 for r in results if r['status'] == 'WARNING')
    
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Warnings: {warnings}")
    print()
    
    if all_passed and failed == 0:
        print("✓ ALL TESTS PASSED")
        print()
        print("System is working correctly:")
        print("  - CVs are processed and in database")
        print("  - Search returns relevant results")
        print("  - Performance is acceptable (<2s)")
        print("  - Ready for production use")
    else:
        print("⚠️ SOME TESTS FAILED")
        print()
        print("Issues found:")
        for r in results:
            if r['status'] != 'PASSED':
                print(f"  - {r['scenario']}: {r.get('reason', 'Unknown')}")
    
    print("=" * 80)
    
    # Save results
    with open('test_results.json', 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_cvs': len(processed_cvs),
            'results': results,
            'performance': {
                'avg_search_time': avg_time,
                'min_search_time': min(perf_times),
                'max_search_time': max(perf_times)
            },
            'overall_status': 'PASSED' if all_passed and failed == 0 else 'FAILED'
        }, f, indent=2)
    
    print("\n✓ Results saved to test_results.json")
    
    return all_passed and failed == 0


if __name__ == '__main__':
    success = test_end_to_end()
    sys.exit(0 if success else 1)
