"""API routes for AQI prediction."""

import logging
import asyncio
import os
import sys

from fastapi import APIRouter, HTTPException, Request

from app.config import settings

# Add project root for module_bridge
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
try:
    from module_bridge import push_event as _push_event
except ImportError:
    def _push_event(*a, **k): pass
from app.schemas.prediction import (
    CityPredictionRequest,
    PredictionRequest,
    PredictionResponse,
    WeatherData,
    HistoricalPollutionData,
)
from app.services.prediction_service import predict_aqi
from app.services.waqi_service import fetch_aqi_by_city, fetch_historical_pollution
from app.services.weather_service import fetch_weather
from app.services.location_service import detect_location_from_ip
from app.utils.aqi_converter import convert_pollutants

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["prediction"])


# -----------------------------------------------------------------------
# Auto-location prediction endpoint
# -----------------------------------------------------------------------
@router.get("/predict/auto", response_model=PredictionResponse)
async def predict_auto_location(request: Request):
    """
    Auto-detect location from IP and predict AQI.

    The API automatically:
    1. Detects your location from IP address
    2. Fetches AQI data from WAQI
    3. Fetches weather data from OpenWeatherMap
    4. Runs the AQI prediction model
    5. Generates dynamic response based on conditions

    No input required - fully automatic!
    """

    # Step 1: Detect location from IP (pass Request for client IP extraction)
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() \
                or request.headers.get("X-Real-IP") \
                or (request.client.host if request.client else None)
    location_data = await detect_location_from_ip(client_ip=client_ip)
    
    if not location_data or not location_data.get("city"):
        raise HTTPException(
            status_code=503,
            detail="Could not detect your location. Please use /predict/city endpoint with a city name instead."
        )
    
    detected_city = location_data["city"]
    logger.info(f"Auto-detected location: {detected_city}")

    try:
        # Step 2 & 3: Run both APIs concurrently
        waqi_data, weather_data = await asyncio.gather(
            fetch_aqi_by_city(detected_city),
            fetch_weather(detected_city),
        )

    except Exception as e:
        logger.exception("Failed to fetch live data for %s", detected_city)
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch live data for {detected_city}: {str(e)}"
        )

    if not waqi_data:
        raise HTTPException(
            status_code=404,
            detail=f"AQI data not available for {detected_city}"
        )

    current_aqi = waqi_data.get("aqi")
    if current_aqi is None or current_aqi <= 0:
        raise HTTPException(
            status_code=502,
            detail=f"Invalid AQI data received for {detected_city}"
        )
    
    current_aqi = min(current_aqi, 500)

    # Get WAQI pollutant sub-indices (0-500 scale)
    waqi_pollutants = waqi_data.get("pollutants", {})
    waqi_weather = waqi_data.get("weather", {})

    # Convert AQI sub-indices to raw concentrations (µg/m³, ppb, mg/m³)
    logger.info(f"Converting WAQI sub-indices to raw concentrations for {detected_city}")
    raw_concentrations = convert_pollutants(waqi_pollutants)
    logger.debug(f"Raw concentrations: {raw_concentrations}")

    # Validate we have at least PM2.5 data
    if not raw_concentrations.get("pm25") or raw_concentrations["pm25"] <= 0:
        # Fallback: use current AQI to estimate PM2.5 concentration
        if current_aqi <= 50:
            raw_concentrations["pm25"] = current_aqi * 0.24
        elif current_aqi <= 100:
            raw_concentrations["pm25"] = 12 + (current_aqi - 50) * 0.46
        else:
            raw_concentrations["pm25"] = 35 + (current_aqi - 100) * 0.40
        logger.warning(f"Using AQI-based PM2.5 estimate: {raw_concentrations['pm25']:.1f} µg/m³")

    # Generate realistic historical pollution sequences (7 days for LSTM)
    historical_sequences = await fetch_historical_pollution(
        detected_city,
        raw_concentrations,
        days=7
    )

    # Validate weather data
    temperature = weather_data.get("temperature") or waqi_weather.get("temperature")
    humidity = weather_data.get("humidity") or waqi_weather.get("humidity")
    
    if temperature is None:
        raise HTTPException(
            status_code=502,
            detail=f"Temperature data unavailable for {detected_city}. Cannot generate reliable prediction."
        )
    
    if humidity is None:
        raise HTTPException(
            status_code=502,
            detail=f"Humidity data unavailable for {detected_city}. Cannot generate reliable prediction."
        )

    # Build weather data with validation
    wind_speed = weather_data.get("wind_speed")
    if wind_speed is None:
        wind_speed = waqi_weather.get("wind_speed")
        if wind_speed is not None:
            wind_speed = wind_speed * 3.6  # m/s to km/h
    
    if wind_speed is None:
        raise HTTPException(
            status_code=502,
            detail=f"Wind speed data unavailable for {detected_city}. Cannot generate reliable prediction."
        )

    pressure = weather_data.get("pressure") or waqi_weather.get("pressure")
    if pressure is None:
        raise HTTPException(
            status_code=502,
            detail=f"Atmospheric pressure data unavailable for {detected_city}. Cannot generate reliable prediction."
        )

    try:
        pred_request = PredictionRequest(
            location=waqi_data.get("city_name", detected_city),
            latitude=waqi_data.get("latitude") or location_data.get("latitude"),
            longitude=waqi_data.get("longitude") or location_data.get("longitude"),
            current_aqi=current_aqi,

            weather=WeatherData(
                temperature=temperature,
                humidity=humidity,
                wind_speed=wind_speed,
                wind_direction=weather_data.get("wind_direction"),
                pressure=pressure,
                precipitation=weather_data.get("precipitation") or 0.0,
            ),

            historical_pollution=HistoricalPollutionData(
                pm25=historical_sequences.get("pm25", []),
                pm10=historical_sequences.get("pm10", []),
                no2=historical_sequences.get("no2", []),
                o3=historical_sequences.get("o3", []),
                so2=historical_sequences.get("so2", []),
                co=historical_sequences.get("co", []),
            ),
        )

    except Exception as e:
        logger.exception("Failed to build prediction request")
        raise HTTPException(status_code=500, detail=f"Prediction preparation failed: {str(e)}")

    result = predict_aqi(pred_request, waqi_data=waqi_data, weather_data=weather_data)

    # Push event to orchestrator with dynamic message based on conditions
    try:
        predicted_aqi = result.hourly_forecast[23].predicted_aqi if result.hourly_forecast else current_aqi
        
        if predicted_aqi > 100:
            # Get category info for dynamic messaging
            from app.config import get_aqi_category
            category_info = get_aqi_category(predicted_aqi)
            
            # Build dynamic message based on AQI level and weather
            if predicted_aqi <= 150:
                severity = "moderately poor"
                base_action = "Sensitive individuals should limit outdoor activities"
            elif predicted_aqi <= 200:
                severity = "unhealthy"
                base_action = "Everyone should reduce prolonged outdoor exertion"
            elif predicted_aqi <= 300:
                severity = "very unhealthy"
                base_action = "Avoid outdoor activities and wear N95 masks if going outside"
            else:
                severity = "hazardous"
                base_action = "Stay indoors, seal windows, and run air purifiers"
            
            # Add weather-specific advice
            weather_advice = []
            if temperature > 30:
                weather_advice.append("High temperature increases health risks")
            if humidity > 80:
                weather_advice.append("High humidity makes breathing more difficult")
            if wind_speed < 5:
                weather_advice.append("Low wind speed means pollutants are not dispersing")
            elif wind_speed > 30:
                weather_advice.append("Strong winds may stir up dust and particles")
            
            combined_action = base_action
            if weather_advice:
                combined_action += ". Note: " + "; ".join(weather_advice)
            
            _push_event("POOR_AIR_QUALITY", "air_quality", {
                "aqi": predicted_aqi,
                "city": waqi_data.get("city_name", detected_city),
                "category": category_info["category"],
                "risk_level": result.health_risk_level,
                "severity": severity,
                "recommended_action": combined_action,
                "temperature": temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
            })
    except Exception as e:
        logger.exception("Failed to push POOR_AIR_QUALITY event for %s: %s", detected_city, str(e))

    return result


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
        raise HTTPException(status_code=404, detail=f"AQI data not available for {request.city}")

    current_aqi = waqi_data.get("aqi")
    if current_aqi is None or current_aqi <= 0:
        raise HTTPException(status_code=502, detail=f"Invalid AQI data received for {request.city}")
    
    current_aqi = min(current_aqi, 500)

    # Get WAQI pollutant sub-indices (0-500 scale)
    waqi_pollutants = waqi_data.get("pollutants", {})
    waqi_weather = waqi_data.get("weather", {})

    # Convert AQI sub-indices to raw concentrations (µg/m³, ppb, ppm)
    logger.info(f"Converting WAQI sub-indices to raw concentrations for {request.city}")
    raw_concentrations = convert_pollutants(waqi_pollutants)
    logger.debug(f"Raw concentrations: {raw_concentrations}")

    # Validate we have at least PM2.5 data
    if not raw_concentrations.get("pm25") or raw_concentrations["pm25"] <= 0:
        # Fallback: use current AQI to estimate PM2.5 concentration
        # This is a rough approximation but better than failing
        if current_aqi <= 50:
            raw_concentrations["pm25"] = current_aqi * 0.24  # Good range
        elif current_aqi <= 100:
            raw_concentrations["pm25"] = 12 + (current_aqi - 50) * 0.46
        else:
            raw_concentrations["pm25"] = 35 + (current_aqi - 100) * 0.40
        logger.warning(f"Using AQI-based PM2.5 estimate: {raw_concentrations['pm25']:.1f} µg/m³")

    # Generate realistic historical pollution sequences (7 days for LSTM)
    historical_sequences = await fetch_historical_pollution(
        request.city,
        raw_concentrations,
        days=7
    )

    # Validate weather data
    temperature = weather_data.get("temperature") or waqi_weather.get("temperature")
    humidity = weather_data.get("humidity") or waqi_weather.get("humidity")
    
    if temperature is None:
        raise HTTPException(
            status_code=502,
            detail=f"Temperature data unavailable for {request.city}. Cannot generate reliable prediction."
        )
    
    if humidity is None:
        raise HTTPException(
            status_code=502,
            detail=f"Humidity data unavailable for {request.city}. Cannot generate reliable prediction."
        )

    # Build weather data with validation
    wind_speed = weather_data.get("wind_speed")
    if wind_speed is None:
        wind_speed = waqi_weather.get("wind_speed")
        if wind_speed is not None:
            wind_speed = wind_speed * 3.6  # m/s to km/h
    
    if wind_speed is None:
        raise HTTPException(
            status_code=502,
            detail=f"Wind speed data unavailable for {request.city}. Cannot generate reliable prediction."
        )

    pressure = weather_data.get("pressure") or waqi_weather.get("pressure")
    if pressure is None:
        raise HTTPException(
            status_code=502,
            detail=f"Atmospheric pressure data unavailable for {request.city}. Cannot generate reliable prediction."
        )

    try:
        pred_request = PredictionRequest(
            location=waqi_data.get("city_name", request.city),
            latitude=waqi_data.get("latitude"),
            longitude=waqi_data.get("longitude"),
            current_aqi=current_aqi,

            weather=WeatherData(
                temperature=temperature,
                humidity=humidity,
                wind_speed=wind_speed,
                wind_direction=weather_data.get("wind_direction"),
                pressure=pressure,
                precipitation=weather_data.get("precipitation") or 0.0,
            ),

            historical_pollution=HistoricalPollutionData(
                pm25=historical_sequences.get("pm25", []),
                pm10=historical_sequences.get("pm10", []),
                no2=historical_sequences.get("no2", []),
                o3=historical_sequences.get("o3", []),
                so2=historical_sequences.get("so2", []),
                co=historical_sequences.get("co", []),
            ),
        )

    except Exception as e:
        logger.exception("Failed to build prediction request")
        raise HTTPException(status_code=500, detail=f"Prediction preparation failed: {str(e)}")

    result = predict_aqi(pred_request, waqi_data=waqi_data, weather_data=weather_data)

    # Push event to orchestrator with dynamic message based on conditions
    try:
        # Safely get 24-hour prediction with bounds checking
        if result.hourly_forecast and len(result.hourly_forecast) > 23:
            predicted_aqi = result.hourly_forecast[23].predicted_aqi
        elif result.hourly_forecast and len(result.hourly_forecast) > 0:
            predicted_aqi = result.hourly_forecast[-1].predicted_aqi  # Use last available
        else:
            predicted_aqi = current_aqi  # Fallback to current
        
        if predicted_aqi > 100:
            # Get category info for dynamic messaging
            from app.config import get_aqi_category
            category_info = get_aqi_category(predicted_aqi)
            
            # Build dynamic message based on AQI level and weather
            if predicted_aqi <= 150:
                severity = "moderately poor"
                base_action = "Sensitive individuals should limit outdoor activities"
            elif predicted_aqi <= 200:
                severity = "unhealthy"
                base_action = "Everyone should reduce prolonged outdoor exertion"
            elif predicted_aqi <= 300:
                severity = "very unhealthy"
                base_action = "Avoid outdoor activities and wear N95 masks if going outside"
            else:
                severity = "hazardous"
                base_action = "Stay indoors, seal windows, and run air purifiers"
            
            # Add weather-specific advice
            weather_advice = []
            if temperature > 30:
                weather_advice.append("High temperature increases health risks")
            if humidity > 80:
                weather_advice.append("High humidity makes breathing more difficult")
            if wind_speed < 5:
                weather_advice.append("Low wind speed means pollutants are not dispersing")
            elif wind_speed > 30:
                weather_advice.append("Strong winds may stir up dust and particles")
            
            combined_action = base_action
            if weather_advice:
                combined_action += ". Note: " + "; ".join(weather_advice)
            
            _push_event("POOR_AIR_QUALITY", "air_quality", {
                "aqi": predicted_aqi,
                "city": waqi_data.get("city_name", request.city),
                "category": category_info["category"],
                "risk_level": result.health_risk_level,
                "severity": severity,
                "recommended_action": combined_action,
                "temperature": temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
            })
    except Exception as e:
        logger.exception("Failed to push POOR_AIR_QUALITY event for %s: %s", request.city, str(e))

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