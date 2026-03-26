"""
Backfill Embeddings Script
Generates embeddings for existing CV intelligence files that don't have embeddings yet
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vector_search import get_vector_search_engine, generate_embedding_for_intelligence

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_intelligence_files(intelligence_dir: str) -> List[Dict]:
    """
    Load all intelligence JSON files
    
    Args:
        intelligence_dir: Directory containing intelligence files
    
    Returns:
        List of intelligence dictionaries
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
            
            data['_filename'] = str(json_file)
            files.append(data)
        
        except Exception as e:
            logger.warning(f"Error loading {json_file}: {e}")
    
    return files


def backfill_embeddings(
    intelligence_dir: str = 'llm_analysis',
    force_regenerate: bool = False,
    batch_size: int = 10
) -> Dict:
    """
    Backfill embeddings for intelligence files
    
    Args:
        intelligence_dir: Directory containing intelligence files
        force_regenerate: Regenerate embeddings even if they exist
        batch_size: Number of files to process in each batch
    
    Returns:
        Statistics dictionary
    """
    logger.info("=" * 70)
    logger.info("Starting Embedding Backfill")
    logger.info("=" * 70)
    
    # Load intelligence files
    logger.info(f"Loading intelligence files from {intelligence_dir}...")
    intelligence_files = load_intelligence_files(intelligence_dir)
    logger.info(f"Found {len(intelligence_files)} intelligence files")
    
    if not intelligence_files:
        logger.warning("No intelligence files found")
        return {'total': 0, 'processed': 0, 'skipped': 0, 'failed': 0}
    
    # Initialize vector search engine
    logger.info("Initializing vector search engine...")
    try:
        engine = get_vector_search_engine()
        logger.info(f"Using {engine.embedding_provider} embeddings ({engine.dimensions} dimensions)")
    except Exception as e:
        logger.error(f"Failed to initialize vector search engine: {e}")
        return {'total': len(intelligence_files), 'processed': 0, 'skipped': 0, 'failed': len(intelligence_files)}
    
    # Process files
    stats = {
        'total': len(intelligence_files),
        'processed': 0,
        'skipped': 0,
        'failed': 0,
        'updated_files': []
    }
    
    for idx, intelligence in enumerate(intelligence_files, 1):
        filename = intelligence.get('_filename')
        anon_id = intelligence.get('anonymized_id', 'UNKNOWN')
        
        logger.info(f"[{idx}/{len(intelligence_files)}] Processing {anon_id}...")
        
        try:
            # Check if embedding already exists
            if 'embedding' in intelligence and not force_regenerate:
                logger.info(f"  Skipping {anon_id} (embedding already exists)")
                stats['skipped'] += 1
                continue
            
            # Generate embedding
            logger.info(f"  Generating embedding for {anon_id}...")
            embedding = generate_embedding_for_intelligence(intelligence)
            
            if not embedding or not engine.validate_embedding(embedding):
                logger.error(f"  Invalid embedding generated for {anon_id}")
                stats['failed'] += 1
                continue
            
            # Add embedding to intelligence data
            intelligence['embedding'] = embedding
            intelligence['embedding_model'] = f"{engine.embedding_provider}:{engine.LOCAL_MODEL if engine.embedding_provider == 'local' else engine.OPENAI_MODEL}"
            intelligence['embedding_dimensions'] = engine.dimensions
            
            # Remove temporary filename field
            del intelligence['_filename']
            
            # Save updated file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(intelligence, f, indent=2, ensure_ascii=False)
            
            logger.info(f"  ✓ Saved embedding for {anon_id}")
            stats['processed'] += 1
            stats['updated_files'].append(filename)
            
            # Optional: Store in Supabase
            try:
                from supabase_storage import SupabaseStorage
                storage = SupabaseStorage()
                storage.store_embedding(anon_id, embedding)
                logger.info(f"  ✓ Stored embedding in Supabase for {anon_id}")
            except Exception as e:
                logger.warning(f"  Could not store in Supabase: {e}")
        
        except Exception as e:
            logger.error(f"  Error processing {anon_id}: {e}")
            stats['failed'] += 1
    
    # Print summary
    logger.info("=" * 70)
    logger.info("Backfill Complete")
    logger.info("=" * 70)
    logger.info(f"Total files: {stats['total']}")
    logger.info(f"Processed: {stats['processed']}")
    logger.info(f"Skipped: {stats['skipped']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Success rate: {stats['processed'] / stats['total'] * 100:.1f}%")
    logger.info("=" * 70)
    
    return stats


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill embeddings for CV intelligence files')
    parser.add_argument(
        '--dir',
        default='llm_analysis',
        help='Directory containing intelligence files (default: llm_analysis)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regenerate embeddings even if they exist'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Batch size for processing (default: 10)'
    )
    
    args = parser.parse_args()
    
    stats = backfill_embeddings(
        intelligence_dir=args.dir,
        force_regenerate=args.force,
        batch_size=args.batch_size
    )
    
    # Exit with error code if any failures
    if stats['failed'] > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
