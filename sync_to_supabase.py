"""Sync all local intelligence JSON files to Supabase database"""
import dns_fix  # Must be first - fixes JioFiber DNS
from dotenv import load_dotenv
load_dotenv()

import os
import json
import glob
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from supabase_storage import SupabaseStorage

def sync_all():
    """Push all valid local intelligence JSON files to Supabase"""
    storage = SupabaseStorage()
    
    intelligence_dir = "llm_analysis"
    files = sorted(glob.glob(os.path.join(intelligence_dir, "*_intelligence.json")))
    
    logger.info(f"Found {len(files)} intelligence files to sync")
    
    synced = 0
    skipped = 0
    errors = 0
    seen_ids = set()  # Track anonymized_ids to skip duplicates (keep latest)
    
    # Process in reverse order (newest first) so we keep latest versions
    for filepath in reversed(files):
        filename = os.path.basename(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Skip files with errors and no verdict
            if 'error' in data and not data.get('verdict'):
                logger.info(f"  SKIP (error): {filename}")
                skipped += 1
                continue
            
            # Skip files marked as not anonymized
            if data.get('error') == 'CV_NOT_ANONYMIZED':
                logger.info(f"  SKIP (not anonymized): {filename}")
                skipped += 1
                continue
            
            # Skip files without anonymized_id
            anon_id = data.get('anonymized_id')
            if not anon_id:
                logger.info(f"  SKIP (no ID): {filename}")
                skipped += 1
                continue
            
            # Verify the stored CV text is actually anonymized
            cleaned_text = data.get('cleaned_text', '')
            if cleaned_text and not any(marker in cleaned_text for marker in ['[REDACTED', '[NAME]']):
                logger.warning(f"  SKIP (CV not anonymized): {anon_id}")
                skipped += 1
                continue
            
            # Skip duplicate IDs (we already have a newer version)
            if anon_id in seen_ids:
                logger.info(f"  SKIP (duplicate {anon_id}): {filename}")
                skipped += 1
                continue
            
            seen_ids.add(anon_id)
            
            # Sync to Supabase
            result = storage.store_intelligence(data)
            logger.info(f"  OK: {anon_id} from {filename}")
            synced += 1
            
        except Exception as e:
            logger.error(f"  FAIL: {filename} -> {e}")
            errors += 1
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Sync complete: {synced} synced, {skipped} skipped, {errors} errors")
    logger.info(f"{'='*50}")
    
    # Verify by reading back
    try:
        all_records = storage.get_all_candidates(limit=100)
        logger.info(f"Supabase now has {len(all_records)} records")
        for rec in all_records:
            logger.info(f"  {rec.get('anonymized_id')}: {rec.get('verdict')} (confidence: {rec.get('confidence_score')})")
    except Exception as e:
        logger.error(f"Verification failed: {e}")

if __name__ == "__main__":
    sync_all()
