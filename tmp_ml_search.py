import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

from supabase_storage import SupabaseStorage
from vector_search import get_vector_search_engine
from app import (
    _candidate_has_searchable_signal,
    _extract_critical_jd_skills,
    compute_semantic_candidate_match,
)

JD = (
    "Looking for ML Engineer with exp in TensorFlow/PyTorch. "
    "Should work on model building, deployment, optimization. "
    "Knowledge of MLOps is bonus."
)


def main() -> int:
    print("JD:", JD)
    critical = _extract_critical_jd_skills(JD)
    print("Critical skills extracted:", critical)

    storage = SupabaseStorage()
    resp = storage.client.table("cv_intelligence").select("*").limit(300).execute()
    candidates = resp.data or []
    print("Fetched candidates:", len(candidates))

    # Quick inventory: how many candidates explicitly list TF/PT.
    tfpt_candidates = []
    for intel in candidates:
        skills = (
            (intel.get("core_technical_skills") or [])
            + (intel.get("secondary_technical_skills") or [])
            + (intel.get("frameworks_tools") or [])
        )
        blob = " ".join(str(s).lower() for s in skills if str(s).strip())
        if "tensorflow" in blob or "pytorch" in blob:
            tfpt_candidates.append(intel.get("anonymized_id"))
    print("Candidates mentioning TensorFlow/PyTorch:", len(tfpt_candidates))

    engine = get_vector_search_engine()
    jd_emb = engine.generate_embedding(JD)
    print("JD embedding dims:", len(jd_emb))

    matches: list[dict] = []
    semantic_only: list[dict] = []
    for intel in candidates:
        if "error" in intel and not intel.get("verdict"):
            continue
        if not _candidate_has_searchable_signal(intel):
            continue

        ranked = compute_semantic_candidate_match(
            candidate=intel, jd_embedding=jd_emb, job_description=JD
        )

        match_percentage = float(ranked.get("match_percentage") or 0.0)
        semantic_score = float(ranked.get("semantic_score") or 0.0)
        critical_cov = float(ranked.get("critical_skill_coverage") or 0.0)
        critical_min = float(ranked.get("critical_skill_min_required") or 0.0)
        critical_required = ranked.get("critical_skills_required") or []

        semantic_only.append(
            {
                "anonymized_id": intel.get("anonymized_id"),
                "semantic_score": semantic_score,
                "critical_skill_coverage": critical_cov,
                "years_experience": intel.get("years_experience", 0),
                "seniority_level": intel.get("seniority_level", "N/A"),
                "primary_domain": intel.get("primary_domain", ""),
                "core_skills": (intel.get("core_technical_skills") or [])[:8],
            }
        )

        # mirror /api/quick-search thresholds
        if match_percentage < 50:
            continue
        if critical_required and critical_cov < critical_min:
            continue

        matches.append(
            {
                "anonymized_id": intel.get("anonymized_id"),
                "match_percentage": match_percentage,
                "semantic_score": semantic_score,
                "critical_skill_coverage": critical_cov,
                "critical_skills_matched": ranked.get("critical_skills_matched") or [],
                "years_experience": intel.get("years_experience", 0),
                "seniority_level": intel.get("seniority_level", "N/A"),
                "primary_domain": intel.get("primary_domain", ""),
                "core_skills": (intel.get("core_technical_skills") or [])[:10],
                "selection_basis": ranked.get("selection_basis", ""),
                "best_knowledge": ranked.get("best_knowledge")
                or intel.get("best_knowledge_summary", ""),
            }
        )

    # sort like endpoint
    matches.sort(
        key=lambda x: (x["semantic_score"], x.get("years_experience", 0)), reverse=True
    )

    print("Matches (after thresholds):", len(matches))
    for i, m in enumerate(matches[:10], 1):
        print(
            f"\n{i}. {m['anonymized_id']}"
            f"  match={m['match_percentage']:.1f}%"
            f"  semantic={m['semantic_score']:.1f}%"
            f"  critical={m['critical_skill_coverage']:.0f}%"
        )
        print(
            f"   exp={m['years_experience']} ({m['seniority_level']})  domain={m['primary_domain']}"
        )
        if m["core_skills"]:
            print("   skills:", ", ".join(m["core_skills"]))
        if m["critical_skills_matched"]:
            print("   critical matched:", ", ".join(m["critical_skills_matched"]))
        if m["selection_basis"]:
            print("   why:", m["selection_basis"])
        if m["best_knowledge"]:
            print("   best:", str(m["best_knowledge"])[:220])

    # If nothing passes gating, still show what the model thinks is closest.
    if not matches and semantic_only:
        semantic_only.sort(key=lambda x: (x["semantic_score"], x.get("years_experience", 0)), reverse=True)
        print("\nTop semantic-only candidates (ignoring critical-skill gating):")
        for i, m in enumerate(semantic_only[:8], 1):
            print(
                f"{i}. {m['anonymized_id']} semantic={m['semantic_score']:.1f}% critical={m['critical_skill_coverage']:.0f}% "
                f"exp={m['years_experience']} {m['seniority_level']} domain={m['primary_domain']}"
            )
            if m["core_skills"]:
                print("   skills:", ", ".join(m["core_skills"]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
