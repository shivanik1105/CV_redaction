"""
Test the system with 15 messy, real-world JDs
This will reveal why we're getting random results
"""
import requests
import json
import time

# 15 Real-world messy JDs
MESSY_JDS = [
    {
        "name": "Software Engineer (Backend)",
        "jd": """We are hiring Software Engineer (Backend) with 1-3 yrs experience. 
Candidate should be strong in Java/Python, APIs, DB concepts. 
You will work on product features, debugging issues, improving performance. 
Good to have cloud exp (AWS). Immediate joiners preferred. 
Code repo experience like GitHub is expected."""
    },
    {
        "name": "Data Scientist",
        "jd": """Looking for Data Scientist – must have experience in Python, ML, SQL. 
Role includes data analysis, model building, dashboards. 
Should be able to explain insights to business team. 
Freshers with strong projects can apply."""
    },
    {
        "name": "Full Stack Developer",
        "jd": """Urgent hiring Full Stack Dev (React + Node). 
Need someone who can handle both frontend and backend. 
Should know APIs, DB, deployment basics. 
Startup environment, fast-paced work."""
    },
    {
        "name": "DevOps Engineer",
        "jd": """Hiring DevOps Engineer – exp in Docker, Kubernetes, CI/CD pipelines. 
AWS knowledge preferred. 
Role includes infra setup, deployment automation, monitoring systems."""
    },
    {
        "name": "Backend Developer",
        "jd": """Backend Developer needed – Node.js / Java. 
Must have experience in API development, DB handling. 
Good understanding of system design is a plus."""
    },
    {
        "name": "Frontend Developer (React)",
        "jd": """Frontend Developer (React) required. 
Should have strong JS, CSS, UI skills. 
Need to build responsive UI, integrate APIs. 
Immediate joiners preferred."""
    },
    {
        "name": "ML Engineer",
        "jd": """Looking for ML Engineer with exp in TensorFlow/PyTorch. 
Should work on model building, deployment, optimization. 
Knowledge of MLOps is bonus."""
    },
    {
        "name": "Data Analyst",
        "jd": """Hiring Data Analyst – SQL, Excel, Power BI required. 
Role includes reporting, dashboard creation, business insights. 
Communication skills important."""
    },
    {
        "name": "AI Engineer",
        "jd": """AI Engineer required – LLM, NLP, Python. 
Experience with OpenAI APIs preferred. 
Build AI-based features and integrate into products."""
    },
    {
        "name": "Technical Recruiter",
        "jd": """Looking for IT recruiter – sourcing candidates, screening, coordination. 
Experience with LinkedIn and job portals required."""
    },
    {
        "name": "Cloud Engineer",
        "jd": """Cloud Engineer – AWS/Azure experience required. 
Infra setup, monitoring, scaling systems. 
Terraform knowledge is plus."""
    },
    {
        "name": "QA Engineer",
        "jd": """QA Tester needed – manual + automation testing. 
Selenium knowledge preferred. 
Should identify bugs and ensure quality."""
    },
    {
        "name": "Mobile Developer",
        "jd": """Hiring Android/iOS dev – Flutter/React Native. 
Build mobile apps, fix bugs, improve performance."""
    },
    {
        "name": "Cybersecurity Analyst",
        "jd": """Security Analyst required – vulnerability testing, monitoring threats, securing systems. 
Knowledge of security tools required."""
    },
    {
        "name": "Product Manager",
        "jd": """Product Manager needed – define roadmap, work with engineering, prioritize features. 
Startup experience preferred."""
    }
]

def test_jd(jd_data, index):
    """Test a single JD"""
    name = jd_data['name']
    jd_text = jd_data['jd']
    
    print(f"\n{'='*80}")
    print(f"TEST {index}/15: {name}")
    print(f"{'='*80}")
    print(f"JD: {jd_text[:100]}...")
    
    url = "http://localhost:5000/api/quick-search"
    payload = {
        "job_description": jd_text,
        "limit": 50
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"ERROR: {response.status_code}")
            print(response.text[:200])
            return None
        
        data = response.json()
        
        if not data.get('success'):
            print(f"FAILED: {data.get('error')}")
            return None
        
        matches = data.get('matches', [])
        total = data.get('total_matches', 0)
        
        print(f"\nRESULTS: {total} matches")
        
        if total == 0:
            print("WARNING: NO MATCHES FOUND!")
            return {'name': name, 'total': 0, 'relevant': 0, 'top_domains': []}
        
        # Analyze top 10 results
        print(f"\nTop 10 Matches:")
        print("-" * 80)
        
        domains = []
        for i, match in enumerate(matches[:10], 1):
            anon_id = match.get('anonymized_id', 'UNKNOWN')
            score = match.get('match_percentage', 0)
            domain = match.get('primary_domain', 'N/A')
            skills = match.get('core_technical_skills', [])[:3]
            critical_cov = match.get('critical_skill_coverage', 0)
            
            domains.append(domain)
            
            print(f"{i:2d}. {anon_id:15s} | {score:5.1f}% | {domain:30s} | Crit: {critical_cov:5.1f}%")
            if i <= 3:
                print(f"    Skills: {', '.join(skills)}")
        
        # Check relevance
        print(f"\nDomain Distribution (Top 10):")
        from collections import Counter
        domain_counts = Counter(domains)
        for domain, count in domain_counts.most_common(5):
            print(f"  {domain}: {count}")
        
        return {
            'name': name,
            'total': total,
            'top_domains': list(domain_counts.most_common(3)),
            'top_score': matches[0].get('match_percentage', 0) if matches else 0
        }
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Flask app")
        print("Start Flask: python app.py")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def main():
    print("="*80)
    print("TESTING 15 MESSY REAL-WORLD JDs")
    print("="*80)
    print("\nThis test will reveal:")
    print("1. Are we getting relevant results?")
    print("2. Are critical skills being extracted properly?")
    print("3. Is domain matching working?")
    print("\nMake sure Flask is running: python app.py")
    
    input("\nPress Enter to start testing...")
    
    results = []
    success_count = 0
    
    for i, jd_data in enumerate(MESSY_JDS, 1):
        result = test_jd(jd_data, i)
        if result:
            results.append(result)
            if result['total'] > 0:
                success_count += 1
        time.sleep(0.5)  # Small delay between requests
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print(f"\nJDs Tested: {len(MESSY_JDS)}")
    print(f"JDs with Results: {success_count}/{len(MESSY_JDS)}")
    print(f"JDs with NO Results: {len(MESSY_JDS) - success_count}")
    
    if results:
        print(f"\nAverage Matches per JD: {sum(r['total'] for r in results) / len(results):.1f}")
        print(f"Average Top Score: {sum(r['top_score'] for r in results) / len(results):.1f}%")
    
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    if success_count < len(MESSY_JDS) * 0.8:
        print("\nWARNING: Less than 80% of JDs returned results!")
        print("\nPossible Issues:")
        print("1. Critical skills extraction failing on messy JDs")
        print("2. Threshold too strict (50% might be too high)")
        print("3. Embeddings not capturing informal language")
        print("\nRecommended Fixes:")
        print("1. Improve critical skills extraction for messy JDs")
        print("2. Add skill synonyms (JS=JavaScript, ML=Machine Learning)")
        print("3. Handle abbreviations better")
    else:
        print("\nSUCCESS: Most JDs returned results!")
        print("\nNext: Check if results are RELEVANT")
        print("- Frontend JD should return frontend candidates")
        print("- Backend JD should return backend candidates")
        print("- Data Science JD should return data scientists")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
