#!/usr/bin/env python3
"""
Clean and repair cv_intelligence records in Supabase.

What this script does:
1. Scans all rows in cv_intelligence.
2. Repairs missing required fields using llm_raw_response backup data where possible.
3. Re-upserts normalized records through SupabaseStorage.store_intelligence.
4. Optionally deletes irrecoverable empty rows.

Usage examples:
  python clean_supabase_data.py --dry-run
  python clean_supabase_data.py --apply
  python clean_supabase_data.py --apply --delete-empty
"""

import argparse
import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

from supabase_storage import SupabaseStorage


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def has_search_signal(candidate: Dict[str, Any]) -> bool:
    """Determine whether candidate has enough data to be searchable."""
    skills = (
        candidate.get("core_technical_skills")
        or candidate.get("secondary_technical_skills")
        or candidate.get("key_skills")
        or []
    )
    domain = (candidate.get("primary_domain") or "").strip()
    summary = (
        candidate.get("cleaned_narrative")
        or candidate.get("overall_summary")
        or candidate.get("cleaned_text")
        or ""
    ).strip()
    years = candidate.get("years_experience")
    if years is None:
        years = candidate.get("years_of_experience")

    return bool(skills or domain or summary or (isinstance(years, (int, float)) and years > 0))


def repair_candidate(storage: SupabaseStorage, raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """Build a repaired app-format candidate from raw DB record + JSON backup."""
    repaired = storage._db_record_to_app_format(raw_record)

    anon_id = raw_record.get("anonymized_id") or repaired.get("anonymized_id")
    repaired["anonymized_id"] = anon_id

    if not repaired.get("core_technical_skills"):
        repaired["core_technical_skills"] = raw_record.get("key_skills") or []

    if not repaired.get("primary_domain"):
        domains = raw_record.get("domain_expertise") or []
        if domains:
            repaired["primary_domain"] = str(domains[0])
            repaired["secondary_domains"] = [str(d) for d in domains[1:]]

    if not repaired.get("cleaned_narrative"):
        repaired["cleaned_narrative"] = raw_record.get("overall_summary") or ""

    if repaired.get("years_experience") is None:
        repaired["years_experience"] = raw_record.get("years_of_experience") or 0

    if repaired.get("confidence_score") is None:
        repaired["confidence_score"] = raw_record.get("confidence_score") or 0

    if repaired.get("verdict") is None:
        repaired["verdict"] = raw_record.get("verdict") or "BACKUP"

    repaired["cleaned_text"] = repaired.get("cleaned_text") or raw_record.get("cleaned_text") or repaired.get("cleaned_narrative") or ""

    return repaired


def scan_records(storage: SupabaseStorage, page_size: int = 500) -> List[Dict[str, Any]]:
    """Fetch all records from Supabase in pages."""
    all_rows: List[Dict[str, Any]] = []
    start = 0

    while True:
        end = start + page_size - 1
        response = storage.client.table(storage.table_name).select("*").range(start, end).execute()
        rows = response.data or []
        all_rows.extend(rows)

        if len(rows) < page_size:
            break
        start += page_size

    return all_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean and repair Supabase candidate records")
    parser.add_argument("--dry-run", action="store_true", help="Only report what would change")
    parser.add_argument("--apply", action="store_true", help="Apply repairs to Supabase")
    parser.add_argument("--delete-empty", action="store_true", help="Delete irrecoverable empty rows (requires --apply)")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        parser.error("Choose one mode: --dry-run or --apply")

    if args.delete_empty and not args.apply:
        parser.error("--delete-empty requires --apply")

    load_dotenv(override=True)

    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        logger.error("SUPABASE_URL/SUPABASE_KEY not set")
        return 1

    storage = SupabaseStorage()
    rows = scan_records(storage)

    logger.info("Found %s rows in cv_intelligence", len(rows))

    repaired_count = 0
    skipped_valid = 0
    empty_rows = 0
    deleted_count = 0
    failed_repairs = 0

    for row in rows:
        anon_id = row.get("anonymized_id", "UNKNOWN")
        repaired = repair_candidate(storage, row)

        if has_search_signal(repaired):
            needs_repair = not has_search_signal(storage._db_record_to_app_format(row))
            if needs_repair:
                if args.apply:
                    try:
                        storage.store_intelligence(repaired)
                        repaired_count += 1
                        logger.info("Repaired: %s", anon_id)
                    except Exception as exc:
                        failed_repairs += 1
                        logger.warning("Repair failed for %s: %s", anon_id, exc)
                else:
                    repaired_count += 1
                    logger.info("Would repair: %s", anon_id)
            else:
                skipped_valid += 1
        else:
            empty_rows += 1
            if args.apply and args.delete_empty:
                try:
                    storage.client.table(storage.table_name).delete().eq("anonymized_id", anon_id).execute()
                    deleted_count += 1
                    logger.info("Deleted empty row: %s", anon_id)
                except Exception as exc:
                    logger.warning("Delete failed for %s: %s", anon_id, exc)

    logger.info("Summary:")
    logger.info("  Valid rows unchanged: %s", skipped_valid)
    logger.info("  Repaired rows: %s", repaired_count)
    logger.info("  Empty/irrecoverable rows: %s", empty_rows)
    logger.info("  Deleted rows: %s", deleted_count)
    logger.info("  Failed repairs: %s", failed_repairs)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
