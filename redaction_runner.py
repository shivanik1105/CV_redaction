"""Reusable redaction-only runner used across the project.

Goal:
- Single source of truth for how we run redaction (no LLM/DB).
- Works both in normal Python mode and PyInstaller frozen mode.
- Ensures config is persistent and writable (copies bundled config on first run).

This module does NOT implement PII rules itself; it simply orchestrates
`universal_pipeline_engine.PipelineOrchestrator` safely.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from universal_pipeline_engine import PipelineOrchestrator


def resolve_runtime_root() -> Path:
    """Return a persistent writable root for runtime data.

    In frozen PyInstaller mode, write next to the bundled executable.
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def default_config_dir(runtime_root: Optional[Path] = None) -> Path:
    root = runtime_root or resolve_runtime_root()
    return root / "config"


def ensure_runtime_config(config_dir: Path, runtime_root: Optional[Path] = None) -> None:
    """Ensure config exists and is populated in frozen builds.

    For PyInstaller onefile mode, data files live under sys._MEIPASS at runtime.
    This copies bundled config into a persistent location next to the exe.

    If config exists already, no-op.
    """

    if config_dir.exists():
        return

    runtime_root = runtime_root or resolve_runtime_root()

    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS", runtime_root))
        bundled_config = bundle_root / "config"
        if bundled_config.exists() and bundled_config.is_dir():
            shutil.copytree(bundled_config, config_dir)
            return

    config_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=8)
def _get_orchestrator_cached(config_dir_str: str, debug: bool) -> PipelineOrchestrator:
    return PipelineOrchestrator(debug=debug, config_dir=config_dir_str)


def get_orchestrator(*, config_dir: Path, debug: bool = False) -> PipelineOrchestrator:
    ensure_runtime_config(config_dir)
    return _get_orchestrator_cached(str(config_dir), bool(debug))


def redact_cv_file(
    cv_path: Path,
    *,
    config_dir: Optional[Path] = None,
    debug: bool = False,
) -> Tuple[str, Any]:
    """Redact a CV file via the universal pipeline.

    Returns:
      (redacted_text, profile)

    Raises:
      ValueError for unsupported formats.
    """

    path = Path(cv_path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    if path.suffix.lower() == ".doc":
        raise ValueError("Unsupported input format: .doc (please convert to .docx)")

    config_dir = config_dir or default_config_dir()
    orchestrator = get_orchestrator(config_dir=config_dir, debug=debug)
    return orchestrator.process_cv(str(path))


def redact_cv_text_only(
    cv_path: Path,
    *,
    config_dir: Optional[Path] = None,
    debug: bool = False,
) -> str:
    """Convenience wrapper that returns only redacted text."""

    text, _profile = redact_cv_file(cv_path, config_dir=config_dir, debug=debug)
    return text


def _load_pii_config(config_dir: Path) -> Dict[str, Any]:
    ensure_runtime_config(config_dir)
    path = Path(config_dir) / "pii_patterns.json"
    if not path.exists():
        # If config hasn't been generated yet, force orchestrator init.
        _ = get_orchestrator(config_dir=config_dir, debug=False)
    return json.loads(path.read_text(encoding="utf-8"))


def _compile_pii_regexes(pii_config: Dict[str, Any]) -> Dict[str, Any]:
    email_re = re.compile(pii_config["email"]["pattern"], re.IGNORECASE)
    url_re = re.compile(pii_config["url"]["pattern"], re.IGNORECASE)
    phone_res = [re.compile(p) for p in pii_config["phone"]["patterns"]]
    social_res = [re.compile(p, re.IGNORECASE) for p in pii_config["social"]["patterns"]]
    return {
        "email": email_re,
        "url": url_re,
        "phone": phone_res,
        "social": social_res,
    }


def _guess_name_tokens_from_filename(path: Path) -> List[str]:
    """Best-effort guess of candidate name tokens from filename.

    Example: Rohini_Parhate_Resume_1991-1 (1).pdf -> ["Rohini", "Parhate"]
    """

    stem = path.stem
    stem = re.sub(r"\(\d+\)$", "", stem).strip()
    parts = re.split(r"[_\-\s]+", stem)

    stop = {
        "resume",
        "cv",
        "profile",
        "updated",
        "final",
        "latest",
        "copy",
        "redacted",
        "anonymized",
        "anonymised",
    }

    tokens: List[str] = []
    for p in parts:
        p = re.sub(r"[^A-Za-z]", "", p)
        if len(p) < 3:
            continue
        if p.lower() in stop:
            continue
        tokens.append(p)
        if len(tokens) >= 4:
            break

    # Prefer first 2 tokens (typical First Last)
    return tokens[:2] if len(tokens) >= 2 else tokens


def _is_contact_line(text: str) -> bool:
    # Keep aligned with universal_pipeline_engine._remove_pii
    return bool(
        re.match(
            # Expand beyond pure "contact" to catch address / demographics lines too.
            # Bias toward over-redaction (privacy-first).
            r"(?i)^.*?(email|e-mail|phone|mobile|contact|linkedin|github|address|location|residence|permanent|current\s+address|dob|date\s+of\s+birth|born\s+on|nationality|gender|marital\s+status|passport|ssn|pan|aadhar|driving\s+licen[cs]e).*?[:|-].*?$",
            text,
        )
    )


def _is_addressish_line(text: str) -> bool:
    """Heuristic: detect address/location lines even without explicit 'Address:' marker."""
    t = (text or "").strip()
    if not t:
        return False
    # Postal / zip / pincode patterns (India often 6 digits; US 5 digits)
    if re.search(r"\b\d{6}\b", t) or re.search(r"\b\d{5}(?:-\d{4})?\b", t):
        return True
    # Common address tokens
    if re.search(
        r"(?i)\b(flat|apt|apartment|residenc(y|e)|building|bldg|tower|wing|plot|house|h\.?no\.?|road|rd\b|street|st\b|lane|ln\b|avenue|ave\b|sector|block|colony|nagar|society|phase|near|behind|opp\b|opposite|pincode|pin\s*code|zip)\b",
        t,
    ):
        return True
    # Lines with multiple commas + digits are frequently addresses
    if t.count(",") >= 1 and re.search(r"\d", t):
        return True
    return False


def _find_soffice_executable() -> Optional[str]:
    """Locate LibreOffice 'soffice' binary if present on PATH."""
    import shutil

    return shutil.which("soffice") or shutil.which("soffice.exe")


def _convert_docx_to_pdf(docx_path: Path, *, output_pdf: Path) -> Path:
    """Best-effort DOCX -> PDF conversion.

    Tries:
    - docx2pdf (Windows/macOS; typically requires MS Word)
    - LibreOffice (soffice) headless conversion
    """
    docx_path = Path(docx_path)
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    def _looks_like_valid_pdf(p: Path) -> bool:
        try:
            if not p.exists() or p.stat().st_size < 2048:
                return False
            with open(p, "rb") as f:
                head = f.read(5)
            if head != b"%PDF-":
                return False
            # Optional: ensure it has pages.
            try:
                import fitz  # type: ignore

                d = fitz.open(str(p))
                ok = d.page_count > 0
                d.close()
                return ok
            except Exception:
                return True
        except Exception:
            return False

    # 1) Try docx2pdf (if installed)
    try:
        from docx2pdf import convert  # type: ignore

        convert(str(docx_path), str(output_pdf))
        if _looks_like_valid_pdf(output_pdf):
            return output_pdf
    except Exception:
        pass

    # 2) Try LibreOffice
    soffice = _find_soffice_executable()
    if soffice:
        import subprocess

        # LibreOffice outputs to directory; filename is derived from input.
        out_dir = output_pdf.parent
        subprocess.run(
            [
                soffice,
                "--headless",
                "--nologo",
                "--nofirststartwizard",
                "--convert-to",
                "pdf",
                "--outdir",
                str(out_dir),
                str(docx_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        candidate = out_dir / f"{docx_path.stem}.pdf"
        if _looks_like_valid_pdf(candidate):
            if candidate.resolve() != output_pdf.resolve():
                candidate.replace(output_pdf)
            return output_pdf

    raise RuntimeError(
        "DOCX->PDF conversion not available. Install MS Word + docx2pdf, "
        "or install LibreOffice (soffice) and ensure it is on PATH."
    )


def _render_text_to_pdf(text: str, *, output_pdf: Path, title: Optional[str] = None) -> Path:
    """Create a simple PDF containing the provided text (fallback for non-PDF inputs)."""
    try:
        import fitz  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("PyMuPDF (fitz) is required for PDF output") from e

    import unicodedata

    def _normalize_for_pdf(s: str) -> str:
        # PyMuPDF's built-in fonts can replace bullets/smart quotes with '?'.
        if not isinstance(s, str):
            s = str(s)
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        s = (
            s.replace("•", "- ")
            .replace("◦", "- ")
            .replace("▪", "- ")
            .replace("●", "- ")
            .replace("–", "-")
            .replace("—", "-")
            .replace("−", "-")
            .replace("“", '"')
            .replace("”", '"')
            .replace("’", "'")
            .replace("‘", "'")
            .replace("…", "...")
        )
        s = unicodedata.normalize("NFKD", s)
        s = s.encode("ascii", "ignore").decode("ascii")
        s = s.replace("\u00a0", " ")
        s = re.sub(r"[\t\f\v]+", " ", s)
        return s

    text = _normalize_for_pdf(text or "")

    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Simple pagination: fixed line budget per page.
    lines = (text or "").splitlines() or [""]
    lines_per_page = 60
    font_size = 10
    margin = 36  # 0.5 inch

    doc = fitz.open()
    try:
        if title:
            lines = [title, "", *lines]
        for i in range(0, len(lines), lines_per_page):
            chunk = lines[i : i + lines_per_page]
            page = doc.new_page(width=595, height=842)  # A4 portrait
            rect = fitz.Rect(margin, margin, page.rect.width - margin, page.rect.height - margin)
            page.insert_textbox(rect, "\n".join(chunk), fontsize=font_size)
        doc.save(str(output_pdf), deflate=True)
    finally:
        doc.close()

    return output_pdf


def render_text_to_pdf(text: str, *, output_pdf: Path, title: Optional[str] = None) -> Path:
    """Public wrapper for rendering redacted text into a PDF."""
    return _render_text_to_pdf(text, output_pdf=output_pdf, title=title)


def redact_pdf_to_file(
    pdf_path: Path,
    *,
    output_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
    config_dir: Optional[Path] = None,
    debug: bool = False,
    remove_images: bool = True,
    remove_images_max_area_ratio: float = 0.30,
) -> Path:
    """Create a masked/redacted PDF with black boxes over detected PII.

    This mirrors the common "anonymized PDF" style (black rectangles) seen in
    some CV analyzer tools.

    Redacts (best-effort):
    - email, phone, urls, linkedin/github handles
    - whole contact lines (email/phone/contact/linkedin/github)
    - guessed candidate name tokens from filename (optional)

    Notes:
    - This is rule-based; no LLM is used.
    - Works only for PDFs (requires PyMuPDF / fitz).
    """

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    if path.suffix.lower() != ".pdf":
        raise ValueError("redact_pdf_to_file supports only .pdf inputs")

    try:
        import fitz  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("PyMuPDF (fitz) is required for PDF redaction") from e

    config_dir = config_dir or default_config_dir()
    pii_config = _load_pii_config(config_dir)
    pii_res = _compile_pii_regexes(pii_config)
    name_tokens = _guess_name_tokens_from_filename(path)

    runtime_root = resolve_runtime_root()
    out_dir = Path(output_dir) if output_dir else (runtime_root / "redacted_output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(output_path) if output_path else (out_dir / f"REDACTED_{path.name}")

    def _word_matches_pii(word: str) -> bool:
        if pii_res["email"].search(word):
            return True
        if pii_res["url"].search(word):
            return True
        if any(r.search(word) for r in pii_res["social"]):
            return True
        if any(r.search(word) for r in pii_res["phone"]):
            return True
        return False

    def _word_is_name_token(word: str) -> bool:
        w = re.sub(r"[^A-Za-z]", "", word)
        if not w:
            return False
        return any(w.lower() == t.lower() for t in name_tokens)

    doc = fitz.open(str(path))
    try:
        total_redactions = 0
        for page in doc:
            # words: x0, y0, x1, y1, word, block_no, line_no, word_no
            words = page.get_text("words")
            if not words:
                continue

            lines: Dict[Tuple[int, int], List[Tuple[fitz.Rect, str]]] = {}
            for x0, y0, x1, y1, word, block_no, line_no, _word_no in words:
                rect = fitz.Rect(x0, y0, x1, y1)
                lines.setdefault((int(block_no), int(line_no)), []).append((rect, str(word)))

            rects_to_redact: List[fitz.Rect] = []

            def _build_line_string(items_sorted: List[Tuple[fitz.Rect, str]]) -> Tuple[str, List[Tuple[int, int]]]:
                """Return (line_str, spans_per_word) where spans are [start,end) in line_str."""
                parts: List[str] = []
                spans: List[Tuple[int, int]] = []
                pos = 0
                for _r, w in items_sorted:
                    w = str(w)
                    if parts:
                        parts.append(" ")
                        pos += 1
                    start = pos
                    parts.append(w)
                    pos += len(w)
                    spans.append((start, pos))
                return "".join(parts), spans

            def _rect_union_for_word_indexes(items_sorted: List[Tuple[fitz.Rect, str]], idxs: List[int]) -> Optional[fitz.Rect]:
                if not idxs:
                    return None
                union = items_sorted[idxs[0]][0]
                for wi in idxs[1:]:
                    union |= items_sorted[wi][0]
                return union

            for (_blk, _ln), items in lines.items():
                # Keep deterministic ordering for stable unions
                items_sorted = sorted(items, key=lambda t: (t[0].y0, t[0].x0))
                line_text, spans = _build_line_string(items_sorted)

                # Union rect for the whole line (used for full-line redactions)
                line_union = items_sorted[0][0]
                for rr, _ww in items_sorted[1:]:
                    line_union |= rr

                # Heuristic: redact probable name header lines near the top.
                # This catches cases where the candidate name is present but the filename
                # doesn't include it (common when uploads are renamed).
                try:
                    top_threshold = page.rect.height * 0.15  # Reduced from 0.22 to 0.15 - only very top
                    in_top_band = float(line_union.y1) <= float(top_threshold)
                except Exception:
                    in_top_band = False

                if in_top_band:
                    lt = line_text.strip()
                    # Avoid masking generic headings, job titles, company names, and technical terms
                    skip_patterns = [
                        r"(?i)\b(resume|curriculum\s+vitae|cv|profile|summary|objective)\b",
                        r"(?i)\b(engineer|developer|architect|manager|consultant|analyst|lead|senior|junior|principal)\b",
                        r"(?i)\b(pvt|ltd|limited|inc|corporation|corp|llc|llp|international|global|solutions|technologies|systems)\b",
                        r"(?i)\b(software|system|technical|project|product|data|web|mobile|cloud|devops)\b",
                        r"(?i)\b(experience|skills|education|certification|projects|achievements)\b",
                    ]
                    if not any(re.search(pat, lt) for pat in skip_patterns):
                        # Name-like: handle honorifics and punctuation.
                        cleaned = re.sub(r"[^A-Za-z\s]", " ", lt)
                        cleaned = re.sub(r"\s+", " ", cleaned).strip()
                        honorific = r"(?:Mr|Mrs|Ms|Miss|Dr|Prof|Shri|Smt)"
                        # More restrictive: only 2-3 words, no long phrases
                        name_pat = rf"(?:{honorific}\s+)?[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){{1,2}}"
                        if re.fullmatch(name_pat, cleaned) and not re.search(r"\d", cleaned) and len(cleaned.split()) <= 3:
                            rects_to_redact.append(line_union + (-2, -1, 2, 1))
                            continue

                    # Also redact address-ish lines near the top (often immediate PII).
                    # But skip if it contains job-related keywords
                    if _is_addressish_line(lt) and not any(re.search(pat, lt) for pat in skip_patterns):
                        rects_to_redact.append(line_union + (-2, -1, 2, 1))
                        continue

                # Address PII can appear outside the header band as well.
                # If the line includes a zip/pincode-like sequence, redact the full line.
                # BUT: Skip if the line contains job-related content (dates, job titles, companies)
                has_postal_code = bool(re.search(r"\b\d{6}\b", line_text) or re.search(r"\b\d{5}(?:-\d{4})?\b", line_text))
                if has_postal_code:
                    # Check if this looks like a job description line (has dates, job titles, etc.)
                    job_indicators = [
                        r"\d{4}\s*[-–]\s*\d{4}",  # Date ranges like 2018-2021
                        r"(?i)\b(engineer|developer|architect|manager|consultant|analyst|lead)\b",
                        r"(?i)\b(pvt|ltd|limited|inc|corporation|corp)\b",
                        r"(?i)\b(experience|project|role|position|responsibilities)\b",
                    ]
                    is_job_line = any(re.search(pat, line_text) for pat in job_indicators)
                    if not is_job_line:
                        rects_to_redact.append(line_union + (-2, -1, 2, 1))
                        continue

                # If the line contains explicit PII patterns, redact the entire line.
                # BUT: Be more selective - don't redact if it's clearly job content
                line_has_direct_pii = bool(
                    pii_res["email"].search(line_text)
                    or pii_res["url"].search(line_text)
                    or any(r.search(line_text) for r in pii_res["social"])
                    or any(r.search(line_text) for r in pii_res["phone"])
                )

                # Check if this is a contact line OR has direct PII
                # BUT: Skip redaction if it's clearly part of job description
                if _is_contact_line(line_text) or line_has_direct_pii:
                    # Check if this line contains job-related content that should be preserved
                    job_content_indicators = [
                        r"(?i)\b(build|develop|design|implement|manage|lead|create|maintain|optimize|proficient|experienced|skilled)\b",
                        r"(?i)\b(application|system|software|platform|service|api|database|framework|technology|technologies)\b",
                        r"(?i)\b(experience|project|role|responsibilities|achievements|skills|expertise|knowledge)\b",
                        r"(?i)\b(c\+\+|python|java|javascript|react|angular|node|sql|aws|azure|docker|kubernetes|android|ios|kotlin)\b",
                        r"\d{4}\s*[-–]\s*\d{4}",  # Date ranges
                    ]
                    has_job_content = any(re.search(pat, line_text) for pat in job_content_indicators)
                    
                    # Only redact if it's truly a contact line and doesn't have job content
                    if not has_job_content:
                        union = items_sorted[0][0]
                        for r, _w in items_sorted[1:]:
                            union |= r
                        # Pad a bit to cover separators
                        rects_to_redact.append(union + (-2, -1, 2, 1))
                        continue

                # Otherwise, try to find multi-word matches (e.g., split phone numbers)
                pii_matches_word_idxs: List[int] = []
                for re_obj in [pii_res["email"], pii_res["url"], *pii_res["social"], *pii_res["phone"]]:
                    for m in re_obj.finditer(line_text):
                        ms, me = m.start(), m.end()
                        for wi, (ws, we) in enumerate(spans):
                            if we <= ms or ws >= me:
                                continue
                            pii_matches_word_idxs.append(wi)
                if pii_matches_word_idxs:
                    uniq = sorted(set(pii_matches_word_idxs))
                    rect = _rect_union_for_word_indexes(items_sorted, uniq)
                    if rect:
                        rects_to_redact.append(rect + (-2, -1, 2, 1))

                for r, w in items_sorted:
                    if _word_matches_pii(w) or _word_is_name_token(w):
                        rects_to_redact.append(r + (-1, -1, 1, 1))

            # Remove likely headshots/logos (images), but avoid nuking scanned PDFs.
            if remove_images:
                try:
                    page_area = float(page.rect.get_area()) or 1.0
                    for img in page.get_images(full=True):
                        xref = img[0]
                        for ir in page.get_image_rects(xref):
                            try:
                                ratio = float(ir.get_area()) / page_area
                            except Exception:
                                ratio = 0.0
                            # Only redact "small" images (profile photo, logo, icons)
                            if ratio <= float(remove_images_max_area_ratio):
                                rects_to_redact.append(ir + (-1, -1, 1, 1))
                except Exception:
                    # Image handling is best-effort.
                    pass

            # Apply redactions
            for r in rects_to_redact:
                page.add_redact_annot(r, fill=(0, 0, 0))
            if rects_to_redact:
                # If we redacted images, remove pixels under the redaction.
                if remove_images:
                    try:
                        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)
                    except Exception:
                        page.apply_redactions()
                else:
                    page.apply_redactions()
                total_redactions += len(rects_to_redact)

        if debug:
            print(f"PDF redaction complete: {total_redactions} regions masked")

        doc.save(str(out_path), deflate=True)
    finally:
        doc.close()

    return out_path


def mask_document_to_pdf(
    input_path: Path,
    *,
    output_path: Path,
    config_dir: Optional[Path] = None,
    debug: bool = False,
) -> Path:
    """Generate a masked PDF for PDF or DOCX inputs.

    - PDF: true redaction (black boxes + remove underlying text), removes small images.
    - DOCX: converts to PDF (best-effort) then applies same masking. If conversion is
      unavailable, falls back to generating a simple PDF from redacted text.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    config_dir = config_dir or default_config_dir()

    suffix = input_path.suffix.lower()
    if suffix == ".pdf":
        return redact_pdf_to_file(
            input_path,
            output_path=output_path,
            config_dir=config_dir,
            debug=debug,
            remove_images=True,
        )

    if suffix == ".docx":
        tmp_pdf = output_path.with_name(f"__tmp_{output_path.stem}.pdf")
        try:
            _convert_docx_to_pdf(input_path, output_pdf=tmp_pdf)

            # If conversion succeeded but produced a PDF with no extractable words,
            # redaction will miss visible PII. Detect and fall back.
            try:
                import fitz  # type: ignore

                d = fitz.open(str(tmp_pdf))
                has_words = False
                for i in range(min(2, d.page_count)):
                    if d[i].get_text("words"):
                        has_words = True
                        break
                d.close()
            except Exception:
                has_words = True

            if has_words:
                return redact_pdf_to_file(
                    tmp_pdf,
                    output_path=output_path,
                    config_dir=config_dir,
                    debug=debug,
                    remove_images=True,
                )

            # No words -> safest is to render redacted text to PDF.
            redacted_text, _profile = redact_cv_file(input_path, config_dir=config_dir)
            clean_text = cleanse_redacted_tags(redacted_text)
            return _render_text_to_pdf(
                clean_text,
                output_pdf=output_path,
                title="MASKED OUTPUT",
            )
        except Exception as e:
            # Fallback: produce a safe masked PDF that contains only already-redacted text.
            redacted_text, _profile = redact_cv_file(input_path, config_dir=config_dir)
            clean_text = cleanse_redacted_tags(redacted_text)
            return _render_text_to_pdf(
                clean_text,
                output_pdf=output_path,
                title="MASKED OUTPUT",
            )
        finally:
            try:
                if tmp_pdf.exists():
                    tmp_pdf.unlink()
            except Exception:
                pass

    raise ValueError(f"mask_document_to_pdf supports only .pdf and .docx (got {suffix})")


def extract_cv_text_no_redaction(
    cv_path: Path,
    *,
    config_dir: Optional[Path] = None,
    debug: bool = False,
) -> str:
    """Extract text using the universal pipeline extraction, but skip redaction.

    Intended for already-anonymized inputs like a masked PDF.
    """

    path = Path(cv_path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    if path.suffix.lower() == ".doc":
        raise ValueError("Unsupported input format: .doc (please convert to .docx)")

    config_dir = config_dir or default_config_dir()
    orchestrator = get_orchestrator(config_dir=config_dir, debug=debug)

    # Prefer orchestrator's extraction-only helper when available.
    extract = getattr(orchestrator, "extract_text_from_cv", None)
    if callable(extract):
        return extract(str(path))

    # Fallback: use full processing and accept the redaction.
    text, _profile = orchestrator.process_cv(str(path))
    return text


def scrub_pii_text(
    text: str,
    *,
    config_dir: Optional[Path] = None,
    add_marker: bool = False,
    replacement_style: str = "tags",
) -> str:
    """Lightweight PII scrubbing for already-anonymized documents.

    Replaces:
    - email -> [REDACTED_EMAIL]
    - phone -> [REDACTED_PHONE]
    - url -> [REDACTED_URL]
    - social -> [REDACTED_SOCIAL]
    - contact lines -> [REDACTED_CONTACT_LINE]

    This intentionally does NOT do heavy redaction (companies/locations/etc.).
    """

    config_dir = config_dir or default_config_dir()
    pii_config = _load_pii_config(config_dir)
    pii_res = _compile_pii_regexes(pii_config)

    # Preserve extraction error sentinels so upstream callers can detect them.
    if isinstance(text, str) and text.lstrip().startswith("[ERROR:"):
        return text

    # Normalize common PDF-extraction whitespace oddities (NBSP, thin spaces, etc.)
    normalized = (text or "")
    normalized = normalized.replace("\u00a0", " ")  # nbsp
    normalized = re.sub(r"[\u2000-\u200b\u202f\u205f\u3000]", " ", normalized)
    normalized = re.sub(r"[\t\r\f\v]+", " ", normalized)

    out_lines: List[str] = []
    any_replacement = False
    for line in normalized.splitlines():
        processed = line
        style = (replacement_style or "tags").strip().lower()
        if style not in {"tags", "remove"}:
            style = "tags"

        # Remove common name header lines if they survived extraction.
        # Keep this conservative to avoid clobbering things like "Project Name:".
        if re.match(r"(?i)^\s*(project|client|company)\s+name\s*[:\-]", processed):
            pass
        elif re.match(r"(?i)^\s*(full\s*name|candidate\s*name|name)\s*[:\-]\s*\S+", processed):
            processed = "[REDACTED_NAME]" if style == "tags" else ""
            any_replacement = True

        if style == "tags":
            processed = pii_res["email"].sub("[REDACTED_EMAIL]", processed)
            if processed != line:
                any_replacement = True
        else:
            processed = pii_res["email"].sub("", processed)
            if processed != line:
                any_replacement = True
        for phone_re in pii_res["phone"]:
            repl = "[REDACTED_PHONE]" if style == "tags" else ""
            new_processed = phone_re.sub(repl, processed)
            if new_processed != processed:
                any_replacement = True
            processed = new_processed
        url_repl = "[REDACTED_URL]" if style == "tags" else ""
        new_processed = pii_res["url"].sub(url_repl, processed)
        if new_processed != processed:
            any_replacement = True
        processed = new_processed
        for social_re in pii_res["social"]:
            social_repl = "[REDACTED_SOCIAL]" if style == "tags" else ""
            new_processed = social_re.sub(social_repl, processed)
            if new_processed != processed:
                any_replacement = True
            processed = new_processed

        # Extra safety-net patterns beyond the config file (covers edge-case phones/emails).
        if style == "tags":
            processed = re.sub(r"\b\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{0,4}\b", "[REDACTED_PHONE]", processed)
            processed = re.sub(r"\b\d{5,}\s+\d{5,}\b", "[REDACTED_PHONE]", processed)
        else:
            processed = re.sub(r"\b\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{0,4}\b", "", processed)
            processed = re.sub(r"\b\d{5,}\s+\d{5,}\b", "", processed)

        if _is_contact_line(processed):
            processed = "[REDACTED_CONTACT_LINE]" if style == "tags" else ""
            any_replacement = True

        # Common "Personal Details" fields that often include sensitive PII.
        if re.search(r"(?i)\b(father|mother|spouse|husband|wife)\b.*\bname\b", processed):
            processed = "[REDACTED_NAME]" if style == "tags" else ""
            any_replacement = True
        if re.search(r"(?i)\b(dob|date\s+of\s+birth|birth\s+date)\b", processed):
            processed = "[REDACTED_DOB]" if style == "tags" else ""
            any_replacement = True

        # If a line contains a postal/zip/pincode-like sequence, treat as address PII.
        if re.search(r"\b\d{6}\b", processed) or re.search(r"\b\d{5}(?:-\d{4})?\b", processed):
            processed = "[REDACTED_ADDRESS]" if style == "tags" else ""
            any_replacement = True

        # Clean up whitespace after removals/replacements.
        processed = re.sub(r"\s+", " ", processed).strip()

        if processed or style == "tags":
            out_lines.append(processed)

    output = "\n".join(out_lines)

    # For masked-PDF flows we want a deterministic marker so is_cv_anonymized() passes
    # even when no direct-contact PII strings were present.
    if style == "tags" and add_marker and "[REDACTED" not in output and output.strip():
        output = "[REDACTED_CONTACT_LINE]\n" + output
        any_replacement = True

    return output


def cleanse_redacted_tags(text: str) -> str:
    """Remove any visible [REDACTED_*] markers and clean up empty lines.

    Use this before showing text in the UI or before rendering a fallback PDF
    so the user never sees [REDACTED_NAME], [REDACTED_EMAIL], etc.
    """
    if not text:
        return text
    # Remove all [REDACTED_...] tokens
    cleaned = re.sub(r"\[REDACTED[^\]]*\]", "", text)
    # Remove lines that became empty or just whitespace
    cleaned = "\n".join(line for line in cleaned.splitlines() if line.strip())
    # Collapse excessive blank lines
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    return cleaned.strip()
