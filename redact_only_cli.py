#!/usr/bin/env python3
"""Redaction-only CLI wrapper.

Purpose:
- Run ONLY the local redaction pipeline (no LLM, no embeddings, no DB).
- Provide a stable interface that can be called from other pipelines.

Examples:
  # Redact a single file and write output into ./redacted_output
  python redact_only_cli.py input.pdf

  # Redact a directory recursively
  python redact_only_cli.py resume/ --output redacted_output/

  # Redact a single file and print redacted text to stdout
  python redact_only_cli.py input.pdf --stdout

  # Emit JSON results (safe to parse by another process)
  python redact_only_cli.py resume/ --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from universal_pipeline_engine import logger
from redaction_runner import redact_cv_file, resolve_runtime_root


def _resolve_runtime_root() -> Path:
    return resolve_runtime_root()


def _iter_input_files(input_path: Path) -> List[Path]:
    if input_path.is_file():
        return [input_path]

    # NOTE: Legacy .doc is intentionally not included here; the underlying
    # parser stack is DOCX/PDF-first. If you need .doc support, convert to .docx.
    patterns = ["**/*.pdf", "**/*.docx"]
    files: List[Path] = []
    for pattern in patterns:
        files.extend(list(input_path.glob(pattern)))

    # Deterministic ordering
    return sorted({p.resolve() for p in files})


def _safe_output_name(input_file: Path) -> str:
    # Mirror orchestrator behavior used in process_directory.
    return f"REDACTED_{input_file.stem}.txt"


def _redact_one(
    config_dir: Path,
    input_file: Path,
    output_dir: Optional[Path],
) -> Dict[str, Any]:
    if input_file.suffix.lower() == '.doc':
        return {
            "ok": False,
            "input": str(input_file),
            "output": None,
            "error": "Unsupported input format: .doc (please convert to .docx)",
        }
    try:
        redacted_text, profile = redact_cv_file(input_file, config_dir=config_dir)

        output_path: Optional[Path] = None
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / _safe_output_name(input_file)
            output_path.write_text(redacted_text, encoding="utf-8")

        return {
            "ok": True,
            "input": str(input_file),
            "output": str(output_path) if output_path else None,
            "cv_type": getattr(profile, "cv_type", None).value if getattr(profile, "cv_type", None) else None,
            "confidence": getattr(profile, "confidence", None),
            "redacted_text": redacted_text,
        }
    except Exception as exc:
        return {
            "ok": False,
            "input": str(input_file),
            "output": None,
            "error": str(exc),
        }


def main(argv: Optional[List[str]] = None) -> int:
    runtime_root = _resolve_runtime_root()

    parser = argparse.ArgumentParser(description="Redact CVs (redaction-only; no LLM/DB)")
    parser.add_argument("input", help="Input file or directory (pdf/doc/docx)")
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output directory for redacted .txt files (default: <runtime>/redacted_output).",
    )
    parser.add_argument(
        "--config-dir",
        default=None,
        help="Config directory (default: <runtime>/config).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging in the pipeline.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print redacted text to stdout (single-file input only).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON results to stdout.",
    )
    parser.add_argument(
        "--json-file",
        default=None,
        help="Write JSON results to a UTF-8 file (avoids PowerShell '>' UTF-16 output).",
    )
    parser.add_argument(
        "--no-text",
        action="store_true",
        help="Omit redacted_text from JSON output (smaller payload).",
    )

    args = parser.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"ERROR: input not found: {input_path}", file=sys.stderr)
        return 2

    if args.stdout and not input_path.is_file():
        print("ERROR: --stdout requires a single input file", file=sys.stderr)
        return 2

    # Default locations are next to the exe/script.
    config_dir = Path(args.config_dir).expanduser().resolve() if args.config_dir else (runtime_root / "config")
    output_dir = (
        None
        if args.stdout
        else (Path(args.output).expanduser().resolve() if args.output else (runtime_root / "redacted_output"))
    )

    # Keep stdout clean when emitting text/JSON.
    if args.stdout or args.json:
        logger.setLevel("ERROR")

    results: List[Dict[str, Any]] = []
    for file_path in _iter_input_files(input_path):
        results.append(_redact_one(config_dir, file_path, output_dir))

    if args.stdout:
        # Single file mode (already enforced)
        result = results[0]
        if not result.get("ok"):
            print(result.get("error") or "Unknown error", file=sys.stderr)
            return 1
        sys.stdout.write(result["redacted_text"])
        return 0

    if args.json or args.json_file:
        payload = {"results": results}
        if args.no_text:
            for item in payload["results"]:
                item.pop("redacted_text", None)

        json_text = json.dumps(payload, ensure_ascii=False)

        if args.json_file:
            json_path = Path(args.json_file).expanduser().resolve()
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json_text, encoding="utf-8")

        if args.json:
            sys.stdout.write(json_text)
        return 0 if all(r.get("ok") for r in results) else 1

    # Human CLI summary
    ok = sum(1 for r in results if r.get("ok"))
    fail = len(results) - ok
    print(f"Processed: {len(results)} | Success: {ok} | Failed: {fail}")
    if output_dir is not None:
        print(f"Output: {output_dir}")

    if fail:
        for r in results:
            if not r.get("ok"):
                print(f"- Failed: {r.get('input')} :: {r.get('error')}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
