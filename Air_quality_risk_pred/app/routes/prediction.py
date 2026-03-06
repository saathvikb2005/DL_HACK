"""API routes for AQI prediction."""

import logging
import asyncio

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas.prediction import (
    CityPredictionRequest,
    PredictionRequest,
    PredictionResponse,
    WeatherData,
    HistoricalPollutionData,
)
from app.services.prediction_service import predict_aqi
from app.services.waqi_service import fetch_aqi_by_city
from app.services.weather_service import fetch_weather

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["prediction"])


# -----------------------------------------------------------------------
# Simple prediction endpoint
# -----------------------------------------------------------------------
@router.post("/predict/city", response_model=PredictionResponse)
async def predict_by_city(request: CityPredictionRequest):
    """
    Simple endpoint: provide a city name.

    The API automatically fetches:
    - AQI data from WAQI
    - Weather data from OpenWeatherMap

    Then runs the AQI prediction model.
    """

    try:
        # Run both APIs concurrently
        waqi_data, weather_data = await asyncio.gather(
            fetch_aqi_by_city(request.city),
            fetch_weather(request.city),
        )

    except Exception as e:
        logger.exception("Failed to fetch live data for %s", request.city)
        raise HTTPException(status_code=502, detail=f"Failed to fetch live data: {str(e)}")

    if not waqi_data:
        raise HTTPException(status_code=404, detail="AQI data not available for this city")

    current_aqi = min(waqi_data.get("aqi") or 0, 500)

    pollutants = waqi_data.get("pollutants", {})
    waqi_weather = waqi_data.get("weather", {})

    # fallback pollutant values
    pm25_val = pollutants.get("pm25") or current_aqi
    pm10_val = pollutants.get("pm10") or 0

    try:

        pred_request = PredictionRequest(
            location=waqi_data.get("city_name", request.city),
            latitude=waqi_data.get("latitude"),
            longitude=waqi_data.get("longitude"),
            current_aqi=current_aqi,

            weather=WeatherData(
                temperature=weather_data.get("temperature")
                or waqi_weather.get("temperature")
                or 25,

                humidity=weather_data.get("humidity")
                or waqi_weather.get("humidity")
                or 50,

                wind_speed=weather_data.get("wind_speed")
                or (waqi_weather.get("wind_speed") or 0) * 3.6,

                wind_direction=weather_data.get("wind_direction"),

                pressure=weather_data.get("pressure")
                or waqi_weather.get("pressure"),

                precipitation=weather_data.get("precipitation", 0),
            ),

            historical_pollution=HistoricalPollutionData(
                pm25=[pm25_val] * 24,
                pm10=[pm10_val] * 24,

                no2=[pollutants.get("no2", 0)] * 24 if pollutants.get("no2") else [],
                o3=[pollutants.get("o3", 0)] * 24 if pollutants.get("o3") else [],
                so2=[pollutants.get("so2", 0)] * 24 if pollutants.get("so2") else [],
                co=[pollutants.get("co", 0)] * 24 if pollutants.get("co") else [],
            ),
        )

    except Exception as e:
        logger.exception("Failed to build prediction request")
        raise HTTPException(status_code=500, detail=f"Prediction preparation failed: {str(e)}")

    result = predict_aqi(pred_request, waqi_data=waqi_data, weather_data=weather_data)

    return result


# -----------------------------------------------------------------------
# Manual prediction endpoint
# -----------------------------------------------------------------------
@router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Full manual prediction endpoint.

    Allows custom AQI, weather, and historical pollution inputs.
    Useful for testing models or offline predictions.
    """

    try:
        result = predict_aqi(request)
        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Prediction service failed")


# -----------------------------------------------------------------------
# AQI categories endpoint
# -----------------------------------------------------------------------
@router.get("/aqi-categories")
async def aqi_categories():
    """Return AQI category definitions."""

    return [
        {
            "range": f"{low}-{high}",
            "category": category,
            "color": color,
            "description": description,
        }
        for low, high, category, color, description in settings.AQI_BREAKPOINTS
    ]