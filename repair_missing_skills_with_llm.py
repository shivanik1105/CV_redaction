"""Repair missing skills in Supabase by re-running extraction on cleaned_text.

Use case
--------
Some rows have `llm_provider != 'none'` but still ended up with empty skill
arrays and empty `key_skills` (typically due to older parsing drift or partial
LLM responses). This script re-runs *extraction-only* analysis on the already
redacted `cleaned_text` and stores the repaired intelligence back into Supabase.

Privacy
-------
- Uses `cleaned_text` only (already redacted).
- The extractor also enforces anonymization checks.

Safety
------
- Dry-run by default (no LLM calls, no DB writes).
- Writes only with `--apply`.

Usage
-----
  # Dry-run preview
  python repair_missing_skills_with_llm.py --dry-run --limit 50

  # Apply for non-placeholder rows that have no skills
  python repair_missing_skills_with_llm.py --apply --scope non_placeholders --limit 200

  # Apply for placeholders too (equivalent to/encompasses enrich_archive_candidates_with_llm.py)
  python repair_missing_skills_with_llm.py --apply --scope all --limit 500
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from cv_intelligence_extractor import CVIntelligenceExtractor
from supabase_storage import SupabaseStorage
from vector_search import VectorSearchEngine


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4})")


def _as_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _is_llm_eligible_fast(cleaned_text: str) -> bool:
    if not cleaned_text:
        return False

    text = cleaned_text.strip()
    if "[REDACTED_" in text:
        return True

    if len(text) < 100:
        return False

    if _EMAIL_RE.search(text):
        return False

    m = _PHONE_RE.search(text)
    if m:
        digits = re.sub(r"\D", "", m.group(0) or "")
        if len(digits) >= 10:
            return False

    return True


def _fetch_candidate_ids(storage: SupabaseStorage, limit: int, scope: str) -> List[Dict]:
    # Avoid selecting cleaned_text in bulk; fetch it per-row to avoid JSON generation
    # errors for any single bad record.
    query = storage.client.table("cv_intelligence").select(
        "anonymized_id,llm_provider,key_skills,core_technical_skills,secondary_technical_skills,created_at",
        count="exact",
    )

    if scope == "placeholders":
        query = query.eq("llm_provider", "none")
    elif scope == "non_placeholders":
        query = query.neq("llm_provider", "none")

    resp = query.order("created_at", desc=False).limit(limit).execute()
    return resp.data or []


def _fetch_cleaned_text(storage: SupabaseStorage, anonymized_id: str) -> str:
    resp = (
        storage.client.table("cv_intelligence")
        .select("cleaned_text")
        .eq("anonymized_id", anonymized_id)
        .limit(1)
        .execute()
    )
    return (resp.data or [{}])[0].get("cleaned_text") or ""


def _needs_repair(row: Dict) -> bool:
    key_skills = _as_list(row.get("key_skills"))
    core = _as_list(row.get("core_technical_skills"))
    secondary = _as_list(row.get("secondary_technical_skills"))
    return not key_skills and not (core or secondary)


def _repair_one(
    storage: SupabaseStorage,
    extractor: CVIntelligenceExtractor,
    engine: Optional[VectorSearchEngine],
    anonymized_id: str,
    cleaned_text: str,
    dry_run: bool,
    skip_embedding: bool,
) -> Tuple[bool, str]:
    if not _is_llm_eligible_fast(cleaned_text):
        return False, "SKIP_NOT_ELIGIBLE"

    prompt = extractor._create_extraction_prompt(  # noqa: SLF001
        cleaned_text,
        job_description=None,
        anonymized_id=anonymized_id,
    )

    if dry_run:
        return True, "DRY_RUN"

    raw = extractor.llm_processor.generate_analysis(prompt)
    intelligence = extractor._parse_prose_response(raw, anonymized_id)  # noqa: SLF001

    intelligence["anonymized_id"] = anonymized_id
    intelligence["llm_provider"] = extractor.api_provider
    intelligence["llm_model"] = extractor.model
    intelligence.setdefault("cleaned_text", cleaned_text)

    storage.store_intelligence(intelligence)

    if not skip_embedding and engine is not None:
        embedding_text = engine.build_embedding_text(intelligence)
        embedding = engine.generate_embedding(embedding_text)
        storage.store_embedding(anonymized_id, embedding)

    return True, "REPAIRED"


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Repair missing skills by re-extracting from cleaned_text")
    parser.add_argument("--apply", action="store_true", help="Call LLM + write updates")
    parser.add_argument("--dry-run", action="store_true", help="Do not call LLM or write updates")
    parser.add_argument("--limit", type=int, default=200, help="Max rows to consider (default: 200)")
    parser.add_argument(
        "--scope",
        choices=["placeholders", "non_placeholders", "all"],
        default="non_placeholders",
        help="Which rows to consider",
    )
    parser.add_argument("--skip-embedding", action="store_true", help="Do not regenerate embeddings")
    args = parser.parse_args(argv)

    load_dotenv()

    do_write = bool(args.apply) and not bool(args.dry_run)

    storage = SupabaseStorage()
    extractor = CVIntelligenceExtractor()
    engine = None if args.skip_embedding else VectorSearchEngine(embedding_provider="local")

    candidates = _fetch_candidate_ids(storage, limit=args.limit, scope=args.scope)

    total = len(candidates)
    considered = 0
    repaired = 0
    skipped = 0
    failed = 0

    for idx, row in enumerate(candidates, start=1):
        anonymized_id = row.get("anonymized_id") or ""
        if not anonymized_id:
            continue

        if not _needs_repair(row):
            continue

        considered += 1

        try:
            cleaned_text = _fetch_cleaned_text(storage, anonymized_id)
            ok, status = _repair_one(
                storage,
                extractor,
                engine,
                anonymized_id=anonymized_id,
                cleaned_text=cleaned_text,
                dry_run=not do_write,
                skip_embedding=args.skip_embedding,
            )

            if status in {"REPAIRED", "DRY_RUN"}:
                repaired += 1
            elif status.startswith("SKIP"):
                skipped += 1
            else:
                failed += 1

            print(f"[{idx}/{total}] {anonymized_id}: {status}")

        except Exception as e:
            failed += 1
            print(f"[{idx}/{total}] {anonymized_id}: ERROR: {e}")

    mode = "APPLY" if do_write else "DRY_RUN"
    print("\nSummary (repair_missing_skills_with_llm)")
    print("- mode:", mode)
    print("- total_candidates_fetched:", total)
    print("- considered_missing_skills:", considered)
    print("- repaired_or_dryrun:", repaired)
    print("- skipped:", skipped)
    print("- failed:", failed)

    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
