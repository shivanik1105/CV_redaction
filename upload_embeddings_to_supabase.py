"""
Upload Existing Embeddings to Supabase
Reads intelligence files with embeddings and uploads them to Supabase
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase_storage import SupabaseStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_intelligence_files(intelligence_dir: str) -> List[Dict]:
    """
    Load all intelligence JSON files that have embeddings
    
    Args:
        intelligence_dir: Directory containing intelligence files
    
    Returns:
        List of intelligence dictionaries with embeddings
    """
    intelligence_dir = Path(intelligence_dir)
    files = []
    
    for json_file in intelligence_dir.glob('*_intelligence.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Skip files with errors
            if 'error' in data and not data.get('verdict'):
                continue
            
            # Only include files that have embeddings
            if 'embedding' in data and data['embedding']:
                data['_filename'] = str(json_file)
                files.append(data)
        
        except Exception as e:
            logger.warning(f"Error loading {json_file}: {e}")
    
    return files


def upload_embeddings_to_supabase(
    intelligence_dir: str = 'llm_analysis',
    force_upload: bool = True
) -> Dict:
    """
    Upload embeddings from intelligence files to Supabase
    
    Args:
        intelligence_dir: Directory containing intelligence files
        force_upload: Upload even if already uploaded
    
    Returns:
        Statistics dictionary
    """
    logger.info("=" * 70)
    logger.info("Uploading Embeddings to Supabase")
    logger.info("=" * 70)
    
    # Load intelligence files with embeddings
    logger.info(f"Loading intelligence files from {intelligence_dir}...")
    intelligence_files = load_intelligence_files(intelligence_dir)
    logger.info(f"Found {len(intelligence_files)} files with embeddings")
    
    if not intelligence_files:
        logger.warning("No intelligence files with embeddings found")
        return {'total': 0, 'uploaded': 0, 'skipped': 0, 'failed': 0}
    
    # Initialize Supabase storage
    logger.info("Connecting to Supabase...")
    try:
        storage = SupabaseStorage()
        logger.info("✓ Connected to Supabase")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return {'total': len(intelligence_files), 'uploaded': 0, 'skipped': 0, 'failed': len(intelligence_files)}
    
    # Upload embeddings
    stats = {
        'total': len(intelligence_files),
        'uploaded': 0,
        'skipped': 0,
        'failed': 0,
        'uploaded_ids': []
    }
    
    for idx, intelligence in enumerate(intelligence_files, 1):
        anon_id = intelligence.get('anonymized_id', 'UNKNOWN')
        embedding = intelligence.get('embedding')
        embedding_model = intelligence.get('embedding_model', 'unknown')
        
        logger.info(f"[{idx}/{len(intelligence_files)}] Uploading {anon_id}...")
        
        try:
            # Upload embedding to Supabase
            success = storage.store_embedding(
                anonymized_id=anon_id,
                embedding=embedding,
                embedding_model=embedding_model
            )
            
            if success:
                logger.info(f"  ✓ Uploaded embedding for {anon_id}")
                stats['uploaded'] += 1
                stats['uploaded_ids'].append(anon_id)
            else:
                logger.warning(f"  ✗ Failed to upload {anon_id} (no record found in database)")
                stats['failed'] += 1
        
        except Exception as e:
            logger.error(f"  ✗ Error uploading {anon_id}: {e}")
            stats['failed'] += 1
    
    # Print summary
    logger.info("=" * 70)
    logger.info("Upload Complete")
    logger.info("=" * 70)
    logger.info(f"Total files: {stats['total']}")
    logger.info(f"Uploaded: {stats['uploaded']}")
    logger.info(f"Skipped: {stats['skipped']}")
    logger.info(f"Failed: {stats['failed']}")
    if stats['uploaded'] > 0:
        logger.info(f"Success rate: {stats['uploaded'] / stats['total'] * 100:.1f}%")
    logger.info("=" * 70)
    
    return stats


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload embeddings to Supabase')
    parser.add_argument(
        '--dir',
        default='llm_analysis',
        help='Directory containing intelligence files (default: llm_analysis)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force upload even if already uploaded'
    )
    
    args = parser.parse_args()
    
    stats = upload_embeddings_to_supabase(
        intelligence_dir=args.dir,
        force_upload=args.force
    )
    
    # Exit with error code if any failures
    if stats['failed'] > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
