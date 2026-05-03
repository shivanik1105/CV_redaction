"""Debug why certain JDs yield 0 matches under production gating.

Prints the top candidates by semantic score for a given JD, plus their critical
coverage and focus overlap signals.

Usage:
  python debug_jd_matches.py "13. Mobile Developer"
  python debug_jd_matches.py "10. Technical Recruiter"
"""

import os
import sys

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase_storage import SupabaseStorage
from vector_search import get_vector_search_engine
from app import (
    compute_semantic_candidate_match,
    _candidate_has_searchable_signal,
    _extract_focus_hit_counts,
    _ROLE_FOCUS_KEYS,
)

from test_15_real_jds_fixed import JDS


def main() -> int:
    if len(sys.argv) < 2:
        print("Provide JD name (exact key from JDS)")
        print("Available keys:")
        for k in JDS.keys():
            print(f"  {k}")
        return 2

    jd_name = sys.argv[1]
    jd_text = JDS.get(jd_name)
    if not jd_text:
        print(f"Unknown JD key: {jd_name}")
        return 2

    storage = SupabaseStorage()
    engine = get_vector_search_engine()

    candidates = storage.client.table("cv_intelligence").select("*").limit(5000).execute().data or []

    jd_focus = set(_extract_focus_hit_counts(jd_text).keys()).intersection(_ROLE_FOCUS_KEYS)
    print(f"JD: {jd_name}")
    print(f"JD focus keys: {sorted(jd_focus)}")

    jd_embedding = engine.generate_embedding(jd_text)

    scored = []
    for intel in candidates:
        if 'error' in intel and not intel.get('verdict'):
            continue
        if not _candidate_has_searchable_signal(intel):
            continue

        ranked = compute_semantic_candidate_match(
            candidate=intel,
            jd_embedding=jd_embedding,
            job_description=jd_text,
        )

        scored.append(
            {
                "id": intel.get("anonymized_id"),
                "semantic": ranked.get("semantic_score"),
                "match": ranked.get("match_percentage"),
                "crit_req": ranked.get("critical_skills_required") or [],
                "crit_cov": ranked.get("critical_skill_coverage"),
                "crit_min": ranked.get("critical_skill_min_required"),
                "primary_domain": intel.get("primary_domain"),
            }
        )

    scored.sort(key=lambda x: (x["semantic"] or 0.0), reverse=True)

    print("\nTop 15 by semantic_score (no gating applied):")
    for row in scored[:15]:
        print(
            f"  {row['id']}  sem={row['semantic']:.2f}  match={row['match']:.2f}  "
            f"crit={row['crit_cov']} (min={row['crit_min']}) req={row['crit_req']}  domain={row['primary_domain']}"
        )

    # Now show how many survive production gating
    survivors = []
    for row in scored:
        if (row["match"] or 0.0) < 50.0:
            continue
        req = row["crit_req"]
        if req:
            cov = row["crit_cov"]
            if cov is None:
                continue
            if float(cov) < float(row["crit_min"] or 0.0):
                continue
        survivors.append(row)

    print(f"\nSurvivors under production gating: {len(survivors)}")
    if survivors:
        print("Top 10 survivors:")
        for row in survivors[:10]:
            print(
                f"  {row['id']}  sem={row['semantic']:.2f}  match={row['match']:.2f}  "
                f"crit={row['crit_cov']} (min={row['crit_min']}) req={row['crit_req']}  domain={row['primary_domain']}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
