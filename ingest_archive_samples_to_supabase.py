"""Bulk ingest every CV under archive/samples into Supabase.

Goal: ensure *every* file becomes a row in `cv_intelligence`, even if:
- the CV is very short
- extraction fails (scanned/binary .doc)
- LLM is unavailable / quota is exhausted

This script stores a minimal BACKUP record with redacted text, plus a safe
filename mapping. It attempts to generate and store embeddings (best-effort).

Required env vars:
- SUPABASE_URL
- SUPABASE_KEY

Optional env vars:
- EMBEDDING_PROVIDER=local|openai

Usage:
  python ingest_archive_samples_to_supabase.py --dry-run
  python ingest_archive_samples_to_supabase.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv

from supabase_storage import (
    SupabaseStorage,
    _extract_years_from_text,
    _extract_skills_from_text,
    _infer_domain,
    _infer_role_types,
    _infer_seniority,
    _extract_certifications,
    _compute_cv_hash,
)
from universal_pipeline_engine import PipelineOrchestrator, UniversalRedactionEngine
from vector_search import get_vector_search_engine


ALLOWED_EXTS = {".pdf", ".docx", ".doc", ".txt"}


@dataclass(frozen=True)
class IngestResult:
    rel_path: str
    anonymized_id: Optional[str]
    status: str  # success|skipped|error
    error: Optional[str] = None
    stored_embedding: bool = False


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _sanitize_text_for_storage(text: str) -> str:
    """Postgres text columns cannot contain NUL (\x00)."""
    if not text:
        return ""
    # Remove NULs and normalize line endings.
    return text.replace("\x00", "").replace("\r\n", "\n")


def _stable_candidate_id(redacted_text: str) -> str:
    """Deterministic anonymized id from content hash — same CV = same ID = override."""
    return f"CAND_{_compute_cv_hash(redacted_text)[:8].upper()}"


def _safe_original_filename(_: str) -> str:
    """Never store local filenames containing PII."""
    return "anonymized_cv.txt"


def _safe_anonymized_filename(rel_path: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short = hashlib.sha1(rel_path.encode("utf-8", errors="ignore")).hexdigest()[:8]
    return f"REDACTED_{stamp}_{short}.txt"


def _iter_input_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTS:
            yield path


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
            return redacted.strip()

        # PDFs / DOCX / DOC
        redacted, _profile = orchestrator.process_cv(str(file_path))
        return (redacted or "").strip()
    except Exception as e:
        # Hard guarantee: never fail ingestion due to extraction/redaction errors.
        # Store a safe placeholder so the file still lands in Supabase.
        return (
            "[ERROR: Text extraction/redaction failed. "
            f"FileType={suffix}. Reason={type(e).__name__}: {e}]"
        )


def _build_minimal_intelligence(
    anonymized_id: str,
    redacted_text: str,
    rel_path: str,
) -> dict:
    now_iso = datetime.now().isoformat()

    redacted_text = _sanitize_text_for_storage(redacted_text)
    if not redacted_text.strip():
        redacted_text = "[ERROR: Empty text after extraction/redaction]"

    # Rule-based extraction from redacted text (no LLM)
    years = _extract_years_from_text(redacted_text)
    skills = _extract_skills_from_text(redacted_text)
    domain = _infer_domain(skills, redacted_text)
    roles = _infer_role_types(redacted_text)
    certs = _extract_certifications(redacted_text)
    seniority = _infer_seniority(years, redacted_text)

    # Build narrative from extracted data (not raw CV dump)
    parts = []
    if seniority and seniority != "NOT_SPECIFIED":
        parts.append(f"{seniority.title()} professional")
    if years > 0:
        parts.append(f"with {years} years of experience")
    if domain:
        parts.append(f"in {domain}")
    if skills:
        parts.append(f". Skills: {', '.join(skills[:8])}.")
    cleaned_narrative = " ".join(parts) if parts else "Profile ingested from archive; rule-based extraction applied."
    cleaned_narrative = cleaned_narrative[:400]

    # Truncate cleaned_text
    cleaned_text_truncated = redacted_text[:4000] if len(redacted_text) > 4000 else redacted_text

    # Compute confidence from extraction completeness
    conf = 0
    if years > 0:
        conf += 20
    if domain:
        conf += 15
    if skills:
        conf += min(40, len(skills) * 3)
    if certs:
        conf += 10
    if roles:
        conf += 10
    conf = max(1, min(100, conf))

    return {
        "anonymized_id": anonymized_id,
        "original_cv_hash": _compute_cv_hash(redacted_text),
        "llm_prompt_used": "archive_ingest:rule_based",
        "llm_raw_response": json.dumps({"source": rel_path, "method": "rule_based_archive_ingest"}),
        "confidence_score": conf,
        "evidence_based_reasoning": f"Archive ingest via rule-based extraction. Source: {rel_path}",
        "overall_summary": cleaned_narrative,
        "key_skills": skills[:25],
        "years_experience": years,
        "career_level": seniority,
        "seniority_level": seniority,
        "years_experience_range": f"{int(years)}-{int(years)+1}" if years > 0 else "",
        "domain_expertise": ([domain] if domain else []),
        "primary_domain": domain,
        "secondary_domains": [],
        "cleaned_narrative": cleaned_narrative,
        "cleaned_text": cleaned_text_truncated,
        "core_technical_skills": skills[:20],
        "secondary_technical_skills": [],
        "frameworks_tools": [],
        "soft_skills": [],
        "certifications": certs,
        "education_level": "",
        "field_of_study": "",
        "highest_degree": "",
        "extraction_timestamp": now_iso,
        "llm_model": "none",
        "llm_provider": "archive_ingest",
        "matched_requirements": [],
        "missing_requirements": [],
        "potential_concerns": [],
        "key_strengths": [],
        "leadership_indicators": [],
        "highlight_achievements": [],
        "role_types": roles,
        "search_keywords": ", ".join(skills[:15]) if skills else "",
        "org_id": "default_org",
    }


def main() -> int:
    # Load env vars from .env early (Supabase creds, embedding provider, etc.)
    load_dotenv()

    parser = argparse.ArgumentParser(description="Ingest archive/samples into Supabase")
    parser.add_argument(
        "--root",
        default=str(Path("archive") / "samples"),
        help="Root folder to scan (default: archive/samples)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write to Supabase; just show what would happen",
    )
    parser.add_argument(
        "--skip-embedding",
        action="store_true",
        help="Skip embedding generation/storage",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit of files to process (0 = no limit)",
    )
    args = parser.parse_args()

    # Keep stdout readable (the CV pipelines + httpx can be very noisy).
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("universal_pipeline_engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("supabase_storage").setLevel(logging.INFO)

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Root folder not found: {root}")

    if not args.dry_run:
        # Ensure env is set early, before doing expensive extraction.
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
            raise SystemExit("Missing SUPABASE_URL/SUPABASE_KEY env vars")

    storage = None if args.dry_run else SupabaseStorage()

    orchestrator = PipelineOrchestrator(debug=False, config_dir="config")
    text_redactor = UniversalRedactionEngine(config_dir="config", debug=False)

    vector_engine = None
    if not args.skip_embedding:
        try:
            vector_engine = get_vector_search_engine()
        except Exception:
            vector_engine = None

    results: list[IngestResult] = []

    files = list(_iter_input_files(root))
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    print(f"Found {len(files)} files under {root}.")

    for file_path in files:
        rel_path = str(file_path.relative_to(root)).replace("\\", "/")
        try:
            redacted_text = _extract_and_redact_text(file_path, orchestrator, text_redactor)
            redacted_text = _sanitize_text_for_storage(redacted_text)
            anonymized_id = _stable_candidate_id(redacted_text)
            safe_original = _safe_original_filename(file_path.name)
            safe_anonymized = _safe_anonymized_filename(rel_path)

            intelligence = _build_minimal_intelligence(anonymized_id, redacted_text, rel_path)

            stored_embedding = False

            if args.dry_run:
                results.append(
                    IngestResult(
                        rel_path=rel_path,
                        anonymized_id=anonymized_id,
                        status="skipped",
                        error="dry-run",
                        stored_embedding=False,
                    )
                )
                continue

            # 1) Store intelligence row (upsert)
            try:
                storage.store_intelligence(intelligence)
            except Exception as store_error:
                # Hard guarantee: still store a placeholder record even if the extracted
                # text has encoding issues or contains problematic sequences.
                fallback = dict(intelligence)
                fallback["cleaned_text"] = "[CONTENT_SKIPPED_DUE_TO_STORAGE_ERROR]"
                fallback["cleaned_narrative"] = "Ingested; content omitted due to storage encoding issue."
                fallback["verdict_reason"] = (
                    "Ingested from archive/samples; content sanitized due to storage error: "
                    f"{type(store_error).__name__}"
                )
                storage.store_intelligence(fallback)

            # 2) Store filename mapping (PII-safe)
            storage.store_filename_mapping(
                anonymized_id=anonymized_id,
                original_filename=safe_original,
                anonymized_filename=safe_anonymized,
            )

            # 3) Best-effort embedding
            if vector_engine is not None:
                try:
                    embedding = vector_engine.generate_embedding(redacted_text)
                    if embedding:
                        stored_embedding = storage.store_embedding(anonymized_id, embedding)
                except Exception:
                    stored_embedding = False

            results.append(
                IngestResult(
                    rel_path=rel_path,
                    anonymized_id=anonymized_id,
                    status="success",
                    error=None,
                    stored_embedding=stored_embedding,
                )
            )

        except Exception as e:
            results.append(
                IngestResult(
                    rel_path=rel_path,
                    anonymized_id=None,
                    status="error",
                    error=str(e),
                    stored_embedding=False,
                )
            )

    success = sum(1 for r in results if r.status == "success")
    errors = [r for r in results if r.status == "error"]
    embeds = sum(1 for r in results if r.stored_embedding)

    print("\nSummary")
    print(f"- success: {success}")
    print(f"- errors:  {len(errors)}")
    print(f"- embedding stored: {embeds}")

    if errors:
        print("\nErrors (first 20)")
        for r in errors[:20]:
            print(f"- {r.rel_path}: {r.error}")

    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
