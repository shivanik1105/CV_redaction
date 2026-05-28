import redis
import os

# Try to connect to Redis and clear search cache
try:
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        print("REDIS_URL not set, skipping cache clear")
    else:
        r = redis.from_url(redis_url, decode_responses=True)
        # Get all keys matching search cache pattern
        pattern = "*search_results*"
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
            print(f"Cleared {len(keys)} cached search results")
        else:
            print("No cached search results found")
except Exception as e:
    print(f"Failed to connect to Redis: {e}")
    print("Redis cache may be disabled")
