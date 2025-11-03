from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from app.services.data_fetcher import fetch_dataset
from app.services.etl_worker import run_etl_once
from app.core.config import settings
import redis, json, time

router = APIRouter()

# Redis initialization with auto-reconnect + retry logic
def get_redis_client():
    """Safely create a new Redis client with retry."""
    try:
        client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        client.ping()
        print("Redis connected successfully")
        return client
    except Exception as e:
        print(f"Redis unavailable: {e}")
        return None

redis_client = get_redis_client()

def safe_redis_get(key):
    """Safe Redis GET with reconnect fallback"""
    global redis_client
    if not redis_client:
        redis_client = get_redis_client()
        if not redis_client:
            return None
    try:
        return redis_client.get(key)
    except Exception as e:
        print(f"Redis get() failed: {e}")
        redis_client = None
        return None

def safe_redis_setex(key, ttl, value):
    """Safe Redis SETEX with reconnect fallback"""
    global redis_client
    if not redis_client:
        redis_client = get_redis_client()
        if not redis_client:
            return
    try:
        redis_client.setex(key, ttl, value)
    except Exception as e:
        print(f"Redis setex() failed: {e}")
        redis_client = None

# Local in-memory fallback cache
_fallback_cache = {}

def fallback_get(key):
    entry = _fallback_cache.get(key)
    if entry and time.time() - entry["time"] < 600:  # valid for 10 mins
        return entry["value"]
    return None

def fallback_set(key, value):
    _fallback_cache[key] = {"value": value, "time": time.time()}


# ---------- HEALTH ----------
@router.get("/api/v1/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


# ---------- HELPERS ----------
def _safe_float(v):
    try:
        if v is None:
            return 0.0
        if isinstance(v, str):
            v = v.replace(",", "").strip()
        return float(v)
    except Exception:
        return 0.0

def _safe_int(v):
    try:
        if v is None:
            return 0
        if isinstance(v, str):
            v = v.replace(",", "").strip()
        return int(float(v))
    except Exception:
        return 0


# ---------- STATES ----------
@router.get("/api/v1/states")
def list_states():
    """Return list of unique states (cached 24h)"""
    cache_key = "states:list"

    if cached := safe_redis_get(cache_key):
        return {"states": json.loads(cached), "source": "cache"}

    if f := fallback_get(cache_key):
        return {"states": f, "source": "memory"}

    records = fetch_dataset(limit=5000)
    if not records:
        raise HTTPException(status_code=404, detail="No data found")

    states = sorted({r.get("state_name") for r in records if r.get("state_name")})
    safe_redis_setex(cache_key, 86400, json.dumps(states))
    fallback_set(cache_key, states)

    return {"states": states, "source": "live"}


# ---------- DISTRICTS ----------
@router.get("/api/v1/districts")
def list_districts(state: str = Query(..., min_length=2)):
    """Return list of districts for a given state"""
    cache_key = f"districts:{state.upper()}"

    if cached := safe_redis_get(cache_key):
        return {"state": state, "districts": json.loads(cached), "source": "cache"}

    if f := fallback_get(cache_key):
        return {"state": state, "districts": f, "source": "memory"}

    records = fetch_dataset(limit=5000)
    filtered = [
        r for r in records
        if r.get("state_name", "").strip().upper() == state.strip().upper()
    ]

    if not filtered:
        raise HTTPException(status_code=404, detail="No districts found for this state")

    districts = sorted({r.get("district_name") for r in filtered if r.get("district_name")})
    safe_redis_setex(cache_key, 86400, json.dumps(districts))
    fallback_set(cache_key, districts)

    return {"state": state, "districts": districts, "source": "live"}


# ---------- DASHBOARD ----------
@router.get("/api/v1/dashboard")
def dashboard(
    state: str = Query(..., min_length=2),
    district: str = Query(..., min_length=2),
    months: int = 12
):
    """Aggregates and caches dashboard KPIs"""
    cache_key = f"dashboard:{state}:{district}:{months}"

    if cached := safe_redis_get(cache_key):
        payload = json.loads(cached)
        payload["source"] = "cache"
        payload["from_cache"] = True
        return payload

    if f := fallback_get(cache_key):
        payload = f
        payload["source"] = "memory"
        payload["from_cache"] = True
        return payload

    records = fetch_dataset(limit=5000)

    filtered = [
        r for r in records
        if r.get("state_name", "").strip().upper() == state.strip().upper()
        and r.get("district_name", "").strip().upper() == district.strip().upper()
    ]

    if not filtered:
        raise HTTPException(status_code=404, detail="No data for this district/state")

    # Sorting
    try:
        def month_key(r):
            return (r.get("fin_year") or "", r.get("month") or "")
        filtered = sorted(filtered, key=month_key)
    except Exception:
        pass

    # KPI aggregation
    total_exp = sum(
        _safe_float(
            r.get("total_expenditure")
            or r.get("Total_Exp")
            or r.get("Wages")
            or r.get("total_expenditure_in_rs")
            or 0
        ) for r in filtered
    )
    total_households = sum(
        _safe_int(
            r.get("total_households_worked")
            or r.get("Total_Households_Worked")
            or r.get("Total_Households")
            or 0
        ) for r in filtered
    )
    total_persondays = sum(
        _safe_int(
            r.get("persondays")
            or r.get("Persondays_of_Central_Liability_so_far")
            or r.get("Persondays")
            or 0
        ) for r in filtered
    )

    kpis = {
        "total_expenditure": round(total_exp, 2),
        "total_households_worked": total_households,
        "total_persondays": total_persondays,
        "records_count": len(filtered),
    }

    series = []
    for r in filtered:
        fin_year = r.get("fin_year") or r.get("financial_year") or ""
        month = r.get("month") or ""
        expenditure = _safe_float(
            r.get("total_expenditure")
            or r.get("Total_Exp")
            or r.get("Wages")
            or r.get("total_expenditure_in_rs")
            or 0
        )
        households = _safe_int(
            r.get("total_households_worked")
            or r.get("Total_Households_Worked")
            or r.get("Total_Households")
            or 0
        )
        persondays = _safe_int(
            r.get("persondays")
            or r.get("Persondays_of_Central_Liability_so_far")
            or r.get("Persondays")
            or 0
        )
        series.append({
            "fin_year": fin_year,
            "month": month,
            "expenditure": expenditure,
            "households": households,
            "persondays": persondays,
        })

    payload = {
        "state": state,
        "district": district,
        "kpis": kpis,
        "series": series,
        "last_updated": datetime.utcnow().isoformat(),
        "source": "live",
        "from_cache": False
    }

    safe_redis_setex(cache_key, 600, json.dumps(payload))
    fallback_set(cache_key, payload)
    return payload