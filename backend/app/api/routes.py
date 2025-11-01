# backend/app/api/routes.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from app.services.data_fetcher import fetch_dataset
from app.services.etl_worker import run_etl_once
from app.core.config import settings
import redis, json

router = APIRouter()

# ✅ Initialize Redis client safely
redis_client = None
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    print("✅ Redis connected successfully")
except Exception as e:
    print(f"⚠️ Redis unavailable, caching disabled: {e}")
    redis_client = None


@router.get("/api/v1/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


def _safe_float(v):
    try:
        if v is None:
            return 0.0
        # Accept strings with commas
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


# ✅ States
@router.get("/api/v1/states")
def list_states():
    """Return list of unique states (cached 24h)"""
    cache_key = "states:list"

    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return {"states": json.loads(cached), "source": "cache"}

    records = fetch_dataset(limit=5000)
    if not records:
        raise HTTPException(status_code=404, detail="No data found")

    states = sorted({r.get("state_name") for r in records if r.get("state_name")})
    if redis_client:
        redis_client.setex(cache_key, 86400, json.dumps(states))
    return {"states": states, "source": "live"}


# ✅ Districts
@router.get("/api/v1/districts")
def list_districts(state: str = Query(..., min_length=2)):
    """Return list of districts for a given state"""
    cache_key = f"districts:{state.upper()}"

    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return {"state": state, "districts": json.loads(cached), "source": "cache"}

    records = fetch_dataset(limit=5000)
    filtered = [
        r for r in records
        if r.get("state_name", "").strip().upper() == state.strip().upper()
    ]

    if not filtered:
        raise HTTPException(status_code=404, detail="No districts found for this state")

    districts = sorted({r.get("district_name") for r in filtered if r.get("district_name")})
    if redis_client:
        redis_client.setex(cache_key, 86400, json.dumps(districts))
    return {"state": state, "districts": districts, "source": "live"}


# ✅ Dashboard
@router.get("/api/v1/dashboard")
def dashboard(state: str = Query(..., min_length=2), district: str = Query(..., min_length=2), months: int = 12):
    """Aggregates and caches dashboard KPIs"""
    cache_key = f"dashboard:{state}:{district}:{months}"

    # Try cache first
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                payload = json.loads(cached)
                payload["source"] = "cache"
                payload["from_cache"] = True
                return payload
        except Exception:
            pass

    records = fetch_dataset(limit=5000)

    filtered = [
        r for r in records
        if r.get("state_name", "").strip().upper() == state.strip().upper()
        and r.get("district_name", "").strip().upper() == district.strip().upper()
    ]

    if not filtered:
        raise HTTPException(status_code=404, detail="No data for this district/state")

    # sort by fin_year & month if possible (attempt to keep chronological)
    try:
        def month_key(r):
            # month may be names like "Dec" — we cannot fully sort correctly without mapping,
            # but we'll return the raw fin_year+month string to get a stable order.
            return (r.get("fin_year") or "", r.get("month") or "")
        filtered = sorted(filtered, key=month_key)
    except Exception:
        pass

    # Aggregate KPIs (use robust key checks)
    total_exp = sum(
        _safe_float(
            r.get("total_expenditure")
            or r.get("Total_Exp")
            or r.get("Wages")
            or r.get("total_expenditure_in_rs")
            or 0
        )
        for r in filtered
    )
    total_households = sum(
        _safe_int(
            r.get("total_households_worked")
            or r.get("Total_Households_Worked")
            or r.get("Total_Households")
            or 0
        )
        for r in filtered
    )
    total_persondays = sum(
        _safe_int(
            r.get("persondays")
            or r.get("Persondays_of_Central_Liability_so_far")
            or r.get("Persondays")
            or 0
        )
        for r in filtered
    )

    kpis = {
        "total_expenditure": round(total_exp, 2),
        "total_households_worked": total_households,
        "total_persondays": total_persondays,
        "records_count": len(filtered),
    }

    # Build normalized series with numeric fields for frontend charts
    series = []
    for r in filtered:
        fin_year = r.get("fin_year") or r.get("financial_year") or ""
        month = r.get("month") or ""
        # get numeric fields with many possible keys
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

    # Cache it for 10 minutes
    if redis_client:
        try:
            redis_client.setex(cache_key, 600, json.dumps(payload))
        except Exception:
            pass

    return payload


# ✅ Refresh Endpoint
@router.post("/api/v1/refresh")
def refresh_data():
    if redis_client:
        try:
            redis_client.flushdb()
        except Exception:
            pass
    run_etl_once(limit=5000)
    return {"message": "ETL refresh complete.", "timestamp": datetime.utcnow().isoformat()}
