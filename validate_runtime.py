"""
Runtime validation for the CV Intelligence System.

Runs real connectivity and model checks for:
- LLM provider
- Supabase
- Embeddings

Usage:
    .venv\\Scripts\\python validate_runtime.py
"""

from __future__ import annotations

import json
from dotenv import load_dotenv

load_dotenv('.env', override=True)

from app import probe_embedding_runtime, probe_llm_provider, probe_supabase_runtime


def main() -> int:
    report = {
        'llm': probe_llm_provider(),
        'supabase': probe_supabase_runtime(),
        'embeddings': probe_embedding_runtime(),
    }

    print(json.dumps(report, indent=2))

    failed = [
        name for name, status in report.items()
        if not status.get('reachable')
    ]

    if failed:
        print(f"\nFAILED: {', '.join(failed)}")
        return 1

    print("\nAll runtime checks passed.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
