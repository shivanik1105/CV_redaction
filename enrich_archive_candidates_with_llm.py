"""Enrich archive-ingested sample CVs with LLM extraction + embeddings.

This targets the placeholder rows created by ingesting files under archive/samples/**,
identified by:
- llm_provider == 'none'
- best_knowledge_summary LIKE 'Source:%'

It upgrades those rows by:
- Running extraction-only LLM analysis on the already-redacted cleaned_text
- Storing extracted intelligence back into Supabase (same anonymized_id)
- Regenerating and storing the embedding from extracted fields

NOTE: Some CVs have extremely short/empty extracted text (often scanned PDFs / broken .doc).
Those will be skipped because they are not safe/eligible for LLM processing.
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import Dict, List, Tuple

from dotenv import load_dotenv

from cv_intelligence_extractor import CVIntelligenceExtractor
from supabase_storage import SupabaseStorage
from vector_search import VectorSearchEngine


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE_RE = re.compile(
    r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4})"
)


def _is_llm_eligible_fast(cleaned_text: str) -> bool:
    """Fast, conservative eligibility check.

    We skip CVs that are too short or appear to still contain PII (email/phone).
    The extractor also does its own strict anonymization check.
    """
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


def _fetch_archive_placeholder_rows(storage: SupabaseStorage, limit: int) -> List[Dict]:
    resp = (
        storage.client.table("cv_intelligence")
        .select("anonymized_id,cleaned_text", count="exact")
        .eq("llm_provider", "archive_ingest")
        .eq("llm_model", "none")
        .limit(limit)
        .execute()
    )
    return resp.data or []


def _enrich_one(
    extractor: CVIntelligenceExtractor,
    engine: VectorSearchEngine,
    storage: SupabaseStorage,
    anonymized_id: str,
    cleaned_text: str,
    best_knowledge_summary: str,
    dry_run: bool,
) -> Tuple[bool, str]:
    if not _is_llm_eligible_fast(cleaned_text):
        return False, "SKIP_NOT_ELIGIBLE"

    # Build a prompt that is explicitly tied to the existing anonymized_id.
    prompt = extractor._create_extraction_prompt(  # noqa: SLF001 (intentional internal call)
        cleaned_text,
        job_description=None,
        anonymized_id=anonymized_id,
    )

    if dry_run:
        return True, "DRY_RUN"

    raw = extractor.llm_processor.generate_analysis(prompt)
    intelligence = extractor._parse_prose_response(raw, anonymized_id)  # noqa: SLF001

    # Force stable ID + preserve source marker.
    intelligence["anonymized_id"] = anonymized_id
    intelligence["llm_provider"] = extractor.api_provider
    intelligence["llm_model"] = extractor.model
    intelligence["best_knowledge_summary"] = best_knowledge_summary or intelligence.get("best_knowledge_summary")

    # Keep the redacted text as cleaned_text (safe for storage/search).
    intelligence.setdefault("cleaned_text", cleaned_text)

    storage.store_intelligence(intelligence)

    embedding_text = engine.build_embedding_text(intelligence)
    embedding = engine.generate_embedding(embedding_text)
    storage.store_embedding(anonymized_id, embedding)

    return True, "ENRICHED"


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="LLM-enrich archive-ingested sample CV rows in Supabase")
    parser.add_argument("--limit", type=int, default=1000, help="Max rows to process (default: 1000)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen, don\'t call LLM or write")
    args = parser.parse_args(argv)

    load_dotenv()

    storage = SupabaseStorage()
    extractor = CVIntelligenceExtractor()
    engine = VectorSearchEngine(embedding_provider="local")

    rows = _fetch_archive_placeholder_rows(storage, limit=args.limit)

    total = len(rows)
    enriched = 0
    skipped = 0
    failed = 0

    for idx, row in enumerate(rows, start=1):
        anonymized_id = row.get("anonymized_id") or ""
        cleaned_text = row.get("cleaned_text") or ""
        best_knowledge_summary = row.get("best_knowledge_summary") or ""

        try:
            ok, status = _enrich_one(
                extractor,
                engine,
                storage,
                anonymized_id=anonymized_id,
                cleaned_text=cleaned_text,
                best_knowledge_summary=best_knowledge_summary,
                dry_run=args.dry_run,
            )

            if status in {"ENRICHED", "DRY_RUN"}:
                enriched += 1
            elif status.startswith("SKIP"):
                skipped += 1
            else:
                failed += 1

            print(f"[{idx}/{total}] {anonymized_id}: {status}")

        except Exception as e:
            failed += 1
            print(f"[{idx}/{total}] {anonymized_id}: ERROR: {e}")

    print("\nSummary")
    print("- total:", total)
    print("- enriched_or_dryrun:", enriched)
    print("- skipped:", skipped)
    print("- failed:", failed)

    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
