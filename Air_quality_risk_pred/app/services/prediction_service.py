"""
Prediction service — orchestrates ML models for AQI forecasting.
"""

import numpy as np
from datetime import datetime, timezone
import pickle
import logging

from app.config import get_aqi_category, get_health_recommendations, settings
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    HourlyForecast,
    DailyForecast,
    DailyForecastEntry,
    LiveDataSummary,
    PollutantReading,
)

logger = logging.getLogger(__name__)

# ----------------------------------------------------
# Model storage
# ----------------------------------------------------
_rf_model = None
_lstm_model = None


# ----------------------------------------------------
# Model loading
# ----------------------------------------------------
def load_models():
    """Load ML models during API startup."""
    global _rf_model, _lstm_model

    # Random Forest
    try:
        if settings.RF_MODEL_PATH.exists():
            with open(settings.RF_MODEL_PATH, "rb") as f:
                _rf_model = pickle.load(f)
            logger.info("Random Forest model loaded")
        else:
            logger.warning("RF model not found — heuristic fallback enabled")
    except Exception:
        logger.exception("Failed loading Random Forest model")

    # LSTM
    try:
        if settings.LSTM_MODEL_PATH.exists():
            from tensorflow.keras.models import load_model

            _lstm_model = load_model(str(settings.LSTM_MODEL_PATH))
            logger.info("LSTM model loaded")
        else:
            logger.warning("LSTM model not found — heuristic fallback enabled")
    except Exception:
        logger.warning("TensorFlow not installed or LSTM failed")


# ----------------------------------------------------
# Feature engineering
# ----------------------------------------------------
def _build_features(req: PredictionRequest):
    poll = req.historical_pollution

    def avg(values):
        return float(np.mean(values)) if values else 0.0

    features = [
        avg(poll.pm25),
        avg(poll.pm10),
        avg(poll.no2),
        avg(poll.co),
        avg(poll.o3),
        avg(poll.so2),
        req.current_aqi,
    ]

    return np.array(features).reshape(1, -1)


def _build_sequence(req: PredictionRequest):
    pm25 = req.historical_pollution.pm25 or [req.current_aqi]

    seq = pm25[-24:]

    if len(seq) < 24:
        seq = [seq[0]] * (24 - len(seq)) + seq

    return np.array(seq).reshape(1, 24, 1)


# ----------------------------------------------------
# Heuristic fallback predictor
# ----------------------------------------------------
def _heuristic_predict(req: PredictionRequest):
    pm25 = req.historical_pollution.pm25 or [req.current_aqi]
    current = req.current_aqi

    if len(pm25) >= 6:
        recent = pm25[-6:]
        trend = (recent[-1] - recent[0]) / len(recent)
    else:
        trend = 0

    wind_factor = max(0.7, 1 - req.weather.wind_speed / 50)
    rain_factor = max(0.5, 1 - (req.weather.precipitation or 0) / 20)
    humidity_factor = 1 + (req.weather.humidity - 50) / 200

    forecasts = []
    aqi = current

    for hour in range(1, 49):

        damping = 0.95 ** hour
        aqi = aqi + trend * damping

        aqi = aqi * wind_factor * rain_factor * humidity_factor

        hour_of_day = (datetime.now().hour + hour) % 24

        if 7 <= hour_of_day <= 10 or 18 <= hour_of_day <= 21:
            aqi *= 1.05
        else:
            aqi *= 0.98

        aqi = max(0, min(500, aqi))

        forecasts.append(round(aqi, 1))

    return forecasts


# ----------------------------------------------------
# Prediction engine
# ----------------------------------------------------
def predict_aqi(req: PredictionRequest, waqi_data=None, weather_data=None):

    model_used = "heuristic_baseline"

    # -------------------------
    # Try LSTM
    # -------------------------
    if _lstm_model is not None:
        try:
            seq = _build_sequence(req)
            preds = _lstm_model.predict(seq, verbose=0).flatten().tolist()

            while len(preds) < 48:
                preds.append(preds[-1])

            hourly_predictions = [max(0, min(500, round(v, 1))) for v in preds[:48]]

            model_used = "lstm"

        except Exception:
            logger.exception("LSTM prediction failed")
            hourly_predictions = _heuristic_predict(req)

    # -------------------------
    # Try Random Forest
    # -------------------------
    elif _rf_model is not None:
        try:
            features = _build_features(req)
            pred_24h = float(_rf_model.predict(features)[0])

            hourly_predictions = []

            for h in range(1, 49):
                ratio = h / 24
                pred = req.current_aqi + (pred_24h - req.current_aqi) * min(ratio, 1)
                hourly_predictions.append(round(max(0, min(500, pred)), 1))

            model_used = "random_forest"

        except Exception:
            logger.exception("RF prediction failed")
            hourly_predictions = _heuristic_predict(req)

    else:
        hourly_predictions = _heuristic_predict(req)

    # ------------------------------------------------
    # Build response
    # ------------------------------------------------
    aqi_24h = hourly_predictions[23]
    aqi_48h = hourly_predictions[47]

    cat_current = get_aqi_category(req.current_aqi)
    cat_24h = get_aqi_category(aqi_24h)
    cat_48h = get_aqi_category(aqi_48h)

    worst_aqi = max(hourly_predictions)

    if worst_aqi <= 50:
        risk = "Low"
    elif worst_aqi <= 100:
        risk = "Moderate"
    elif worst_aqi <= 150:
        risk = "High"
    elif worst_aqi <= 200:
        risk = "Very High"
    elif worst_aqi <= 300:
        risk = "Severe"
    else:
        risk = "Critical"

    warnings = []

    if worst_aqi > 100:
        warnings.append("AQI expected to reach unhealthy levels.")

    if worst_aqi > 150:
        warnings.append("Sensitive groups should take precautions.")

    if worst_aqi > 200:
        warnings.append("Health alert: harmful air quality expected.")

    if worst_aqi > 300:
        warnings.append("Hazardous air quality — avoid outdoor exposure.")

    recommendations = get_health_recommendations(worst_aqi)

    hourly_forecast = []

    for i, value in enumerate(hourly_predictions):
        cat = get_aqi_category(value)

        hourly_forecast.append(
            HourlyForecast(
                hour=i + 1,
                predicted_aqi=value,
                category=cat["category"],
                color=cat["color"],
            )
        )

    # -------------------------
    # Daily forecast
    # -------------------------
    daily_forecast = []

    if waqi_data and "daily_forecast" in waqi_data:

        for pollutant, entries in waqi_data["daily_forecast"].items():

            daily_forecast.append(
                DailyForecast(
                    pollutant=pollutant,
                    forecasts=[
                        DailyForecastEntry(**entry)
                        for entry in entries
                    ],
                )
            )

    # -------------------------
    # Live data summary
    # -------------------------
    live_data = None

    if waqi_data:

        pollutants = waqi_data.get("pollutants", {})

        live_data = LiveDataSummary(
            waqi_aqi=waqi_data.get("aqi"),
            dominant_pollutant=waqi_data.get("dominant_pollutant"),
            pollutants=PollutantReading(**pollutants) if pollutants else None,
            weather_description=(weather_data or {}).get("description"),
            temperature=(weather_data or {}).get("temperature"),
            humidity=(weather_data or {}).get("humidity"),
            wind_speed=(weather_data or {}).get("wind_speed"),
        )

    return PredictionResponse(
        location=req.location,
        current_aqi=req.current_aqi,
        current_category=cat_current["category"],
        predicted_aqi_24h=aqi_24h,
        predicted_category_24h=cat_24h["category"],
        predicted_aqi_48h=aqi_48h,
        predicted_category_48h=cat_48h["category"],
        health_risk_level=risk,
        health_warnings=warnings,
        recommendations=recommendations,
        hourly_forecast=hourly_forecast,
        daily_forecast=daily_forecast,
        live_data=live_data,
        model_used=model_used,
        predicted_at=datetime.now(timezone.utc),
    )