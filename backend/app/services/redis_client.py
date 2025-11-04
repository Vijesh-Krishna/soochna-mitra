import os
import json
import time
from upstash_redis import Redis

# Load environment variables
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

# Initialize Upstash Redis client
redis_client = None
if UPSTASH_URL and UPSTASH_TOKEN:
    try:
        redis_client = Redis(url=UPSTASH_URL, token=UPSTASH_TOKEN)
        print("Connected to Upstash Redis successfully.")
    except Exception as e:
        print(f"Redis initialization failed: {e}")
else:
    print("Redis URL or Token missing, using fallback cache only.")

# Local fallback cache (valid for 10 minutes)
_fallback_cache = {}

def fallback_get(key: str):
    """Get value from local fallback cache."""
    entry = _fallback_cache.get(key)
    if entry and time.time() - entry["time"] < 600:  # 10 min TTL
        return entry["value"]
    return None

def fallback_set(key: str, value):
    """Store value in local fallback cache."""
    _fallback_cache[key] = {"value": value, "time": time.time()}

# Redis helper functions
def redis_get(key: str):
    """Get a value from Redis if available; fallback otherwise."""
    if redis_client:
        try:
            value = redis_client.get(key)
            if value is not None:
                print(f"Redis cache hit for key: {key}")
                try:
                    return json.loads(value)
                except Exception:
                    return value
            else:
                print(f"Redis miss for key: {key}")
        except Exception as e:
            print(f"Redis get() failed: {e}")
    # fallback
    return fallback_get(key)


def redis_set(key: str, value, ttl: int = 3600):
    """Set a value in Redis (1 hour TTL by default) with fallback."""
    if redis_client:
        try:
            redis_client.set(key, json.dumps(value), ex=ttl)
            print(f"Redis cache stored for key: {key}")
            return
        except Exception as e:
            print(f"Redis set() failed: {e}")
    else:
        print("Redis unavailable, using fallback cache.")
    fallback_set(key, value)
