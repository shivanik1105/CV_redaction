"""
Test script for Redis cache functionality.
Run this after deploying to verify cache is working.

Usage:
    python test_redis_cache.py
"""
import sys
import time

def test_redis_connection():
    """Test Redis connection."""
    print("=" * 60)
    print("TEST 1: Redis Connection")
    print("=" * 60)
    
    try:
        from redis_cache import REDIS_AVAILABLE, redis_client
        
        if not REDIS_AVAILABLE:
            print("❌ Redis not available")
            print("   Check REDIS_URL environment variable")
            return False
        
        # Test ping
        redis_client.ping()
        print("✅ Redis connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def test_embedding_cache():
    """Test embedding cache."""
    print("\n" + "=" * 60)
    print("TEST 2: Embedding Cache")
    print("=" * 60)
    
    try:
        from redis_cache import cache_embedding, get_embedding_from_cache
        
        # Test data
        test_text = "Senior Python developer with 5 years experience"
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 77  # 385 dimensions
        
        # Cache embedding
        print(f"Caching embedding for: '{test_text[:50]}...'")
        success = cache_embedding(test_text, test_embedding, ttl_seconds=60)
        
        if not success:
            print("❌ Failed to cache embedding")
            return False
        
        print("✅ Embedding cached successfully")
        
        # Retrieve from cache
        print("Retrieving from cache...")
        cached = get_embedding_from_cache(test_text)
        
        if cached is None:
            print("❌ Failed to retrieve cached embedding")
            return False
        
        if cached != test_embedding:
            print("❌ Cached embedding doesn't match original")
            return False
        
        print("✅ Embedding retrieved successfully")
        print(f"   Dimensions: {len(cached)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding cache test failed: {e}")
        return False


def test_search_cache():
    """Test search results cache."""
    print("\n" + "=" * 60)
    print("TEST 3: Search Results Cache")
    print("=" * 60)
    
    try:
        from redis_cache import cache_search_results, get_search_results_from_cache
        
        # Test data
        test_jd = "Looking for Python developer with Django experience"
        test_results = {
            'success': True,
            'matches': [
                {'anonymized_id': 'CAND_001', 'match_percentage': 85},
                {'anonymized_id': 'CAND_002', 'match_percentage': 78}
            ],
            'total_matches': 2
        }
        
        # Cache results
        print(f"Caching search results for: '{test_jd[:50]}...'")
        success = cache_search_results(test_jd, 10, test_results, ttl_seconds=60)
        
        if not success:
            print("❌ Failed to cache search results")
            return False
        
        print("✅ Search results cached successfully")
        
        # Retrieve from cache
        print("Retrieving from cache...")
        cached = get_search_results_from_cache(test_jd, 10)
        
        if cached is None:
            print("❌ Failed to retrieve cached search results")
            return False
        
        if cached['total_matches'] != test_results['total_matches']:
            print("❌ Cached results don't match original")
            return False
        
        print("✅ Search results retrieved successfully")
        print(f"   Matches: {cached['total_matches']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Search cache test failed: {e}")
        return False


def test_cache_stats():
    """Test cache statistics."""
    print("\n" + "=" * 60)
    print("TEST 4: Cache Statistics")
    print("=" * 60)
    
    try:
        from redis_cache import get_cache_stats
        
        stats = get_cache_stats()
        
        if not stats.get('available'):
            print("❌ Cache not available")
            return False
        
        print("✅ Cache statistics retrieved")
        print(f"   Total keys: {stats.get('total_keys', 0)}")
        print(f"   Embedding keys: {stats.get('embedding_keys', 0)}")
        print(f"   Search keys: {stats.get('search_keys', 0)}")
        print(f"   Cache hits: {stats.get('hits', 0)}")
        print(f"   Cache misses: {stats.get('misses', 0)}")
        print(f"   Hit rate: {stats.get('hit_rate', 0)}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache stats test failed: {e}")
        return False


def test_cache_invalidation():
    """Test cache invalidation."""
    print("\n" + "=" * 60)
    print("TEST 5: Cache Invalidation")
    print("=" * 60)
    
    try:
        from redis_cache import (
            cache_search_results,
            get_search_results_from_cache,
            invalidate_search_cache
        )
        
        # Cache some search results
        test_jd = "Test job description for invalidation"
        test_results = {'success': True, 'matches': []}
        
        print("Caching test search results...")
        cache_search_results(test_jd, 10, test_results, ttl_seconds=60)
        
        # Verify cached
        cached = get_search_results_from_cache(test_jd, 10)
        if cached is None:
            print("❌ Failed to cache results for invalidation test")
            return False
        
        print("✅ Results cached")
        
        # Invalidate
        print("Invalidating search cache...")
        deleted = invalidate_search_cache()
        print(f"✅ Invalidated {deleted} cache entries")
        
        # Verify invalidated
        cached = get_search_results_from_cache(test_jd, 10)
        if cached is not None:
            print("❌ Cache not properly invalidated")
            return False
        
        print("✅ Cache invalidation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache invalidation test failed: {e}")
        return False


def test_performance():
    """Test cache performance."""
    print("\n" + "=" * 60)
    print("TEST 6: Cache Performance")
    print("=" * 60)
    
    try:
        from redis_cache import cache_embedding, get_embedding_from_cache
        
        test_text = "Performance test embedding"
        test_embedding = [0.1] * 384
        
        # Test cache write speed
        start = time.time()
        for i in range(10):
            cache_embedding(f"{test_text}_{i}", test_embedding, ttl_seconds=60)
        write_time = (time.time() - start) * 1000  # ms
        
        print(f"✅ Cache write: {write_time:.2f}ms for 10 embeddings")
        print(f"   Average: {write_time/10:.2f}ms per embedding")
        
        # Test cache read speed
        start = time.time()
        for i in range(10):
            get_embedding_from_cache(f"{test_text}_{i}")
        read_time = (time.time() - start) * 1000  # ms
        
        print(f"✅ Cache read: {read_time:.2f}ms for 10 embeddings")
        print(f"   Average: {read_time/10:.2f}ms per embedding")
        
        if read_time / 10 > 10:  # Should be <10ms per read
            print("⚠️  Warning: Cache reads slower than expected")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("REDIS CACHE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Embedding Cache", test_embedding_cache),
        ("Search Cache", test_search_cache),
        ("Cache Statistics", test_cache_stats),
        ("Cache Invalidation", test_cache_invalidation),
        ("Cache Performance", test_performance)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Redis cache is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

