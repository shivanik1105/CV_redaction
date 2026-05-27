"""Reprocess 20 recoverable empty candidates with Groq rate limit protection.

Usage:
    python reprocess_20.py --apply
"""
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase_storage import SupabaseStorage
from cv_intelligence_extractor import CVIntelligenceExtractor
from vector_search import VectorSearchEngine
from universal_pipeline_engine import PipelineOrchestrator

# 20 recoverable candidates: (anonymized_id, file_path)
RECOVERABLE = [
    ('CAND_856', r"archive\samples\more\VarunsaagarSaravanan_ML Engg.or GEN AI_TTL_Bangalore_July24_Propellence.pdf"),
    ('CAND_759', r"uploads\20260503_203531_Rohini_Parhate_Resume_1991-1_1.pdf"),
    ('CAND_384', r"archive\samples\more\ResumeU.pdf"),
    ('CAND_368', r"archive\samples\more\Thakur Pranay Singh (Projects) CV.docx"),
    ('CAND_988', r"archive\samples\more\RishabhJain.pdf"),
    ('CAND_687', r"archive\samples\more\RajendraPrasad.pdf"),
    ('CAND_408', r"archive\samples\more\RAJESH _ZANKE __-_Sr. Technical Support Engineer _Rajesh Siddharth Zanke conv (1).pdf"),
    ('CAND_987', r"archive\samples\more\Shivani Shinde-Resume.pdf"),
    ('CAND_360', r"archive\samples\more\Nikhil_Resume (1) (1).pdf"),
    ('CAND_166', r"archive\samples\more\Tejas Deshmukhs Resume.pdf"),
    ('CAND_459', r"uploads\20260406_220420_Naukri_MayurPatil3y_2m.pdf"),
    ('CAND_919', r"archive\samples\more\TKT_CV.docx"),
    ('CAND_803', r"archive\samples\more\SayliMukundHisvankar.pdf"),
    ('CAND_658', r"uploads\20260512_162518_Anandprakash_Tandale_Resume_2.pdf"),
    ('CAND_627', r"uploads\20260503_203531_Rohini_Parhate_Resume_1991-1_1.pdf"),
    ('CAND_416', r"archive\samples\more\Vishnu Suresh Babu_Mechanical Lead_Tata Elxsi_02 OCT 2024 (1).pdf"),
    ('CAND_230', r"archive\samples\more\Pranay Kharode_Senior Specialist_Resume.pdf"),
    ('CAND_769', r"archive\samples\more\Resume-Ravi Pandey.docx"),
    ('CAND_700', r"archive\samples\more\Samrat Tidke (1).pdf"),
    ('CAND_227', r"archive\samples\more\VarsharaniJagdale.pdf"),
]


def extract_and_redact(file_path: str) -> Optional[str]:
    """Extract and redact text from a CV file."""
    try:
        orchestrator = PipelineOrchestrator()
        final_text, _profile = orchestrator.process_cv(file_path, redact=True)
        if final_text and len(final_text) > 100:
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
    print(f"Reprocessing 20 recoverable candidates: {mode}\n")

    if not args.apply:
        print("Will process:")
        for aid, path in RECOVERABLE:
            print(f"  {aid} -> {path}")
        print("\n(Dry run. Use --apply to execute.)")
        return

    storage = SupabaseStorage()
    extractor = CVIntelligenceExtractor()
    engine = VectorSearchEngine(embedding_provider="local")

    success = 0
    failed = 0
    skipped = 0

    for i, (aid, path) in enumerate(RECOVERABLE, 1):
        print(f"\n[{i}/20] {aid} -> {path}")

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

        # CRITICAL: Override with original ID so we UPDATE existing record
        intelligence['anonymized_id'] = aid

        try:
            storage.store_intelligence(intelligence)
        except Exception as e:
            print(f"  -> STORE_ERROR: {e}")
            failed += 1
            continue

        # Generate and store embedding
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

        # Rate limit protection - wait between calls
        if i < len(RECOVERABLE):
            delay = 8  # 8 seconds between LLM calls
            print(f"  Waiting {delay}s for rate limit...")
            time.sleep(delay)

    print(f"\n{'='*50}")
    print(f"Reprocessing complete!")
    print(f"  Success: {success}/20")
    print(f"  Failed: {failed}/20")
    print(f"  Skipped: {skipped}/20")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
