"""
WAQI (World Air Quality Index) service — fetches live AQI and pollutant data.
"""

import httpx
import logging
import random
from typing import Dict, Any, List
from datetime import datetime, timedelta

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


async def fetch_historical_pollution(
    city: str,
    current_pollutants: Dict[str, float],
    days: int = 7
) -> Dict[str, List[float]]:
    """
    Generate historical pollution sequences for LSTM model.
    
    Since WAQI free API doesn't provide historical data, this function
    generates realistic synthetic sequences with a linear trend leading
    to the current value. This creates a smooth, predictable pattern
    that avoids confusing the LSTM model with random noise.
    
    Args:
        city: City name (for logging)
        current_pollutants: Current pollutant concentrations (raw µg/m³, ppb, mg/m³)
        days: Number of historical days to generate (default 7 for LSTM)
        
    Returns:
        Dict with pollutant names as keys, lists of past values as values
        Each list has 'days' values ending with current_value
    """
    sequences = {}
    
    for pollutant, current_val in current_pollutants.items():
        # Allow zero as valid measurement, only treat None or negative as invalid
        if current_val is None or current_val < 0:
            # If no current data, use zeros
            sequences[pollutant] = [0.0] * days
            continue
        
        # Create a linear trend from 90% of current value to current value
        # This simulates a gradual build-up over the past week
        start_val = current_val * 0.90
        
        historical = []
        for i in range(days):
            # Linear interpolation from start_val to current_val
            ratio = i / (days - 1) if days > 1 else 1
            value = start_val + (current_val - start_val) * ratio
            historical.append(round(max(0, value), 2))
        
        sequences[pollutant] = historical
    
    logger.debug(f"Generated {days}-day linear trend sequences for {city}")
    return sequences