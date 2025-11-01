import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.core.config import API_KEY, DATASET_URL


# Setup retry logic to handle temporary network issues
def get_session_with_retries():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,            # retry 3 times
        backoff_factor=1,   # wait 1s, 2s, 4s
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    return session

def fetch_gov_data(limit=5):
    session = get_session_with_retries()
    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": limit
    }

    headers = {"User-Agent": "SoochnaMitra/1.0", "Accept": "application/json"}

    try:
        response = session.get(DATASET_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return {"status": "success", "data": response.json()}
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 403:
            return {"status": "error", "message": "Access denied (403). Check your API key or dataset permissions."}
        return {"status": "error", "message": f"HTTP error occurred: {http_err}"}
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "The request timed out. Please try again later."}
    except Exception as err:
        return {"status": "error", "message": f"Unexpected error: {err}"}
