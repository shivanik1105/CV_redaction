"""
Smart CV Processing - Process All CVs with Free Tier Optimization
Handles rate limits, uses triage, and provides progress tracking
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from universal_pipeline_engine import PipelineOrchestrator
from cv_intelligence_extractor import CVIntelligenceExtractor, is_cv_anonymized
from enhanced_triage import EnhancedTriageEngine
from supabase_storage import SupabaseStorage


def process_all_cvs(
    job_description: str,
    samples_dirs: list = None,
    use_triage: bool = True,
    max_per_day: int = 100  # Increased default to process all at once
):
    """
    Process all CVs from samples folder with smart rate limiting
    
    Args:
        job_description: Job description for analysis
        samples_dirs: List of directories to scan (default: ['samples', 'samples/more'])
        use_triage: Enable pre-filtering (default: True)
        max_per_day: Maximum CVs to process per run (default: 50 for free tier)
    """
    print("=" * 80)
    print("Smart CV Processing - Free Tier Optimized")
    print("=" * 80)
    print(f"Job Description: {job_description[:100]}...")
    print(f"Triage: {'Enabled' if use_triage else 'Disabled'}")
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
    
    print(f"Found {len(all_cvs)} CVs in samples folder")
    
    # Check which are already processed
    intelligence_dir = Path('llm_analysis')
    processed_files = set()
    for json_file in intelligence_dir.glob('*_intelligence.json'):
        # Extract original filename from intelligence file
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            orig_file = data.get('original_filename_raw', '')
            if orig_file:
                processed_files.add(orig_file)
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
    orchestrator = PipelineOrchestrator(config_dir='config')
    extractor = CVIntelligenceExtractor(api_provider='gemini')
    triage = EnhancedTriageEngine() if use_triage else None
    storage = SupabaseStorage()
    
    # Process CVs
    stats = {
        'total': len(cvs_to_process),
        'redacted': 0,
        'triage_rejected': 0,
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
            stats['redacted'] += 1
            print(f"     ✓ Redacted: {redacted_filename}")
            
            # Verify anonymization
            if not is_cv_anonymized(redacted_text):
                print(f"     ✗ Not properly anonymized (skipping)")
                stats['failed'] += 1
                continue
            
            # Step 2: Triage (if enabled)
            if use_triage and triage:
                print("  2. Pre-filtering with triage...")
                should_process, reason, relevance_score = triage.should_process(
                    redacted_text, job_description
                )
                match_pct = relevance_score * 100
                
                if not should_process:
                    print(f"     ⚡ Rejected by triage ({match_pct:.1f}% match)")
                    print(f"     Reason: {reason[:100]}...")
                    stats['triage_rejected'] += 1
                    
                    # Save lightweight intelligence for rejected CVs
                    intelligence = {
                        'anonymized_id': f"CAND_{hash(cv_name) % 1000:03d}",
                        'verdict': 'REJECT',
                        'confidence_score': 95,
                        'match_score': int(match_pct),
                        'verdict_reason': f"Pre-filtered by triage: {reason}",
                        'years_experience': 0,
                        'seniority_level': 'UNKNOWN',
                        'core_technical_skills': [],
                        'primary_domain': 'Unknown',
                        'triage_filtered': True,
                        'original_filename_raw': cv_name
                    }
                    
                    intel_filename = f"{Path(redacted_filename).stem}_intelligence.json"
                    intel_path = intelligence_dir / intel_filename
                    with open(intel_path, 'w', encoding='utf-8') as f:
                        json.dump(intelligence, f, indent=2, ensure_ascii=False)
                    
                    continue
                else:
                    print(f"     ✓ Passed triage ({match_pct:.1f}% match)")
            
            # Step 3: LLM Analysis
            print("  3. Analyzing with LLM...")
            # Rate limit: 6 seconds between calls = 10 RPM
            if idx > 1:
                time.sleep(6)
            
            intelligence = extractor.extract_intelligence(
                redacted_text, job_description, redacted_filename
            )
            
            if intelligence.get("error") == "CV_NOT_ANONYMIZED":
                print(f"     ✗ CV not anonymized")
                stats['failed'] += 1
                continue
            
            stats['llm_analyzed'] += 1
            print(f"     ✓ Analyzed: {intelligence.get('anonymized_id')}")
            print(f"     Verdict: {intelligence.get('verdict')} ({intelligence.get('confidence_score')}%)")
            
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
                        original_filename=redacted_filename,
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
    print(f"Triage rejected: {stats['triage_rejected']} ({stats['triage_rejected']/stats['total']*100:.1f}% API savings)")
    print(f"LLM analyzed: {stats['llm_analyzed']}")
    print(f"Stored in Supabase: {stats['stored_supabase']}")
    print(f"Failed: {stats['failed']}")
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Avg time per CV: {elapsed/stats['total']:.1f} seconds")
    print("=" * 80)
    
    # Remaining CVs
    if len(unprocessed_cvs) > max_per_day:
        remaining = len(unprocessed_cvs) - max_per_day
        print(f"\n⚠️ {remaining} CVs remaining. Run again tomorrow to continue.")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process all CVs with smart rate limiting')
    parser.add_argument(
        '--jd',
        type=str,
        required=True,
        help='Job description text'
    )
    parser.add_argument(
        '--max',
        type=int,
        default=50,
        help='Maximum CVs to process per run (default: 50)'
    )
    parser.add_argument(
        '--no-triage',
        action='store_true',
        help='Disable triage pre-filtering'
    )
    
    args = parser.parse_args()
    
    process_all_cvs(
        job_description=args.jd,
        use_triage=not args.no_triage,
        max_per_day=args.max
    )


if __name__ == '__main__':
    main()
