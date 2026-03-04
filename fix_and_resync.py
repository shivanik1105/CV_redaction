"""
Fix and re-sync all existing intelligence data to Supabase.
- Fixes overall_summary (uses accurate builder instead of raw CV text)
- Populates cv_filename_mapping (was empty because web UI never stored it)
- Skips error records and duplicates (keeps newest version)
- Uses the improved store_intelligence that builds accurate summaries

Run: python fix_and_resync.py
"""
import dns_fix  # Must be first
from dotenv import load_dotenv
load_dotenv()

import os
import json
import glob
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from supabase_storage import SupabaseStorage


def fix_and_resync():
    """Re-sync all valid intelligence files to Supabase with fixed summaries + filename mappings."""
    
    print("\n" + "=" * 60)
    print(" Fix & Re-Sync Intelligence Data to Supabase")
    print("=" * 60 + "\n")
    
    storage = SupabaseStorage()
    
    intelligence_dir = "llm_analysis"
    files = sorted(glob.glob(os.path.join(intelligence_dir, "*_intelligence.json")))
    
    logger.info(f"Found {len(files)} intelligence files\n")
    
    synced = 0
    mapped = 0
    skipped = 0
    errors = 0
    seen_ids = set()
    
    # Process newest first so we keep the latest version of each candidate
    for filepath in reversed(files):
        filename = os.path.basename(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Skip files with errors
            if data.get('error') and not data.get('verdict'):
                logger.info(f"  SKIP (error): {filename}")
                skipped += 1
                continue
            
            anon_id = data.get('anonymized_id')
            if not anon_id:
                logger.info(f"  SKIP (no ID): {filename}")
                skipped += 1
                continue
            
            # Skip duplicates (we already have a newer version)
            if anon_id in seen_ids:
                logger.info(f"  SKIP (duplicate {anon_id}): {filename}")
                skipped += 1
                continue
            
            seen_ids.add(anon_id)
            
            # Re-sync to Supabase (uses fixed _build_accurate_summary)
            result = storage.store_intelligence(data)
            logger.info(f"  SYNCED: {anon_id}")
            synced += 1
            
            # Store filename mapping (this was missing!)
            orig_filename = data.get('original_filename', '')
            if orig_filename and anon_id:
                try:
                    storage.store_filename_mapping(
                        anonymized_id=anon_id,
                        original_filename=orig_filename,
                        anonymized_filename=orig_filename
                    )
                    logger.info(f"  MAPPED: {anon_id} -> {orig_filename}")
                    mapped += 1
                except Exception as me:
                    logger.warning(f"  MAPPING FAILED for {anon_id}: {me}")
        
        except Exception as e:
            logger.error(f"  FAIL: {filename} -> {e}")
            errors += 1
    
    print("\n" + "=" * 60)
    print(" Re-Sync Complete!")
    print("=" * 60)
    print(f"\n  Intelligence records synced: {synced}")
    print(f"  Filename mappings created:  {mapped}")
    print(f"  Skipped:                    {skipped}")
    print(f"  Errors:                     {errors}")
    
    # Verify the results
    print("\n" + "-" * 60)
    print(" Verification")
    print("-" * 60 + "\n")
    
    try:
        all_records = storage.get_all_candidates(limit=100)
        print(f"  cv_intelligence table: {len(all_records)} records")
        for rec in all_records:
            aid = rec.get('anonymized_id', '?')
            verdict = rec.get('verdict', '?')
            conf = rec.get('confidence_score', 0)
            skills = rec.get('key_skills', []) or []
            summary = (rec.get('overall_summary') or '')[:80]
            print(f"    {aid}: {verdict} conf={conf} skills={len(skills)} summary=\"{summary}...\"")
    except Exception as e:
        logger.error(f"  Verification of cv_intelligence failed: {e}")
    
    print()
    try:
        mappings = storage.client.table("cv_filename_mapping").select("*").execute()
        print(f"  cv_filename_mapping table: {len(mappings.data)} records")
        for m in mappings.data:
            print(f"    {m.get('anonymized_id')} -> {m.get('original_filename', '?')[:50]}")
    except Exception as e:
        logger.error(f"  Verification of cv_filename_mapping failed: {e}")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    fix_and_resync()
