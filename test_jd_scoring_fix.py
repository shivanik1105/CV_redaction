"""
Quick test: verify score_breakdown now contains skill_score, capability_score,
experience_score, domain_score for the two real JDs that were returning all zeros.
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

    # 5. Full intelligent match (the function that WAS used before semantic switch)
    result = compute_intelligent_candidate_match(CANDIDATE, jd_text, CANDIDATE_CV_TEXT)
    breakdown = result.get('score_breakdown', {})
    print(f"\n  Overall match_percentage: {result['match_percentage']}%")
    print(f"  Score breakdown:")
    for key, val in breakdown.items():
        status = "OK" if val > 0 else "X STILL ZERO"
        print(f"    {key:30s} = {val:6.1f}  {status}")

    # Check the keys the UI needs
    ui_keys = ['skill_score', 'capability_score', 'experience_score', 'domain_score']
    missing = [k for k in ui_keys if k not in breakdown]
    if missing:
        print(f"\n  ⚠ MISSING UI KEYS: {missing}")
    else:
        all_nonzero = all(breakdown.get(k, 0) > 0 for k in ui_keys)
        if all_nonzero:
            print(f"\n  [OK] All UI breakdown scores are non-zero!")
        else:
            zero_keys = [k for k in ui_keys if breakdown.get(k, 0) == 0]
            print(f"\n  [WARN] Some UI keys still zero: {zero_keys}")

    return breakdown


if __name__ == '__main__':
    print("Testing JD scoring fixes with real-world job descriptions...\n")

    b1 = test_jd("Data Scientist", JD_DATA_SCIENTIST)
    b2 = test_jd("Full Stack Developer", JD_FULLSTACK)

    print(f"\n{'='*70}")
    print("  FINAL VERDICT")
    print(f"{'='*70}")

    ui_keys = ['skill_score', 'capability_score', 'experience_score', 'domain_score']
    ds_ok = all(b1.get(k, 0) > 0 for k in ui_keys)
    fs_ok = all(b2.get(k, 0) > 0 for k in ui_keys)

    if ds_ok and fs_ok:
        print("\n  [PASS] Both JDs now produce non-zero breakdown scores!")
    else:
        if not ds_ok:
            print(f"\n  [FAIL] Data Scientist still has zero scores: {[k for k in ui_keys if b1.get(k,0)==0]}")
        if not fs_ok:
            print(f"\n  [FAIL] Full Stack still has zero scores: {[k for k in ui_keys if b2.get(k,0)==0]}")

    print()
