"""
Redis caching layer for embeddings and search results.
Reduces API calls and improves response times.
"""
import os
import json
import hashlib
import logging
from typing import Optional, Any, List
import redis

logger = logging.getLogger(__name__)

# Initialize Redis client
try:
    REDIS_URL = os.getenv('REDIS_URL')
    if REDIS_URL:
        redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Test connection
        redis_client.ping()
        REDIS_AVAILABLE = True
        logger.info("✓ Redis cache connected")
    else:
        redis_client = None
        REDIS_AVAILABLE = False
        logger.warning("Redis URL not configured - caching disabled")
except Exception as e:
    redis_client = None
    REDIS_AVAILABLE = False
    logger.warning(f"Redis connection failed - caching disabled: {e}")


def get_cache_key(prefix: str, text: str, max_length: int = 16) -> str:
    """
    Generate cache key from text using SHA256 hash.
    
    Args:
        prefix: Key prefix (e.g., 'emb', 'search')
        text: Text to hash
        max_length: Hash length (default: 16 chars)
        
    Returns:
        Cache key string
    """
    text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:max_length]
    return f"{prefix}:{text_hash}"


def get_embedding_from_cache(text: str) -> Optional[List[float]]:
    """
    Get embedding from Redis cache.
    
    Args:
        text: Text that was embedded
        
    Returns:
        Embedding vector or None if not cached
    """
    if not REDIS_AVAILABLE or not redis_client:
        return None
    
    try:
        cache_key = get_cache_key('emb', text)
        cached = redis_client.get(cache_key)
        
        if cached:
            logger.debug(f"✓ Embedding cache hit: {cache_key}")
            return json.loads(cached)
        
        return None
        
    except Exception as e:
        logger.warning(f"Redis get error: {e}")
        return None


def cache_embedding(text: str, embedding: List[float], ttl_seconds: int = 604800) -> bool:
    """
    Cache embedding in Redis with 7-day TTL.
    
    Args:
        text: Text that was embedded
        embedding: Embedding vector
        ttl_seconds: Time to live (default: 7 days)
        
    Returns:
        True if cached successfully
    """
    if not REDIS_AVAILABLE or not redis_client:
        return False
    
    try:
        cache_key = get_cache_key('emb', text)
        redis_client.setex(
            cache_key,
            ttl_seconds,
            json.dumps(embedding)
        )
        logger.debug(f"✓ Cached embedding: {cache_key}")
        return True
        
    except Exception as e:
        logger.warning(f"Redis set error: {e}")
        return False


def get_search_results_from_cache(job_description: str, limit: int) -> Optional[dict]:
    """
    Get search results from Redis cache.
    
    Args:
        job_description: Job description text
        limit: Result limit
        
    Returns:
        Search results dict or None if not cached
    """
    if not REDIS_AVAILABLE or not redis_client:
        return None
    
    try:
        # Include limit in cache key
        cache_text = f"{job_description}:{limit}"
        cache_key = get_cache_key('search', cache_text, max_length=12)
        cached = redis_client.get(cache_key)
        
        if cached:
            logger.info(f"✓ Search cache hit: {cache_key}")
            return json.loads(cached)
        
        return None
        
    except Exception as e:
        logger.warning(f"Redis get error: {e}")
        return None


def cache_search_results(
    job_description: str,
    limit: int,
    results: dict,
    ttl_seconds: int = 300
) -> bool:
    """
    Cache search results in Redis with 5-minute TTL.
    
    Args:
        job_description: Job description text
        limit: Result limit
        results: Search results dict
        ttl_seconds: Time to live (default: 5 minutes)
        
    Returns:
        True if cached successfully
    """
    if not REDIS_AVAILABLE or not redis_client:
        return False
    
    try:
        cache_text = f"{job_description}:{limit}"
        cache_key = get_cache_key('search', cache_text, max_length=12)
        redis_client.setex(
            cache_key,
            ttl_seconds,
            json.dumps(results)
        )
        logger.info(f"✓ Cached search results: {cache_key}")
        return True
        
    except Exception as e:
        logger.warning(f"Redis set error: {e}")
        return False


def invalidate_search_cache() -> int:
    """
    Invalidate all search result caches.
    Call this when new candidates are added.
    
    Returns:
        Number of keys deleted
    """
    if not REDIS_AVAILABLE or not redis_client:
        return 0
    
    try:
        # Find all search cache keys
        keys = redis_client.keys('search:*')
        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"✓ Invalidated {deleted} search cache entries")
            return deleted
        return 0
        
    except Exception as e:
        logger.warning(f"Redis delete error: {e}")
        return 0


def get_cache_stats() -> dict:
    """
    Get Redis cache statistics.
    
    Returns:
        Dict with cache stats
    """
    if not REDIS_AVAILABLE or not redis_client:
        return {
            'available': False,
            'error': 'Redis not configured'
        }
    
    try:
        info = redis_client.info('stats')
        
        # Count keys by prefix
        emb_keys = len(redis_client.keys('emb:*'))
        search_keys = len(redis_client.keys('search:*'))
        
        return {
            'available': True,
            'total_keys': redis_client.dbsize(),
            'embedding_keys': emb_keys,
            'search_keys': search_keys,
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'hit_rate': round(
                info.get('keyspace_hits', 0) / 
                max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100,
                2
            )
        }
        
    except Exception as e:
        return {
            'available': False,
            'error': str(e)
        }


def clear_all_cache() -> bool:
    """
    Clear all cache entries (use with caution!).
    
    Returns:
        True if successful
    """
    if not REDIS_AVAILABLE or not redis_client:
        return False
    
    try:
        redis_client.flushdb()
        logger.warning("⚠️ Cleared all Redis cache")
        return True
        
    except Exception as e:
        logger.error(f"Redis flush error: {e}")
        return False
