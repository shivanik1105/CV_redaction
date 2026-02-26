"""
Generate sample intelligence data from existing redacted CVs
This creates realistic intelligence records for dashboard testing
when LLM API is unavailable or quota is exceeded.
"""
import json
import os
import re
from pathlib import Path
from datetime import datetime
import random
import hashlib


def extract_skills_from_text(text):
    """Extract likely technical skills from CV text using pattern matching"""
    # Common tech skills to look for
    skill_patterns = [
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C\\+\\+', 'C#', 'Go', 'Rust', 'Ruby',
        'React', 'Angular', 'Vue', 'Node\\.js', 'Django', 'Flask', 'Spring', 'Spring Boot',
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'K8s', 'Jenkins', 'CI/CD',
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch',
        'REST', 'RESTful', 'GraphQL', 'Microservices', 'API',
        'Git', 'GitHub', 'GitLab', 'Jira', 'Agile', 'Scrum',
        'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch',
        'Linux', 'Unix', 'Bash', 'Shell',
        'HTML', 'CSS', 'SASS', 'Bootstrap', 'Tailwind',
        'Terraform', 'Ansible', 'Puppet', 'Chef',
        'Kafka', 'RabbitMQ', 'Redis', 'Celery',
        'MuleSoft', 'Salesforce', 'SAP', 'Oracle',
        'DevOps', 'SRE', 'Networking',
        'Pandas', 'NumPy', 'Scikit-learn',
        'Power BI', 'Tableau', 'Grafana', 'Prometheus',
        'Nginx', 'Apache', 'Tomcat',
        'OpenShift', 'Red Hat', 'Helm',
        '.NET', 'ASP.NET', 'Entity Framework',
        'Swift', 'Kotlin', 'Flutter', 'React Native',
        'Selenium', 'Jest', 'JUnit', 'PyTest',
        'RDBMS', 'NoSQL', 'DynamoDB', 'Cassandra',
    ]
    
    found_skills = []
    text_upper = text.upper()
    for skill in skill_patterns:
        if re.search(r'\b' + skill + r'\b', text, re.IGNORECASE):
            # Clean up regex chars for display
            clean = skill.replace('\\', '').replace('.', '.').replace('+', '+')
            if clean not in found_skills:
                found_skills.append(clean)
    
    return found_skills[:15]  # Max 15 skills


def estimate_experience(text):
    """Estimate years of experience from CV text"""
    # Look for year ranges
    year_ranges = re.findall(r'(20\d{2})\s*[-–to]+\s*(20\d{2}|present|till date|current)', text, re.IGNORECASE)
    
    if year_ranges:
        min_year = min(int(yr[0]) for yr in year_ranges)
        max_year = max(
            int(yr[1]) if yr[1].isdigit() else 2026
            for yr in year_ranges
        )
        years = max_year - min_year
        return max(1, min(years, 25))
    
    # Look for "X years" pattern
    years_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)', text, re.IGNORECASE)
    if years_match:
        return int(years_match.group(1))
    
    return random.randint(3, 8)


def determine_seniority(years):
    """Determine seniority level from years of experience"""
    if years <= 2:
        return "ENTRY"
    elif years <= 5:
        return "MID"
    elif years <= 10:
        return "SENIOR"
    elif years <= 15:
        return "LEAD"
    else:
        return "EXECUTIVE"


def determine_domain(skills, text):
    """Determine primary domain from skills and text"""
    domains = {
        'Backend Development': ['Python', 'Java', 'C#', '.NET', 'Spring', 'Django', 'Flask', 'Node.js'],
        'Frontend Development': ['React', 'Angular', 'Vue', 'JavaScript', 'TypeScript', 'HTML', 'CSS'],
        'DevOps': ['Docker', 'Kubernetes', 'Jenkins', 'CI/CD', 'Terraform', 'Ansible', 'AWS', 'Azure'],
        'Data Engineering': ['Kafka', 'Spark', 'Hadoop', 'ETL', 'Airflow', 'Data Pipeline'],
        'Data Science': ['Machine Learning', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy'],
        'Integration/Middleware': ['MuleSoft', 'Salesforce', 'SAP', 'API', 'Integration'],
        'Full Stack': ['React', 'Node.js', 'MongoDB', 'Express'],
        'Mobile Development': ['Swift', 'Kotlin', 'Flutter', 'React Native'],
        'QA/Testing': ['Selenium', 'Jest', 'JUnit', 'PyTest', 'Testing'],
    }
    
    scores = {}
    skills_lower = [s.lower() for s in skills]
    text_lower = text.lower()
    
    for domain, keywords in domains.items():
        score = sum(1 for kw in keywords if kw.lower() in skills_lower or kw.lower() in text_lower)
        if score > 0:
            scores[domain] = score
    
    if scores:
        return max(scores, key=scores.get)
    return "Software Engineering"


def generate_intelligence(redacted_file, job_description=""):
    """Generate intelligence record from a redacted CV file"""
    with open(redacted_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    filename = os.path.basename(redacted_file)
    
    # Extract skills
    skills = extract_skills_from_text(text)
    core_skills = skills[:8]
    secondary_skills = skills[8:]
    
    # Estimate experience
    years = estimate_experience(text)
    seniority = determine_seniority(years)
    
    # Determine domain
    primary_domain = determine_domain(skills, text)
    
    # Generate scores
    has_jd = bool(job_description.strip())
    if has_jd:
        # Score based on skill overlap
        jd_skills = extract_skills_from_text(job_description)
        overlap = len(set(s.lower() for s in core_skills) & set(s.lower() for s in jd_skills))
        match_score = min(100, max(30, int(overlap / max(len(jd_skills), 1) * 100)))
    else:
        match_score = random.randint(50, 85)
    
    confidence = random.randint(55, 95)
    
    # Determine verdict
    if match_score >= 75 and confidence >= 70:
        verdict = "SHORTLIST"
    elif match_score >= 55:
        verdict = "BACKUP"
    else:
        verdict = "REVIEW"
    
    requires_human_review = confidence < 70
    
    # Generate anonymized ID
    cand_num = random.randint(100, 999)
    anonymized_id = f"CAND_{cand_num}"
    
    # Create narrative from text
    lines = [l.strip() for l in text.split('\n') if l.strip() and '[' not in l and len(l.strip()) > 20]
    narrative_parts = lines[:3] if lines else ["Professional with experience in software development."]
    cleaned_narrative = " ".join(narrative_parts)[:500]
    
    # Leadership indicators
    leadership = []
    if re.search(r'lead|manager|architect|principal|director|head', text, re.IGNORECASE):
        leadership.append("Leadership role mentioned")
    if re.search(r'team\s+(?:of\s+)?\d+|managed\s+\d+', text, re.IGNORECASE):
        leadership.append("Team management")
    if re.search(r'mentor', text, re.IGNORECASE):
        leadership.append("Mentoring")
    
    intelligence = {
        "anonymized_id": anonymized_id,
        "original_filename": filename,
        "analysis_date": datetime.now().isoformat(),
        
        # Core fields
        "verdict": verdict,
        "confidence_score": confidence,
        "match_score": match_score,
        "verdict_reason": f"Candidate has {years} years experience with {', '.join(core_skills[:3]) if core_skills else 'relevant skills'}. "
                         f"{'Strong match for role requirements.' if match_score >= 75 else 'Partial match - some key skills present.' if match_score >= 55 else 'Requires human review for role fit.'}",
        
        # Experience
        "years_experience": years,
        "years_experience_range": f"{years}-{years+1}",
        "seniority_level": seniority,
        
        # Skills
        "core_technical_skills": core_skills,
        "secondary_technical_skills": secondary_skills,
        "frameworks_tools": [s for s in skills if s.lower() in ['react', 'angular', 'django', 'flask', 'spring', 'docker', 'kubernetes']],
        "soft_skills": ["Communication", "Team Collaboration"],
        "certifications": [],
        
        # Domain
        "primary_domain": primary_domain,
        "secondary_domains": [],
        "role_types": [seniority + " " + primary_domain.split()[0]],
        "leadership_indicators": leadership,
        
        # Education
        "highest_degree": "B.E./B.Tech" if re.search(r'B\.?E|B\.?Tech|Bachelor', text, re.IGNORECASE) else "Not specified",
        "field_of_study": "Computer Science" if re.search(r'comput|IT|information', text, re.IGNORECASE) else "Engineering",
        "education_level": "BACHELORS",
        
        # Analysis
        "cleaned_narrative": cleaned_narrative,
        "cleaned_text": text[:2000],
        "matched_requirements": core_skills[:5],
        "missing_requirements": [],
        "key_strengths": core_skills[:3],
        "potential_concerns": ["Auto-generated analysis - verify with full LLM analysis" if not has_jd else ""],
        
        # Search
        "search_keywords": core_skills + [primary_domain, seniority],
        "highlight_achievements": [],
        
        # Metadata
        "requires_human_review": requires_human_review,
        "llm_provider": "rule_based_extraction",
        "llm_model": "skill_matcher_v1",
        "extraction_timestamp": datetime.now().isoformat(),
        "job_description_hash": hashlib.sha256(job_description.encode()).hexdigest()[:16] if job_description else "",
        "original_cv_hash": hashlib.sha256(text.encode()).hexdigest(),
    }
    
    return intelligence


def main():
    """Generate intelligence for all redacted CVs"""
    redacted_dir = Path("redacted_output")
    output_dir = Path("llm_analysis")
    output_dir.mkdir(exist_ok=True)
    
    # Read job description if available
    jd_path = Path("example_job_description.txt")
    job_description = ""
    if jd_path.exists():
        with open(jd_path, 'r', encoding='utf-8') as f:
            job_description = f.read()
        print(f"Using job description from {jd_path}")
    
    cv_files = sorted(redacted_dir.glob("REDACTED_*.txt"))
    print(f"Found {len(cv_files)} redacted CVs")
    
    # Track used IDs to avoid duplicates
    used_ids = set()
    generated = 0
    
    for cv_file in cv_files:
        try:
            intelligence = generate_intelligence(str(cv_file), job_description)
            
            # Ensure unique ID
            while intelligence["anonymized_id"] in used_ids:
                intelligence["anonymized_id"] = f"CAND_{random.randint(100, 999)}"
            used_ids.add(intelligence["anonymized_id"])
            
            # Save
            output_file = output_dir / f"{cv_file.stem}_intelligence.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(intelligence, f, indent=2, ensure_ascii=False)
            
            print(f"  {intelligence['anonymized_id']}: {intelligence['verdict']} "
                  f"(match: {intelligence['match_score']}%, conf: {intelligence['confidence_score']}%) "
                  f"- {', '.join(intelligence['core_technical_skills'][:3])}")
            generated += 1
            
        except Exception as e:
            print(f"  Error processing {cv_file.name}: {e}")
    
    print(f"\nGenerated {generated} intelligence records in {output_dir}/")


if __name__ == "__main__":
    main()
