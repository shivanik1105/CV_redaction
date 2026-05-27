"""Reprocess remaining empty candidates with local files or cleaned_text.

Covers:
- 5 candidates with local PDF/DOCX files in archive/samples/more/
- 1 candidate (CAND_991) with substantial cleaned_text in Supabase
"""
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase_storage import SupabaseStorage
from cv_intelligence_extractor import CVIntelligenceExtractor
from vector_search import VectorSearchEngine
from universal_pipeline_engine import PipelineOrchestrator

# Candidates with local files
FILE_CANDIDATES = [
    ('CAND_856', r"archive\samples\more\VarunsaagarSaravanan_ML Engg.or GEN AI_TTL_Bangalore_July24_Propellence.pdf"),
    ('CAND_308', r"archive\samples\more\VarsharaniJagdale.pdf"),
    ('CAND_947', r"archive\samples\more\Vishnu Suresh Babu_Mechanical Lead_Tata Elxsi_02 OCT 2024 (1).pdf"),
    ('CAND_903', r"archive\samples\more\Naukri_RaviPurankar[6y_0m].pdf"),
    ('CAND_271', r"archive\samples\more\Naukri_YogeshBhagwatraoJadhav[5y_2m].pdf"),
]

# Candidate with cleaned_text only
TEXT_CANDIDATES = [
    'CAND_991',
]


def extract_and_redact(file_path: str, max_chars: int = 8000) -> Optional[str]:
    """Extract and redact text from a CV file, truncating if too long."""
    try:
        orchestrator = PipelineOrchestrator()
        final_text, _profile = orchestrator.process_cv(file_path, redact=True)
        if not final_text or len(final_text) < 100:
            return None
        # Truncate to avoid Payload Too Large
        if len(final_text) > max_chars:
            print(f"    Truncating from {len(final_text)} to {max_chars} chars")
            final_text = final_text[:max_chars]
        return final_text
    except Exception as e:
        print(f"    Pipeline error: {e}")
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    mode = "APPLY" if args.apply else "DRY_RUN"
    print(f"Reprocessing {len(FILE_CANDIDATES)} file-based + {len(TEXT_CANDIDATES)} text-based candidates: {mode}\n")

    storage = SupabaseStorage()
    extractor = CVIntelligenceExtractor()
    engine = VectorSearchEngine(embedding_provider="local")

    success = 0
    failed = 0
    skipped = 0
    total = len(FILE_CANDIDATES) + len(TEXT_CANDIDATES)
    idx = 0

    # --- File-based candidates ---
    for aid, path in FILE_CANDIDATES:
        idx += 1
        print(f"\n[{idx}/{total}] {aid} -> {path}")

        if not args.apply:
            print(f"  -> DRY_RUN")
            continue

        if not Path(path).exists():
            print(f"  -> SKIP: File not found")
            skipped += 1
            continue

        cv_text = extract_and_redact(path)
        if not cv_text or len(cv_text) < 100:
            print(f"  -> SKIP: Extraction failed or too short ({len(cv_text) if cv_text else 0} chars)")
            skipped += 1
            continue

        try:
            intelligence = extractor.extract_intelligence(
                cv_text,
                job_description=None,
                original_filename=Path(path).name,
                trust_source=True,
            )
        except Exception as e:
            print(f"  -> EXTRACTION_ERROR: {e}")
            failed += 1
            continue

        if "error" in intelligence:
            print(f"  -> EXTRACTION_ERROR: {intelligence.get('error')}")
            failed += 1
            continue

        intelligence['anonymized_id'] = aid

        try:
            storage.store_intelligence(intelligence)
        except Exception as e:
            print(f"  -> STORE_ERROR: {e}")
            failed += 1
            continue

        try:
            embedding_text = engine.build_embedding_text(intelligence)
            embedding = engine.generate_embedding(embedding_text)
            if embedding:
                storage.store_embedding(aid, embedding)
        except Exception as e:
            print(f"  -> Embedding warning: {e}")

        ks = intelligence.get('key_skills', [])
        print(f"  -> SUCCESS ({len(ks)} key_skills)")
        success += 1

        if idx < total:
            delay = 8
            print(f"  Waiting {delay}s for rate limit...")
            time.sleep(delay)

    # --- Text-based candidates ---
    for aid in TEXT_CANDIDATES:
        idx += 1
        print(f"\n[{idx}/{total}] {aid} -> from Supabase cleaned_text")

        if not args.apply:
            print(f"  -> DRY_RUN")
            continue

        resp = storage.client.table("cv_intelligence").select("cleaned_text").eq("anonymized_id", aid).limit(1).execute()
        if not resp.data:
            print(f"  -> SKIP: Not found in Supabase")
            skipped += 1
            continue

        cleaned_text = resp.data[0].get("cleaned_text", "")
        if not cleaned_text or len(cleaned_text) < 100:
            print(f"  -> SKIP: cleaned_text too short ({len(cleaned_text)} chars)")
            skipped += 1
            continue

        # Truncate if needed
        if len(cleaned_text) > 8000:
            print(f"    Truncating cleaned_text from {len(cleaned_text)} to 8000 chars")
            cleaned_text = cleaned_text[:8000]

        try:
            intelligence = extractor.extract_intelligence(
                cleaned_text,
                job_description=None,
                original_filename=f"{aid}_cleaned_text",
                trust_source=True,
            )
        except Exception as e:
            print(f"  -> EXTRACTION_ERROR: {e}")
            failed += 1
            continue

        if "error" in intelligence:
            print(f"  -> EXTRACTION_ERROR: {intelligence.get('error')}")
            failed += 1
            continue

        intelligence['anonymized_id'] = aid

        try:
            storage.store_intelligence(intelligence)
        except Exception as e:
            print(f"  -> STORE_ERROR: {e}")
            failed += 1
            continue

        try:
            embedding_text = engine.build_embedding_text(intelligence)
            embedding = engine.generate_embedding(embedding_text)
            if embedding:
                storage.store_embedding(aid, embedding)
        except Exception as e:
            print(f"  -> Embedding warning: {e}")

        ks = intelligence.get('key_skills', [])
        print(f"  -> SUCCESS ({len(ks)} key_skills)")
        success += 1

        if idx < total:
            delay = 8
            print(f"  Waiting {delay}s for rate limit...")
            time.sleep(delay)

    if args.apply:
        print(f"\n{'='*50}")
        print(f"Reprocessing complete!")
        print(f"  Success: {success}/{total}")
        print(f"  Failed: {failed}/{total}")
        print(f"  Skipped: {skipped}/{total}")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
