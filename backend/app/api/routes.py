from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from app.services.data_fetcher import fetch_dataset
from app.services.etl_worker import run_etl_once
from app.services.redis_client import redis_get, redis_set, fallback_get, fallback_set


router = APIRouter()


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
    cache_key = "states:list"

    if cached := redis_get(cache_key):
        return {"states": cached, "source": "cache"}

    if f := fallback_get(cache_key):
        return {"states": f, "source": "memory"}

    records = fetch_dataset(limit=5000)
    if not records:
        raise HTTPException(status_code=404, detail="No data found")

    states = sorted({r.get("state_name") for r in records if r.get("state_name")})
    redis_set(cache_key, states, ttl=86400)
    fallback_set(cache_key, states)

    return {"states": states, "source": "live"}


# ---------- DISTRICTS ----------
@router.get("/api/v1/districts")
def list_districts(state: str = Query(..., min_length=2)):
    cache_key = f"districts:{state.upper()}"

    if cached := redis_get(cache_key):
        return {"state": state, "districts": cached, "source": "cache"}

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
    redis_set(cache_key, districts, ttl=86400)
    fallback_set(cache_key, districts)

    return {"state": state, "districts": districts, "source": "live"}


# ---------- DASHBOARD ----------
@router.get("/api/v1/dashboard")
def dashboard(
    state: str = Query(..., min_length=2),
    district: str = Query(..., min_length=2),
    months: int = 12
):
    cache_key = f"dashboard:{state}:{district}:{months}"

    if cached := redis_get(cache_key):
        payload = cached
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

    try:
        filtered = sorted(filtered, key=lambda r: (r.get("fin_year") or "", r.get("month") or ""))
    except Exception:
        pass

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
        series.append({
            "fin_year": fin_year,
            "month": month,
            "expenditure": _safe_float(
                r.get("total_expenditure")
                or r.get("Total_Exp")
                or r.get("Wages")
                or r.get("total_expenditure_in_rs")
                or 0
            ),
            "households": _safe_int(
                r.get("total_households_worked")
                or r.get("Total_Households_Worked")
                or r.get("Total_Households")
                or 0
            ),
            "persondays": _safe_int(
                r.get("persondays")
                or r.get("Persondays_of_Central_Liability_so_far")
                or r.get("Persondays")
                or 0
            ),
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

    redis_set(cache_key, payload, ttl=600)
    fallback_set(cache_key, payload)
    return payload
