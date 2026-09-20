"""
api_extractor.py
-----------------
Extract stage for the web-API data source (Open-Meteo current weather —
free, no API key required, good stand-in for any REST JSON API).
Includes retry-with-backoff so transient network errors don't kill
the whole pipeline run.
"""

import time
from datetime import datetime, timezone
from typing import List, Dict, Any

import requests


def extract_weather_api(url: str, logger, max_retries: int = 3) -> List[Dict[str, Any]]:
    logger.info(f"Extracting API source: {url}")

    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            payload = response.json()
            current = payload.get("current", {})

            record = {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "latitude": payload.get("latitude"),
                "longitude": payload.get("longitude"),
                "temperature_c": current.get("temperature_2m"),
                "relative_humidity_pct": current.get("relative_humidity_2m"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
            }
            logger.info(f"Extracted 1 record from API on attempt {attempt}")
            return [record]

        except (requests.RequestException, ValueError) as exc:
            last_exception = exc
            wait = 2 ** attempt
            logger.warning(
                f"API extraction attempt {attempt}/{max_retries} failed: {exc}. "
                f"Retrying in {wait}s..."
            )
            time.sleep(min(wait, 2))  # capped for demo speed

    logger.error(f"API extraction failed after {max_retries} attempts: {last_exception}")
    raise ConnectionError(f"Could not extract data from API: {last_exception}")
