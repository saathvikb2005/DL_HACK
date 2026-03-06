"""
WAQI (World Air Quality Index) service — fetches live AQI and pollutant data.
"""

import httpx
import logging
from typing import Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

WAQI_BASE_URL = "https://api.waqi.info/feed"


async def fetch_aqi_by_city(city: str) -> Dict[str, Any]:
    """
    Fetch real-time AQI data for a city from WAQI.

    Returns normalized dictionary containing:
    - AQI value
    - dominant pollutant
    - pollutant sub-indices
    - weather values from WAQI station
    - daily forecast
    - city metadata
    """

    url = f"{WAQI_BASE_URL}/{city}/"
    params = {"token": settings.WAQI_TOKEN}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

    except httpx.HTTPError as e:
        logger.error(f"WAQI API request failed for {city}: {e}")
        return {}

    if data.get("status") != "ok":
        logger.error(f"WAQI API returned error for {city}: {data}")
        return {}

    payload = data["data"]
    iaqi = payload.get("iaqi", {})

    # -------------------------------
    # Extract pollutant values
    # -------------------------------
    pollutants = {
        "pm25": iaqi.get("pm25", {}).get("v"),
        "pm10": iaqi.get("pm10", {}).get("v"),
        "no2": iaqi.get("no2", {}).get("v"),
        "o3": iaqi.get("o3", {}).get("v"),
        "so2": iaqi.get("so2", {}).get("v"),
        "co": iaqi.get("co", {}).get("v"),
    }

    # -------------------------------
    # Extract weather values
    # -------------------------------
    weather = {
        "temperature": iaqi.get("t", {}).get("v"),
        "humidity": iaqi.get("h", {}).get("v"),
        "wind_speed": iaqi.get("w", {}).get("v"),
        "pressure": iaqi.get("p", {}).get("v"),
    }

    # -------------------------------
    # Extract daily forecasts
    # -------------------------------
    forecast_raw = payload.get("forecast", {}).get("daily", {})
    daily_forecast = {}

    for pollutant, entries in forecast_raw.items():
        daily_forecast[pollutant] = [
            {
                "day": entry.get("day"),
                "avg": entry.get("avg"),
                "min": entry.get("min"),
                "max": entry.get("max"),
            }
            for entry in entries
        ]

    # -------------------------------
    # City metadata
    # -------------------------------
    city_info = payload.get("city", {})
    geo = city_info.get("geo", [None, None])

    result = {
        "aqi": payload.get("aqi"),
        "dominant_pollutant": payload.get("dominentpol"),
        "pollutants": pollutants,
        "weather": weather,
        "daily_forecast": daily_forecast,
        "city_name": city_info.get("name", city),
        "latitude": geo[0] if len(geo) > 0 else None,
        "longitude": geo[1] if len(geo) > 1 else None,
        "timestamp": payload.get("time", {}).get("iso"),
    }

    return result