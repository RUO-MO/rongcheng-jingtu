import requests
import time
import threading
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)
_cache = {}
_cache_lock = threading.RLock()
CACHE_DURATION = 3600

def fetch_aqi_by_location(lat: float, lng: float) -> Optional[int]:
    cache_key = f"{lat:.4f},{lng:.4f}"
    now = time.time()
    
    with _cache_lock:
        if cache_key in _cache:
            cached_value, timestamp = _cache[cache_key]
            if now - timestamp < CACHE_DURATION:
                return cached_value

    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "european_aqi",
        "timezone": "Asia/Shanghai"
    }

    max_retries = 3
    timeout = 15
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            data = resp.json()

            if "current" in data and "european_aqi" in data["current"]:
                aqi = data["current"]["european_aqi"]
                if aqi is not None:
                    aqi_int = int(aqi)
                    with _cache_lock:
                        _cache[cache_key] = (aqi_int, now)
                    return aqi_int
            return None

        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                return None
            time.sleep(2 ** attempt)
        except Exception:
            return None

fetch_aqi = fetch_aqi_by_location