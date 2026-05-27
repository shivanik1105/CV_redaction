"""Repair cv_intelligence rows whose cleaned_text is an error/empty placeholder.

Why this exists
---------------
Some historical/placeholder ingests stored `cleaned_text` as an error string like:
- "Error: PyMuPDF not available"
- "[ERROR: No text extracted ...]"

When this happens there is no usable CV text to infer skills from, so `key_skills`
remains empty.

If the row contains `best_knowledge_summary` like "Source: more/Foo.pdf", we can
re-run the local extraction+redaction pipeline against the corresponding file
under `archive/samples/` and update Supabase with real cleaned_text.

Safety
------
- Dry-run by default.
- Writes only when `--apply` is provided.

Usage
-----
  python repair_error_cleaned_text_from_archive.py --dry-run
  python repair_error_cleaned_text_from_archive.py --apply

Then run:
  python backfill_key_skills.py --infer-from-text --lexicon-fallback --apply --only-placeholders
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from supabase_storage import SupabaseStorage
from universal_pipeline_engine import PipelineOrchestrator, UniversalRedactionEngine


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _sanitize_text_for_storage(text: str) -> str:
    if not text:
        return ""
    return text.replace("\x00", "").replace("\r\n", "\n")


def _parse_archive_source_rel_path(best_knowledge_summary: Any) -> Optional[str]:
    if not best_knowledge_summary:
        return None
    text = str(best_knowledge_summary).strip()
    if not text:
        return None
    match = re.search(r"\bSource:\s*([^\r\n]+)", text)
    if not match:
        return None
    rel_path = match.group(1).strip().strip('"\'')
    if not rel_path:
        return None
    rel_path = rel_path.replace("\\", "/")
    rel_path = rel_path.lstrip("/").replace("..", "")
    return rel_path or None


def _safe_join_under(root: Path, rel_path: str) -> Optional[Path]:
    if not rel_path:
        return None
    candidate = (root / rel_path).resolve()
    try:
        root_resolved = root.resolve()
        if str(candidate).startswith(str(root_resolved)):
            return candidate
    except Exception:
        return None
    return None


def _resolve_source_file(root: Path, rel_path: str) -> Optional[Path]:
    """Resolve Source: paths under archive/samples.

    Some historical rows stored only the basename (no subfolder). In that case,
    fall back to searching the archive tree by filename.
    """
    direct = _safe_join_under(root, rel_path)
    if direct and direct.exists():
        return direct

    basename = Path(rel_path).name
    if not basename:
        return None

    # NOTE: Do not use rglob(basename) because basename can contain glob
    # metacharacters like '[' and ']' (common in these sample filenames).
    matches = [
        p
        for p in root.rglob("*")
        if p.is_file() and p.name.lower() == basename.lower()
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def _is_error_text(cleaned_text: Any) -> bool:
    compact = " ".join(str(cleaned_text or "").split())
    if not compact:
        return True
    low = compact.lower()
    return low.startswith("[error") or low.startswith("error:")


def _is_too_short(cleaned_text: Any, min_len: int) -> bool:
    if min_len <= 0:
        return False
    compact = " ".join(str(cleaned_text or "").split())
    return 0 < len(compact) < min_len


def _extract_and_redact_text(
    file_path: Path,
    orchestrator: PipelineOrchestrator,
    text_redactor: UniversalRedactionEngine,
) -> str:
    suffix = file_path.suffix.lower()

    try:
        if suffix == ".txt":
            raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
            redacted = text_redactor.redact(raw_text, file_path.name)
            return (redacted or "").strip()

        redacted, _profile = orchestrator.process_cv(str(file_path))
        return (redacted or "").strip()
    except Exception as e:
        return (
            "[ERROR: Text extraction/redaction failed. "
            f"FileType={suffix}. Reason={type(e).__name__}: {e}]"
        )


@dataclass
class RepairStats:
    scanned: int = 0
    eligible: int = 0
    repaired: int = 0
    still_error: int = 0
    missing_file: int = 0
    write_errors: int = 0


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Repair error cleaned_text from archive sources")
    parser.add_argument("--apply", action="store_true", help="Write updates to Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Alias for not using --apply")
    parser.add_argument("--limit", type=int, default=0, help="Max rows to repair (0 = no limit)")
    parser.add_argument(
        "--root",
        default=str(Path("archive") / "samples"),
        help="Archive samples root (default: archive/samples)",
    )
    parser.add_argument(
        "--min-cleaned-length",
        type=int,
        default=200,
        help="Also reprocess rows whose cleaned_text is shorter than this (0 disables)",
    )
    args = parser.parse_args()

    do_write = bool(args.apply) and not bool(args.dry_run)

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Root folder not found: {root}")

    # Keep stdout readable.
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("universal_pipeline_engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    storage = SupabaseStorage()
    client = storage.client

    orchestrator = PipelineOrchestrator(debug=False, config_dir="config")
    text_redactor = UniversalRedactionEngine(config_dir="config", debug=False)

    stats = RepairStats()

    # Pull a bounded set and filter locally; the dataset here is small.
    rows = (
        client.table("cv_intelligence")
        .select(
            "anonymized_id,cleaned_text,llm_raw_response,llm_provider,created_at,key_skills,core_technical_skills,secondary_technical_skills"
        )
        .limit(1000)
        .execute()
        .data
        or []
    )

    # Stable iteration: oldest first.
    rows.sort(key=lambda r: str(r.get("created_at") or ""))

    for row in rows:
        if args.limit and stats.repaired >= args.limit:
            break

        stats.scanned += 1

        anonymized_id = row.get("anonymized_id")
        if not anonymized_id:
            continue

        # Only fix rows that are missing all skills (otherwise we risk rewriting
        # cleaned_text for already-good candidates).
        if row.get("key_skills") or row.get("core_technical_skills") or row.get("secondary_technical_skills"):
            continue

        # Fix rows that are currently unusable or suspiciously short.
        if not (_is_error_text(row.get("cleaned_text")) or _is_too_short(row.get("cleaned_text"), args.min_cleaned_length)):
            continue

        # best_knowledge_summary may have been dropped from DB; try JSON backup
        raw_backup = row.get("llm_raw_response", "")
        bks = ""
        if raw_backup and isinstance(raw_backup, str) and raw_backup.startswith("{"):
            try:
                bks = json.loads(raw_backup).get("best_knowledge_summary", "")
            except Exception:
                pass
        rel_path = _parse_archive_source_rel_path(bks)
        if not rel_path:
            continue

        stats.eligible += 1

        file_path = _resolve_source_file(root, rel_path)
        if not file_path or not file_path.exists():
            stats.missing_file += 1
            print(f"[MISSING_FILE] {anonymized_id}: {rel_path}")
            continue

        repaired_text = _extract_and_redact_text(file_path, orchestrator, text_redactor)
        repaired_text = _sanitize_text_for_storage(repaired_text)

        if _is_error_text(repaired_text):
            stats.still_error += 1
            head = " ".join(str(repaired_text).split())[:160]
            print(f"[STILL_ERROR] {anonymized_id}: {head}")
            continue

        cleaned_narrative = " ".join(repaired_text.split())
        cleaned_narrative = cleaned_narrative[:280] if cleaned_narrative else ""

        update: Dict[str, Any] = {
            "cleaned_text": repaired_text,
            "cleaned_narrative": cleaned_narrative,
            # Keep this consistent with archive ingest behavior.
            "original_cv_hash": _sha256_hex(repaired_text),
            "extraction_timestamp": datetime.now().isoformat(),
        }

        if do_write:
            try:
                client.table("cv_intelligence").update(update).eq("anonymized_id", anonymized_id).execute()
            except Exception as e:
                stats.write_errors += 1
                print(f"[WRITE_ERROR] {anonymized_id}: {type(e).__name__}: {e}")
                continue

        stats.repaired += 1
        print(f"[REPAIRED] {anonymized_id}: {rel_path}")

    mode = "APPLY" if do_write else "DRY_RUN"
    print("Repair cleaned_text from archive:", mode)
    print("- scanned:", stats.scanned)
    print("- eligible:", stats.eligible)
    print("- repaired:", stats.repaired)
    print("- still_error:", stats.still_error)
    print("- missing_file:", stats.missing_file)
    print("- write_errors:", stats.write_errors)

    if do_write and stats.write_errors:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
