"""
Weather service — fetches live weather data from OpenWeatherMap API.
"""

import httpx
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

OPENWEATHERMAP_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


async def fetch_weather(city: str) -> dict:
    """
    Fetch current weather for a city from OpenWeatherMap.

    Returns normalized weather data matching WeatherData schema.
    """

    params = {
        "q": city,
        "appid": settings.OWM_API_KEY,
        "units": "metric",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(OPENWEATHERMAP_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

    except httpx.HTTPError as e:
        logger.error(f"Weather API request failed for {city}: {e}")
        return {}

    main = data.get("main", {})
    wind = data.get("wind", {})
    weather = data.get("weather", [{}])[0]

    # Precipitation (rain or snow)
    rain = data.get("rain", {}).get("1h", 0.0)
    snow = data.get("snow", {}).get("1h", 0.0)

    precipitation = rain + snow

    normalized_weather = {
        "temperature": main.get("temp"),
        "humidity": main.get("humidity"),
        "pressure": main.get("pressure"),
        "wind_speed": wind.get("speed", 0) * 3.6,  # convert m/s → km/h
        "wind_direction": wind.get("deg"),
        "precipitation": precipitation,
        "description": weather.get("description"),
        "feels_like": main.get("feels_like"),
        "visibility": data.get("visibility"),
        "lat": data.get("coord", {}).get("lat"),
        "lon": data.get("coord", {}).get("lon"),
    }

    return normalized_weather