"""
Smart CV Processing - Process All CVs using Groq API (FREE)
No rate limiting needed - Groq is free and fast!
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from universal_pipeline_engine import PipelineOrchestrator
from cv_intelligence_extractor import CVIntelligenceExtractor, is_cv_anonymized
from supabase_storage import SupabaseStorage


def _extract_original_filename_from_intel_path(json_file: Path) -> str:
    """Best-effort extraction of source CV filename from an intelligence JSON path."""
    import re

    stem = json_file.stem  # e.g. REDACTED_20260326_150441_name.pdf.txt_intelligence
    suffix = "_intelligence"
    if stem.endswith(suffix):
        core = stem[:-len(suffix)]
    else:
        core = stem

    match = re.match(r"^REDACTED_\d{8}_\d{6}_(.+)$", core)
    if match:
        remaining = match.group(1)
        if remaining.endswith(".txt"):
            remaining = remaining[:-4]
        return remaining
    return ""


def process_all_cvs(
    job_description: str = None,
    samples_dirs: list = None,
    max_per_day: int = 100
):
    """
    Process all CVs from samples folder using Groq API (FREE)
    
    Args:
        job_description: Optional job description for matching analysis (if None, only extracts skills/experience)
        samples_dirs: List of directories to scan (default: ['samples', 'samples/more'])
        max_per_day: Maximum CVs to process per run (default: 100)
    """
    print("=" * 80)
    print("Smart CV Processing - Groq API (FREE)")
    print("=" * 80)
    if job_description:
        print(f"Job Description: {job_description[:100]}...")
    else:
        print("Mode: Extraction only (no JD matching)")
    print(f"Max per run: {max_per_day} CVs")
    print()
    
    # Default directories
    if samples_dirs is None:
        samples_dirs = [Path('samples'), Path('samples/more')]
    else:
        samples_dirs = [Path(d) for d in samples_dirs]
    
    # Collect all CVs
    allowed_ext = {'.pdf', '.docx', '.doc'}
    all_cvs = []
    for sample_dir in samples_dirs:
        if sample_dir.exists():
            for f in sorted(sample_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in allowed_ext:
                    all_cvs.append(f)

    source_cv_names = {cv.name for cv in all_cvs}
    
    print(f"Found {len(all_cvs)} CVs in samples folder")
    
    # Check which are already processed
    intelligence_dir = Path('llm_analysis')
    processed_files = set()
    for json_file in intelligence_dir.glob('*_intelligence.json'):
        # Extract original filename from intelligence file
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Prefer raw original filename, then fallback to sanitized/local fields.
            raw_original = data.get('original_filename_raw', '')
            if raw_original and raw_original != 'unknown':
                name = Path(raw_original).name
                if name in source_cv_names:
                    processed_files.add(name)

            fallback_original = data.get('original_filename', '')
            if fallback_original and fallback_original != 'unknown':
                name = Path(fallback_original).name
                if name in source_cv_names:
                    processed_files.add(name)

            inferred_original = _extract_original_filename_from_intel_path(json_file)
            if inferred_original and inferred_original in source_cv_names:
                processed_files.add(Path(inferred_original).name)
        except Exception:
            pass
    
    # Filter to unprocessed CVs
    unprocessed_cvs = [cv for cv in all_cvs if cv.name not in processed_files]
    
    print(f"Already processed: {len(processed_files)}")
    print(f"Remaining to process: {len(unprocessed_cvs)}")
    print()
    
    if not unprocessed_cvs:
        print("✓ All CVs already processed!")
        return
    
    # Limit to max_per_day
    cvs_to_process = unprocessed_cvs[:max_per_day]
    if len(unprocessed_cvs) > max_per_day:
        print(f"⚠️ Processing {max_per_day} CVs today (free tier limit)")
        print(f"   Remaining {len(unprocessed_cvs) - max_per_day} CVs will be processed next run")
        print()
    
    # Initialize components
    # Read LLM provider from environment (defaults to groq if not set)
    llm_provider = os.getenv('LLM_PROVIDER', 'groq')
    llm_model = os.getenv('LLM_MODEL', None)
    
    orchestrator = PipelineOrchestrator(config_dir='config')
    extractor = CVIntelligenceExtractor(api_provider=llm_provider, model=llm_model)
    storage = SupabaseStorage()
    
    # Process CVs
    stats = {
        'total': len(cvs_to_process),
        'redacted': 0,
        'llm_analyzed': 0,
        'stored_supabase': 0,
        'failed': 0,
        'start_time': time.time()
    }
    
    for idx, cv_path in enumerate(cvs_to_process, 1):
        cv_name = cv_path.name
        print(f"\n[{idx}/{len(cvs_to_process)}] Processing: {cv_name}")
        print("-" * 80)
        
        try:
            # Step 1: Redact PII
            print("  1. Redacting PII...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            redacted_filename = f"REDACTED_{timestamp}_{cv_name}.txt"
            redacted_path = Path('redacted_output') / redacted_filename
            
            redacted_text, profile = orchestrator.process_cv(str(cv_path))
            with open(redacted_path, 'w', encoding='utf-8') as f:
                f.write(redacted_text)
            print(f"     ✓ Redacted: {redacted_filename}")

            if redacted_text.startswith("[ERROR: No text extracted"):
                print("     ✗ No extractable text (skipping)")
                stats['failed'] += 1
                continue
            
            # Verify anonymization
            if not is_cv_anonymized(redacted_text):
                print(f"     ✗ Not properly anonymized (skipping)")
                stats['failed'] += 1
                continue

            stats['redacted'] += 1
            
            # Step 2: LLM Analysis
            print("  2. Analyzing with LLM...")
            
            intelligence = extractor.extract_intelligence(
                redacted_text, job_description, redacted_filename
            )
            
            if intelligence.get("error") == "CV_NOT_ANONYMIZED":
                print(f"     ✗ CV not anonymized")
                stats['failed'] += 1
                continue
            
            stats['llm_analyzed'] += 1
            print(f"     ✓ Analyzed: {intelligence.get('anonymized_id')}")
            print(f"     Confidence: {intelligence.get('confidence_score')}%")
            
            # Save intelligence JSON
            intel_filename = f"{Path(redacted_filename).stem}_intelligence.json"
            intel_path = intelligence_dir / intel_filename
            with open(intel_path, 'w', encoding='utf-8') as f:
                json.dump(intelligence, f, indent=2, ensure_ascii=False)
            
            # Step 4: Store in Supabase
            print("  4. Storing in Supabase...")
            try:
                storage.store_intelligence(intelligence)
                anon_id = intelligence.get('anonymized_id')
                if anon_id:
                    storage.store_filename_mapping(
                        anonymized_id=anon_id,
                        original_filename=cv_name,
                        anonymized_filename=redacted_filename
                    )
                stats['stored_supabase'] += 1
                print(f"     ✓ Stored in database")
            except Exception as e:
                print(f"     ⚠️ Supabase store failed: {e}")
            
            print(f"  ✓ Complete: {cv_name}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            stats['failed'] += 1
            
            # Check if quota exhausted
            if 'quota' in str(e).lower() or '429' in str(e):
                print("\n⚠️ API quota exhausted. Stopping.")
                break
    
    # Print summary
    elapsed = time.time() - stats['start_time']
    print("\n" + "=" * 80)
    print("Processing Complete")
    print("=" * 80)
    print(f"Total CVs: {stats['total']}")
    print(f"Redacted: {stats['redacted']}")
    print(f"LLM analyzed: {stats['llm_analyzed']}")
    print(f"Stored in Supabase: {stats['stored_supabase']}")
    print(f"Failed: {stats['failed']}")
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Avg time per CV: {elapsed/stats['total']:.1f} seconds")
    print("=" * 80)
    
    # Remaining CVs
    if len(unprocessed_cvs) > max_per_day:
        remaining = len(unprocessed_cvs) - max_per_day
        print(f"\n⚠️ {remaining} CVs remaining. Run again to continue.")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process all CVs using Groq API (FREE)')
    parser.add_argument(
        '--jd',
        type=str,
        required=False,
        default=None,
        help='Job description text (optional - if not provided, only extracts skills/experience without matching)'
    )
    parser.add_argument(
        '--max',
        type=int,
        default=100,
        help='Maximum CVs to process per run (default: 100)'
    )
    
    args = parser.parse_args()
    
    process_all_cvs(
        job_description=args.jd,
        max_per_day=args.max
    )


if __name__ == '__main__':
    main()
