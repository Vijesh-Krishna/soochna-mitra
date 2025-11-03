import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.core.config import settings

def get_session_with_retries(total=3, backoff=1.0):
    s = requests.Session()
    retries = Retry(
        total=total,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

def fetch_dataset(state=None, district=None, limit=5000):
    """Fetch dataset from data.gov.in"""
    if not settings.API_KEY or not settings.DATASET_URL:
        print("Missing API_KEY or DATASET_URL in .env")
        return []

    params = {
        "api-key": settings.API_KEY,
        "format": "json",
        "limit": limit,
    }

    try:
        response = get_session_with_retries().get(settings.DATASET_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        records = data.get("records", [])

        if state:
            records = [r for r in records if r.get("state_name", "").strip().upper() == state.upper()]
        if district:
            records = [r for r in records if r.get("district_name", "").strip().upper() == district.upper()]

        print(f"Successfully fetched {len(records)} records from API")
        return records

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return []
