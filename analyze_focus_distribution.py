"""Analyze which role-focus signals actually exist in the candidate dataset.

This helps interpret 0-match outcomes: if there are no candidates with strong
signals for a focus key, returning 0 is correct (avoid random matches).
"""

import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

from collections import Counter

from supabase_storage import SupabaseStorage
from app import (
    _extract_focus_hit_counts,
    _FOCUS_MIN_DISTINCT_PHRASE_HITS,
    _ROLE_FOCUS_KEYS,
)


def main() -> int:
    storage = SupabaseStorage()
    resp = storage.client.table("cv_intelligence").select(
        "anonymized_id, primary_domain, secondary_domains, domain_expertise, core_technical_skills, secondary_technical_skills, frameworks_tools, cleaned_narrative, overall_summary, best_knowledge_summary, evidence_based_reasoning, key_strengths"
    ).limit(1000).execute()

    candidates = resp.data or []
    print(f"Candidates fetched: {len(candidates)}")

    role_key_counts_any = Counter()
    role_key_counts_strong = Counter()

    for intel in candidates:
        skills = (
            (intel.get("core_technical_skills") or [])
            + (intel.get("secondary_technical_skills") or [])
            + (intel.get("frameworks_tools") or [])
        )
        all_skill_blob = " ".join(str(s).lower() for s in skills if str(s).strip())

        candidate_focus_text = " ".join(
            [
                str(intel.get("primary_domain") or ""),
                " ".join(str(d) for d in (intel.get("secondary_domains") or []) if str(d).strip()),
                " ".join(str(d) for d in (intel.get("domain_expertise") or []) if str(d).strip()),
                all_skill_blob,
                str(intel.get("cleaned_narrative") or ""),
                str(intel.get("overall_summary") or ""),
                str(intel.get("best_knowledge_summary") or ""),
                str(intel.get("evidence_based_reasoning") or ""),
                " ".join(str(s) for s in (intel.get("key_strengths") or []) if str(s).strip()),
            ]
        )

        counts = _extract_focus_hit_counts(candidate_focus_text)
        role_keys = set(counts.keys()).intersection(_ROLE_FOCUS_KEYS)
        for k in role_keys:
            role_key_counts_any[k] += 1

        role_keys_strong = {
            k
            for k in role_keys
            if counts.get(k, 0) >= _FOCUS_MIN_DISTINCT_PHRASE_HITS.get(k, 1)
        }
        for k in role_keys_strong:
            role_key_counts_strong[k] += 1

    print("\nRole focus presence (any hit):")
    for key, count in role_key_counts_any.most_common():
        print(f"  {key:16s}  {count:4d}")

    print("\nRole focus presence (strong hit threshold applied):")
    for key, count in role_key_counts_strong.most_common():
        min_hits = _FOCUS_MIN_DISTINCT_PHRASE_HITS.get(key, 1)
        print(f"  {key:16s}  {count:4d}   (min_distinct_phrase_hits={min_hits})")

    print("\nConfigured min distinct phrase hits (only keys != 1 shown):")
    for k, v in sorted(_FOCUS_MIN_DISTINCT_PHRASE_HITS.items()):
        if v != 1:
            print(f"  {k}: {v}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
