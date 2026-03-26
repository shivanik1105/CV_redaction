"""
Verify Embeddings in Supabase
Checks how many records have embeddings stored
"""
import os
import sys
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase_storage import SupabaseStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_embeddings():
    """Verify embeddings in Supabase"""
    logger.info("=" * 70)
    logger.info("Verifying Embeddings in Supabase")
    logger.info("=" * 70)
    
    try:
        # Connect to Supabase
        storage = SupabaseStorage()
        logger.info("✓ Connected to Supabase")
        
        # Count total records
        response = storage.client.table('cv_intelligence').select('anonymized_id', count='exact').execute()
        total_records = response.count
        logger.info(f"Total CV records: {total_records}")
        
        # Count records with embeddings (embedding IS NOT NULL)
        # Note: We can't directly query for NOT NULL in PostgREST easily,
        # so we fetch all and count client-side
        response = storage.client.table('cv_intelligence').select('anonymized_id, embedding').execute()
        records_with_embeddings = sum(1 for r in response.data if r.get('embedding'))
        
        logger.info(f"Records with embeddings: {records_with_embeddings}")
        logger.info(f"Records without embeddings: {total_records - records_with_embeddings}")
        
        if records_with_embeddings > 0:
            percentage = (records_with_embeddings / total_records) * 100
            logger.info(f"Coverage: {percentage:.1f}%")
            
            # Show sample IDs with embeddings
            sample_ids = [r['anonymized_id'] for r in response.data if r.get('embedding')][:5]
            logger.info(f"Sample IDs with embeddings: {', '.join(sample_ids)}")
        
        logger.info("=" * 70)
        logger.info("✓ Verification Complete")
        logger.info("=" * 70)
        
        return {
            'total': total_records,
            'with_embeddings': records_with_embeddings,
            'without_embeddings': total_records - records_with_embeddings,
            'coverage_percent': (records_with_embeddings / total_records * 100) if total_records > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error verifying embeddings: {e}")
        raise


if __name__ == '__main__':
    try:
        stats = verify_embeddings()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)
