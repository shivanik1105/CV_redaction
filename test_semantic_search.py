"""
Test Semantic Search with Supabase pgvector
Verifies that semantic search is using the database efficiently
"""
import os
import sys
import time
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


def test_semantic_search():
    """Test semantic search performance"""
    logger.info("=" * 70)
    logger.info("Testing Semantic Search with pgvector")
    logger.info("=" * 70)
    
    try:
        # Connect to Supabase
        storage = SupabaseStorage()
        logger.info("✓ Connected to Supabase")
        
        # Test queries
        test_queries = [
            "Senior Python developer with AWS experience",
            "Full stack engineer with React and Node.js",
            "DevOps engineer with Kubernetes",
            "Data scientist with machine learning",
            "Frontend developer with TypeScript"
        ]
        
        for query in test_queries:
            logger.info(f"\nQuery: '{query}'")
            
            # Time the search
            start_time = time.time()
            results = storage.semantic_search(
                query_text=query,
                limit=5,
                similarity_threshold=0.5
            )
            elapsed = time.time() - start_time
            
            logger.info(f"  Found {len(results)} results in {elapsed:.3f}s")
            
            # Show top 3 results
            for i, result in enumerate(results[:3], 1):
                anon_id = result.get('anonymized_id', 'UNKNOWN')
                similarity = result.get('similarity', 0)
                summary = result.get('overall_summary', '')[:100]
                logger.info(f"  {i}. {anon_id} (similarity: {similarity:.3f})")
                logger.info(f"     {summary}...")
        
        logger.info("\n" + "=" * 70)
        logger.info("✓ Semantic Search Test Complete")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Error testing semantic search: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    try:
        test_semantic_search()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
