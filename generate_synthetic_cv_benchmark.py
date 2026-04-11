#!/usr/bin/env python3
"""
Generate synthetic Python-developer CV profiles and benchmark recommendation quality.

Output:
- test_results/synthetic_cvs/*.json (60 profiles)
- test_results/synthetic_benchmark_report.json

This benchmark compares:
1. Keyword-only ranking
2. Weighted intelligent ranking (skills + capability + experience + domain)
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Tuple


ARCHETYPES = {
    "python_data_case": {
        "core": ["Python", "Pandas", "NumPy", "SQL", "scikit-learn", "Statistics"],
        "secondary": ["A/B Testing", "Data Visualization", "Hypothesis Testing", "Business Analytics"],
        "strengths": [
            "Strong case study solving and business problem framing",
            "Excellent problem solving using data-driven approaches",
            "Designs experiments and validates hypotheses"
        ],
        "domain": "Data Science",
        "narrative": "Built end-to-end data science solutions and presented measurable business impact through analytics."
    },
    "python_dsa": {
        "core": ["Python", "Data Structures", "Algorithms", "Dynamic Programming", "Graph Algorithms"],
        "secondary": ["Competitive Programming", "LeetCode", "System Design Basics"],
        "strengths": [
            "Very strong DSA and algorithmic optimization",
            "Fast at coding interviews and complexity reduction"
        ],
        "domain": "Software Engineering",
        "narrative": "Focused on algorithm-heavy engineering tasks with strong coding performance and optimization mindset."
    },
    "python_backend": {
        "core": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker"],
        "secondary": ["Microservices", "REST APIs", "CI/CD", "AWS"],
        "strengths": [
            "Designed scalable backend APIs",
            "Strong debugging and production incident handling"
        ],
        "domain": "Backend Platform",
        "narrative": "Developed production backend services and API platforms with reliability and scaling focus."
    },
    "python_mlops": {
        "core": ["Python", "MLflow", "Airflow", "Docker", "Kubernetes", "AWS"],
        "secondary": ["Monitoring", "Model Deployment", "Feature Store", "Terraform"],
        "strengths": [
            "Productionized ML models with robust pipelines",
            "Strong platform engineering and MLOps practices"
        ],
        "domain": "MLOps",
        "narrative": "Operationalized machine learning systems with automated deployment, monitoring, and retraining."
    },
    "python_automation": {
        "core": ["Python", "PyTest", "Selenium", "API Testing", "Postman"],
        "secondary": ["Jenkins", "Test Automation", "Regression Testing", "CI/CD"],
        "strengths": [
            "Built reliable automation frameworks",
            "Strong root cause analysis and bug triage"
        ],
        "domain": "QA Automation",
        "narrative": "Implemented automation strategy across UI and API layers to improve release quality."
    },
    "python_generalist": {
        "core": ["Python", "SQL", "Pandas", "NumPy", "FastAPI", "Docker"],
        "secondary": ["Problem Solving", "Team Collaboration", "Cloud Basics", "Testing"],
        "strengths": [
            "Good all-round software delivery and execution",
            "Strong coding discipline and collaboration"
        ],
        "domain": "Software Engineering",
        "narrative": "Worked on mixed backend and analytics tasks with solid execution across multiple projects."
    },
}


JDS = [
    {
        "name": "Python Data Scientist",
        "text": (
            "Need Python Data Scientist with strong case study solving, hypothesis testing, A/B testing, "
            "statistics, pandas, SQL, and business problem solving. 3+ years required."
        ),
        "relevant": {"python_data_case"},
        "ideal": "python_data_case"
    },
    {
        "name": "Python Backend Engineer",
        "text": (
            "Looking for Python backend engineer with FastAPI or Django, microservices, PostgreSQL, Docker, "
            "Redis, and system design. 4+ years experience."
        ),
        "relevant": {"python_backend"},
        "ideal": "python_backend"
    },
    {
        "name": "Python MLOps Engineer",
        "text": (
            "Hiring Python MLOps engineer with MLflow, Airflow, Kubernetes, Docker, cloud deployment, "
            "monitoring and model lifecycle management. 3+ years."
        ),
        "relevant": {"python_mlops"},
        "ideal": "python_mlops"
    },
]


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9+#./-]{2,}", text.lower())


def extract_min_years(jd: str):
    match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", jd.lower())
    if not match:
        return None
    try:
        return float(match.group(1))
    except Exception:
        return None


def keyword_score(candidate: Dict, jd_text: str) -> float:
    candidate_text = " ".join(
        candidate["core_technical_skills"]
        + candidate["secondary_technical_skills"]
        + [candidate["cleaned_narrative"], candidate["primary_domain"]]
    ).lower()
    jd_tokens = [t for t in tokenize(jd_text) if len(t) >= 3]
    if not jd_tokens:
        return 0.0
    hits = sum(1 for token in jd_tokens if token in candidate_text)
    return round((hits / len(jd_tokens)) * 100.0, 2)


def intelligent_score(candidate: Dict, jd_text: str) -> float:
    kd = keyword_score(candidate, jd_text)

    jd_tokens = set(tokenize(jd_text))
    skill_tokens = set(tokenize(" ".join(candidate["core_technical_skills"] + candidate["secondary_technical_skills"])))

    token_overlap = len(jd_tokens.intersection(skill_tokens))
    token_score = round((token_overlap / len(jd_tokens)) * 100.0, 2) if jd_tokens else 0.0

    strength_text = " ".join(candidate["key_strengths"]).lower()
    jd_lower = jd_text.lower()

    capability = 60.0
    if "case study" in jd_lower:
        capability = 100.0 if "case study" in strength_text else 30.0
    if "problem solving" in jd_lower:
        capability = max(capability, 100.0 if "problem solving" in strength_text else 40.0)
    if "algorithm" in jd_lower or "dsa" in jd_lower:
        capability = max(capability, 100.0 if "algorithm" in strength_text or "dsa" in strength_text else 35.0)

    min_years = extract_min_years(jd_text)
    years = float(candidate["years_experience"])
    if min_years is None:
        experience = 60.0
    elif years >= min_years:
        experience = min(100.0, 80.0 + ((years - min_years) * 5.0))
    else:
        experience = max(0.0, (years / max(min_years, 0.5)) * 70.0)

    domain = candidate["primary_domain"].lower()
    domain_hits = 0
    if "data" in jd_lower and "data" in domain:
        domain_hits += 1
    if "backend" in jd_lower and "backend" in domain:
        domain_hits += 1
    if "mlops" in jd_lower and "mlops" in domain:
        domain_hits += 1
    domain_score = 100.0 if domain_hits > 0 else 50.0

    return round((0.30 * kd) + (0.30 * capability) + (0.15 * token_score) + (0.15 * experience) + (0.10 * domain_score), 2)


def make_candidate(index: int) -> Dict:
    archetype_population = [
        ("python_data_case", 10),
        ("python_dsa", 10),
        ("python_backend", 12),
        ("python_mlops", 10),
        ("python_automation", 8),
        ("python_generalist", 20),
    ]
    weighted = []
    for name, weight in archetype_population:
        weighted.extend([name] * weight)
    archetype_name = random.choice(weighted)
    base = ARCHETYPES[archetype_name]

    years = round(random.uniform(1.5, 9.5), 1)
    extra_skill_pool = [
        "Kafka", "Spark", "Azure", "GCP", "Terraform", "Snowflake", "Power BI", "Flask", "LangChain"
    ]
    extras = random.sample(extra_skill_pool, k=random.randint(1, 3))

    core = list(base["core"])
    random.shuffle(core)
    core = core[: random.randint(5, min(8, len(core)))]

    secondary = list(base["secondary"]) + extras
    random.shuffle(secondary)
    secondary = secondary[: random.randint(4, min(8, len(secondary)))]

    strengths = list(base["strengths"])
    random.shuffle(strengths)

    return {
        "anonymized_id": f"SYN_{index:03d}",
        "archetype": archetype_name,
        "years_experience": years,
        "core_technical_skills": core,
        "secondary_technical_skills": secondary,
        "key_strengths": strengths,
        "primary_domain": base["domain"],
        "cleaned_narrative": base["narrative"],
        "verdict_reason": strengths[0]
    }


def rank_candidates(candidates: List[Dict], jd_text: str, scorer) -> List[Tuple[str, float, str]]:
    scored = []
    for candidate in candidates:
        score = scorer(candidate, jd_text)
        scored.append((candidate["anonymized_id"], score, candidate["archetype"]))
    scored.sort(key=lambda row: row[1], reverse=True)
    return scored


def run_head_to_head_checks() -> Dict:
    """Run deterministic checks for capability-sensitive ranking behavior."""
    data_scientist_jd = (
        "Need Python Data Scientist with strong case study solving, hypothesis testing, A/B testing, "
        "statistics, pandas, SQL, and business problem solving. 3+ years required."
    )

    case_candidate = {
        "anonymized_id": "H2H_CASE",
        "archetype": "python_data_case",
        "years_experience": 4.0,
        "core_technical_skills": ["Python", "Pandas", "SQL", "Statistics"],
        "secondary_technical_skills": ["A/B Testing", "Hypothesis Testing"],
        "key_strengths": [
            "Strong case study solving and business problem framing",
            "Designs experiments and validates hypotheses"
        ],
        "primary_domain": "Data Science",
        "cleaned_narrative": "Built analytics solutions with measurable business impact.",
        "verdict_reason": "Strong case study solving and business problem framing"
    }

    dsa_candidate = {
        "anonymized_id": "H2H_DSA",
        "archetype": "python_dsa",
        "years_experience": 4.0,
        "core_technical_skills": [
            "Python", "SQL", "Pandas", "Algorithms", "Data Structures", "Problem Solving"
        ],
        "secondary_technical_skills": ["Competitive Programming", "LeetCode", "Machine Learning Basics"],
        "key_strengths": [
            "Very strong DSA and algorithmic optimization",
            "Fast at coding interviews"
        ],
        "primary_domain": "Software Engineering",
        "cleaned_narrative": "Focused on algorithm-heavy coding and optimization tasks.",
        "verdict_reason": "Very strong DSA and algorithmic optimization"
    }

    keyword_case = keyword_score(case_candidate, data_scientist_jd)
    keyword_dsa = keyword_score(dsa_candidate, data_scientist_jd)
    intelligent_case = intelligent_score(case_candidate, data_scientist_jd)
    intelligent_dsa = intelligent_score(dsa_candidate, data_scientist_jd)

    return {
        "jd": "Python Data Scientist",
        "keyword": {
            "case_candidate": keyword_case,
            "dsa_candidate": keyword_dsa,
            "preferred": "case_candidate" if keyword_case >= keyword_dsa else "dsa_candidate"
        },
        "intelligent": {
            "case_candidate": intelligent_case,
            "dsa_candidate": intelligent_dsa,
            "preferred": "case_candidate" if intelligent_case >= intelligent_dsa else "dsa_candidate"
        }
    }


def precision_at_k(ranked_rows: List[Tuple[str, float, str]], relevant: set, k: int = 10) -> float:
    top = ranked_rows[:k]
    if not top:
        return 0.0
    hits = sum(1 for _, _, archetype in top if archetype in relevant)
    return round(hits / len(top), 3)


def ideal_in_top_k(ranked_rows: List[Tuple[str, float, str]], ideal: str, k: int = 3) -> int:
    """Return 1 if ideal archetype appears in top-k, else 0."""
    top = ranked_rows[:k]
    return 1 if any(archetype == ideal for _, _, archetype in top) else 0


def main() -> None:
    random.seed(42)

    out_dir = Path("test_results/synthetic_cvs")
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates = [make_candidate(i + 1) for i in range(60)]

    for candidate in candidates:
        out_file = out_dir / f"{candidate['anonymized_id']}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(candidate, f, indent=2)

    report = {
        "total_candidates": len(candidates),
        "jds": []
    }

    for jd in JDS:
        keyword_ranked = rank_candidates(candidates, jd["text"], keyword_score)
        intelligent_ranked = rank_candidates(candidates, jd["text"], intelligent_score)

        k_prec_5 = precision_at_k(keyword_ranked, jd["relevant"], k=5)
        i_prec_5 = precision_at_k(intelligent_ranked, jd["relevant"], k=5)
        k_prec_10 = precision_at_k(keyword_ranked, jd["relevant"], k=10)
        i_prec_10 = precision_at_k(intelligent_ranked, jd["relevant"], k=10)
        k_ideal_top3 = ideal_in_top_k(keyword_ranked, jd["ideal"], k=3)
        i_ideal_top3 = ideal_in_top_k(intelligent_ranked, jd["ideal"], k=3)

        keyword_top = keyword_ranked[:10]
        intelligent_top = intelligent_ranked[:10]

        report["jds"].append(
            {
                "name": jd["name"],
                "ideal_archetype": jd["ideal"],
                "precision": {
                    "p_at_5_keyword": k_prec_5,
                    "p_at_5_intelligent": i_prec_5,
                    "p_at_5_delta": round(i_prec_5 - k_prec_5, 3),
                    "p_at_10_keyword": k_prec_10,
                    "p_at_10_intelligent": i_prec_10,
                    "p_at_10_delta": round(i_prec_10 - k_prec_10, 3),
                    "ideal_in_top3_keyword": k_ideal_top3,
                    "ideal_in_top3_intelligent": i_ideal_top3
                },
                "top10_keyword": [
                    {"candidate_id": cid, "score": score, "archetype": arc}
                    for cid, score, arc in keyword_top
                ],
                "top10_intelligent": [
                    {"candidate_id": cid, "score": score, "archetype": arc}
                    for cid, score, arc in intelligent_top
                ]
            }
        )

    report_file = Path("test_results/synthetic_benchmark_report.json")
    report["head_to_head"] = run_head_to_head_checks()

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("Generated synthetic candidates:", len(candidates))
    print("Profiles folder:", out_dir)
    print("Benchmark report:", report_file)

    for jd_result in report["jds"]:
        p = jd_result["precision"]
        print(
            f"{jd_result['name']}: "
            f"P@5 keyword={p['p_at_5_keyword']} intelligent={p['p_at_5_intelligent']} delta={p['p_at_5_delta']} | "
            f"Ideal-in-Top3 keyword={p['ideal_in_top3_keyword']} intelligent={p['ideal_in_top3_intelligent']}"
        )

    h2h = report["head_to_head"]
    print("Head-to-head (Data Scientist JD):")
    print(
        "  Keyword -> "
        f"case={h2h['keyword']['case_candidate']} dsa={h2h['keyword']['dsa_candidate']} "
        f"preferred={h2h['keyword']['preferred']}"
    )
    print(
        "  Intelligent -> "
        f"case={h2h['intelligent']['case_candidate']} dsa={h2h['intelligent']['dsa_candidate']} "
        f"preferred={h2h['intelligent']['preferred']}"
    )


if __name__ == "__main__":
    main()
