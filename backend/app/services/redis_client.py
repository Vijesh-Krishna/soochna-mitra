import os, json, time, requests

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

# Local fallback cache (10 mins)
_fallback_cache = {}

def fallback_get(key):
    entry = _fallback_cache.get(key)
    if entry and time.time() - entry["time"] < 600:
        return entry["value"]
    return None

def fallback_set(key, value):
    _fallback_cache[key] = {"value": value, "time": time.time()}

# --- Upstash REST API Helpers ---
def redis_get(key):
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        print("Redis URL or Token missing, using fallback cache only.")
        return None
    try:
        r = requests.get(f"{UPSTASH_URL}/get/{key}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
        if r.status_code == 200:
            data = r.json()
            value = data.get("result")
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
        return None
    except Exception as e:
        print(f"Redis get() failed: {e}")
        return None


def redis_set(key, value, ttl=3600):
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        print("Redis URL or Token missing, skipping remote cache.")
        return
    try:
        payload = json.dumps(value)
        r = requests.post(
            f"{UPSTASH_URL}/set/{key}",
            params={"EX": ttl},
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"},
            data=payload
        )
        if r.status_code != 200:
            print(f"Redis set() non-200: {r.status_code}")
    except Exception as e:
        print(f"Redis set() failed: {e}")
