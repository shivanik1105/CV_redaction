"""Backfill key_skills for cv_intelligence rows in Supabase.

Why this exists
---------------
`key_skills` is used as a convenient combined skill list. In this repo it is
normally computed as:

    key_skills = core_technical_skills + secondary_technical_skills

However, older rows, placeholder ingests (`llm_provider='none'`), or schema
migrations can leave `key_skills` empty even when other skill fields exist.

This script:
- Fills missing/empty `key_skills` from existing `core_technical_skills` +
  `secondary_technical_skills`.
- Optionally infers skills from `cleaned_text` when *all* skill fields are empty
  (useful for placeholder rows) via `--infer-from-text`.

Safety
------
- Dry-run by default.
- Writes only when `--apply` is provided.

Usage
-----
  python backfill_key_skills.py --dry-run
  python backfill_key_skills.py --apply

  # Only placeholder rows
  python backfill_key_skills.py --only-placeholders --apply

  # Also infer skills from cleaned_text for rows with no skill fields
  python backfill_key_skills.py --infer-from-text --apply
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from dotenv import load_dotenv

from supabase_storage import SupabaseStorage


_SKILLS_HEADERS = (
    "skills",
    "technical skills",
    "key skills",
    "technologies",
    "tools",
)

_SECTION_STOP_HEADERS = (
    "experience",
    "work experience",
    "professional experience",
    "education",
    "projects",
    "certifications",
    "summary",
    "profile summary",
)


# Conservative tech lexicon to extract skills when the CV doesn't have an explicit
# "Skills:" section. Intentionally small to reduce false positives.
_TECH_LEXICON: List[Tuple[str, re.Pattern]] = [
    ("Python", re.compile(r"\bpython\b", re.I)),
    ("Java", re.compile(r"\bjava\b", re.I)),
    ("JavaScript", re.compile(r"\bjavascript\b|\bjs\b", re.I)),
    ("TypeScript", re.compile(r"\btypescript\b|\bts\b", re.I)),
    ("C#", re.compile(r"\bc#\b|\bcsharp\b", re.I)),
    ("C++", re.compile(r"\bc\+\+\b", re.I)),
    (".NET", re.compile(r"\b\.net\b|\bdotnet\b", re.I)),
    ("React", re.compile(r"\breact\b", re.I)),
    ("Node.js", re.compile(r"\bnode\.js\b|\bnodejs\b", re.I)),
    ("Django", re.compile(r"\bdjango\b", re.I)),
    ("Flask", re.compile(r"\bflask\b", re.I)),
    ("FastAPI", re.compile(r"\bfastapi\b", re.I)),
    ("Spring", re.compile(r"\bspring\b", re.I)),
    ("SQL", re.compile(r"\bsql\b", re.I)),
    ("PostgreSQL", re.compile(r"\bpostgresql\b|\bpostgres\b", re.I)),
    ("MySQL", re.compile(r"\bmysql\b", re.I)),
    ("MongoDB", re.compile(r"\bmongodb\b", re.I)),
    ("Redis", re.compile(r"\bredis\b", re.I)),
    ("Docker", re.compile(r"\bdocker\b", re.I)),
    ("Kubernetes", re.compile(r"\bkubernetes\b|\bk8s\b", re.I)),
    ("AWS", re.compile(r"\baws\b|\bamazon web services\b", re.I)),
    ("Azure", re.compile(r"\bazure\b", re.I)),
    ("GCP", re.compile(r"\bgcp\b|\bgoogle cloud\b", re.I)),
    ("Terraform", re.compile(r"\bterraform\b", re.I)),
    ("Kafka", re.compile(r"\bkafka\b", re.I)),
    ("Airflow", re.compile(r"\bairflow\b", re.I)),
    ("Spark", re.compile(r"\bspark\b", re.I)),
    ("Git", re.compile(r"\bgit\b", re.I)),
    ("Linux", re.compile(r"\blinux\b", re.I)),
    ("REST APIs", re.compile(r"\brest\b|\brestful\b", re.I)),
    ("GraphQL", re.compile(r"\bgraphql\b", re.I)),
]


def _as_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    # Supabase sometimes returns arrays as strings depending on schema/RPC
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        return [s]
    return [str(value).strip()] if str(value).strip() else []


def _dedupe_case_insensitive(items: Iterable[str], max_items: int = 30) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        s = str(item).strip()
        if not s:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= max_items:
            break
    return out


def _infer_skills_from_text(cleaned_text: str, max_items: int = 25) -> List[str]:
    """Very conservative heuristic skill extractor.

    Intended only as a fallback when LLM extraction wasn't run.
    It tries to pull content following a SKILLS/TECHNOLOGIES header.
    """
    if not cleaned_text:
        return []

    raw = str(cleaned_text)
    if not raw.strip():
        return []

    # SupabaseStorage normalizes whitespace (collapses newlines). Handle both
    # multi-line and single-line blobs.
    raw_compact = re.sub(r"\s+", " ", raw).strip()

    # 1) Single-line pattern: "SKILLS: Python, Django, ..." optionally followed by
    # another section header.
    section_re = re.compile(
        r"\b(?:skills|technical skills|key skills|technologies|tools)\b\s*[:\-]\s*(.+?)\s*(?=\b(?:experience|work experience|professional experience|education|projects|certifications|summary|profile summary)\b|$)",
        re.I,
    )
    m = section_re.search(raw_compact)
    if m:
        blob = m.group(1)
        parts = re.split(r"[,;/|]+", blob)
        skills = []
        for p in parts:
            s = p.strip().strip("-•* ").strip()
            s = re.sub(r"\s{2,}", " ", s)
            if not s:
                continue
            if s.lower() in {"not specified", "n/a", "na", "none"}:
                continue
            if len(s.split()) > 6:
                continue
            skills.append(s)
        skills = _dedupe_case_insensitive(skills, max_items=max_items)
        if skills:
            return skills

    # 2) Multi-line fallback
    lines = [ln.strip() for ln in raw.splitlines()]
    lines = [ln for ln in lines if ln and not ln.startswith("[ERROR")]
    if not lines:
        return []

    header_idx = -1
    for i, ln in enumerate(lines):
        lower = ln.lower().strip(": ")
        if any(h == lower or lower.startswith(h + ":") for h in _SKILLS_HEADERS):
            header_idx = i
            break

    # Also accept inline forms like: "SKILLS: Python, Django, ..."
    if header_idx == -1:
        for i, ln in enumerate(lines):
            if re.match(r"^(?:skills|technical skills|key skills|technologies|tools)\s*:\s*.+$", ln, re.I):
                header_idx = i
                break

    if header_idx == -1:
        return []

    collected: List[str] = []

    # If header line itself contains ':' items, include them.
    m_inline = re.match(r"^(?:skills|technical skills|key skills|technologies|tools)\s*:\s*(.+)$", lines[header_idx], re.I)
    if m_inline:
        collected.append(m_inline.group(1))

    # Collect subsequent short lines until a stop header.
    for ln in lines[header_idx + 1 : header_idx + 40]:
        lower = ln.lower().strip(": ")
        if any(stop == lower or lower.startswith(stop) for stop in _SECTION_STOP_HEADERS):
            break
        # Too-long lines are usually descriptions, not skill lists.
        if len(ln) > 120:
            continue
        collected.append(ln)

    blob = "\n".join(collected)
    # Normalize bullets and separators
    blob = blob.replace("•", "\n").replace("·", "\n")
    parts = re.split(r"[\n,;/|]+", blob)

    # Filter and de-noise
    skills: List[str] = []
    for p in parts:
        s = p.strip().strip("-•* ").strip()
        s = re.sub(r"\s{2,}", " ", s)
        if not s:
            continue
        if s.lower() in {"not specified", "n/a", "na", "none"}:
            continue
        # Skip lines that look like full sentences.
        if len(s.split()) > 6:
            continue
        skills.append(s)

    return _dedupe_case_insensitive(skills, max_items=max_items)


def _infer_skills_from_lexicon(cleaned_text: str, max_items: int = 25) -> List[str]:
    if not cleaned_text:
        return []

    text = re.sub(r"\s+", " ", str(cleaned_text)).strip()
    if not text or text.startswith("[ERROR"):
        return []

    hits: List[str] = []
    for canonical, pattern in _TECH_LEXICON:
        if pattern.search(text):
            hits.append(canonical)
            if len(hits) >= max_items:
                break
    return _dedupe_case_insensitive(hits, max_items=max_items)


@dataclass
class BackfillStats:
    scanned: int = 0
    updated_from_existing: int = 0
    inferred_from_text: int = 0
    skipped_no_signal: int = 0
    write_errors: int = 0


def _needs_key_skills(row: Dict) -> bool:
    return not _as_list(row.get("key_skills"))


def _has_any_skills(row: Dict) -> bool:
    return bool(_as_list(row.get("core_technical_skills")) or _as_list(row.get("secondary_technical_skills")))


def _is_placeholder(row: Dict) -> bool:
    return (row.get("llm_provider") or "").lower() == "none"


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Backfill key_skills for cv_intelligence")
    parser.add_argument("--apply", action="store_true", help="Write updates to Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Alias for not using --apply")
    parser.add_argument("--limit", type=int, default=0, help="Max rows to scan (0 = no limit)")
    parser.add_argument("--page-size", type=int, default=200, help="Rows per page")
    parser.add_argument(
        "--only-placeholders",
        action="store_true",
        help="Only update placeholder rows (llm_provider='none')",
    )
    parser.add_argument(
        "--infer-from-text",
        action="store_true",
        help="If skill fields are empty, try to infer from cleaned_text",
    )
    parser.add_argument(
        "--lexicon-fallback",
        action="store_true",
        help="When inferring from cleaned_text, also try a conservative tech lexicon fallback",
    )
    args = parser.parse_args()

    do_write = bool(args.apply) and not bool(args.dry_run)

    storage = SupabaseStorage()
    client = storage.client

    stats = BackfillStats()

    start = 0
    page_size = max(50, min(int(args.page_size), 1000))

    while True:
        end = start + page_size - 1
        # NOTE: Do NOT select cleaned_text in bulk pages. Some historical rows may
        # contain invalid characters that make PostgREST fail to generate JSON.
        # For --infer-from-text, fetch cleaned_text per-row only when needed.
        query = client.table("cv_intelligence").select(
            "anonymized_id,llm_provider,key_skills,core_technical_skills,secondary_technical_skills,created_at"
        )

        # PostgREST range pagination
        query = query.range(start, end).order("created_at", desc=False)
        resp = query.execute()
        rows = resp.data or []
        if not rows:
            break

        for row in rows:
            if args.limit and stats.scanned >= args.limit:
                break

            stats.scanned += 1

            if args.only_placeholders and not _is_placeholder(row):
                continue

            anonymized_id = row.get("anonymized_id")
            if not anonymized_id:
                continue

            if not _needs_key_skills(row):
                continue

            core = _as_list(row.get("core_technical_skills"))
            secondary = _as_list(row.get("secondary_technical_skills"))

            update: Dict[str, object] = {"anonymized_id": anonymized_id}

            if core or secondary:
                combined = _dedupe_case_insensitive(core + secondary, max_items=30)
                if not combined:
                    stats.skipped_no_signal += 1
                    continue

                update["key_skills"] = combined

                if do_write:
                    try:
                        client.table("cv_intelligence").update(update).eq("anonymized_id", anonymized_id).execute()
                    except Exception as e:
                        stats.write_errors += 1
                        print(f"[WRITE_ERROR] {anonymized_id}: {type(e).__name__}: {e}")
                        continue

                stats.updated_from_existing += 1
                continue

            # No skill fields present
            if args.infer_from_text:
                try:
                    text_resp = (
                        client.table("cv_intelligence")
                        .select("cleaned_text")
                        .eq("anonymized_id", anonymized_id)
                        .limit(1)
                        .execute()
                    )
                    cleaned_text = (text_resp.data or [{}])[0].get("cleaned_text") or ""
                except Exception as e:
                    print(f"[READ_ERROR] {anonymized_id}: {type(e).__name__}: {e}")
                    cleaned_text = ""

                inferred = _infer_skills_from_text(cleaned_text)
                if not inferred and args.lexicon_fallback:
                    inferred = _infer_skills_from_lexicon(cleaned_text)
                if inferred:
                    update["core_technical_skills"] = inferred
                    update["secondary_technical_skills"] = []
                    update["key_skills"] = inferred

                    if do_write:
                        try:
                            client.table("cv_intelligence").update(update).eq("anonymized_id", anonymized_id).execute()
                        except Exception as e:
                            stats.write_errors += 1
                            print(f"[WRITE_ERROR] {anonymized_id}: {type(e).__name__}: {e}")
                            continue

                    stats.inferred_from_text += 1
                else:
                    stats.skipped_no_signal += 1
            else:
                # Missing key_skills, but we have no other fields to derive it.
                stats.skipped_no_signal += 1

        if args.limit and stats.scanned >= args.limit:
            break

        start += page_size

    mode = "APPLY" if do_write else "DRY_RUN"
    print("Backfill key_skills:", mode)
    print("- scanned:", stats.scanned)
    print("- updated_from_existing:", stats.updated_from_existing)
    print("- inferred_from_text:", stats.inferred_from_text)
    print("- skipped_no_signal:", stats.skipped_no_signal)
    print("- write_errors:", stats.write_errors)

    if do_write and stats.write_errors:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
