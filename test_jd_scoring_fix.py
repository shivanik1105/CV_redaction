"""test_jd_scoring_fix.py

This project no longer emits sub-score breakdowns (skill/capability/experience/domain)
in API payloads. This script remains as a quick sanity check that the match function
still returns an overall score and critical-skill signal for two representative JDs.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress noisy imports
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

from app import (
    _extract_critical_jd_skills,
    _extract_domain_terms_from_jd,
    _capability_focus_score,
    _extract_min_years_requirement,
    compute_intelligent_candidate_match,
    compute_local_keyword_match,
)

# ---- Two real JDs from the user ----
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

# ---- Simulated candidate (resembles the screenshot: Python, APIs, Flask, Django, ML) ----
CANDIDATE = {
    'anonymized_id': 'CAND_TEST',
    'core_technical_skills': ['Python', 'APIs', 'Flask', 'Django', 'Machine Learning'],
    'secondary_technical_skills': ['SQL', 'REST API', 'Git'],
    'frameworks_tools': ['Pandas', 'NumPy'],
    'primary_domain': 'Web Development',
    'secondary_domains': ['Backend'],
    'domain_expertise': [],
    'years_experience': 4,
    'seniority_level': 'MID',
    'key_strengths': ['Strong Python backend development', 'API design and integration'],
    'matched_requirements': [],
    'fitment_analysis': [],
    'verdict_reason': 'Profile extracted',
}

CANDIDATE_CV_TEXT = (
    "Python developer with 4 years experience building REST APIs using Flask and Django. "
    "Skilled in SQL, Pandas, NumPy, machine learning basics. Familiar with Git and GitHub."
)

def test_jd(label, jd_text):
    print(f"\n{'='*70}")
    print(f"  JD: {label}")
    print(f"{'='*70}")

    # 1. Critical skills extraction
    critical = _extract_critical_jd_skills(jd_text)
    print(f"\n  Critical skills extracted: {critical}")

    # 2. Domain terms
    domains = _extract_domain_terms_from_jd(jd_text)
    print(f"  Domain terms from JD:     {domains}")

    # 3. Capability focus score
    strength_text = " ".join(CANDIDATE.get('key_strengths', []))
    cap_score = _capability_focus_score(jd_text, strength_text)
    print(f"  Capability focus score:   {cap_score}")

    # 4. Min years requirement
    min_years = _extract_min_years_requirement(jd_text)
    print(f"  Min years requirement:    {min_years}")

    # 5. Full intelligent match (legacy weighted matcher)
    result = compute_intelligent_candidate_match(CANDIDATE, jd_text, CANDIDATE_CV_TEXT)
    print(f"\n  Overall match_percentage: {result['match_percentage']}%")

    breakdown = result.get('score_breakdown')
    if breakdown is None:
        print("  ✓ score_breakdown not present (expected)")
    else:
        print("  ⚠ score_breakdown present (unexpected)")

    return result


if __name__ == '__main__':
    print("Testing JD scoring fixes with real-world job descriptions...\n")

    r1 = test_jd("Data Scientist", JD_DATA_SCIENTIST)
    r2 = test_jd("Full Stack Developer", JD_FULLSTACK)

    print(f"\n{'='*70}")
    print("  FINAL VERDICT")
    print(f"{'='*70}")

    if isinstance(r1, dict) and isinstance(r2, dict):
        print("\n  [PASS] Both JDs produced match results")
    else:
        print("\n  [FAIL] One or more JDs did not produce results")

    print()
