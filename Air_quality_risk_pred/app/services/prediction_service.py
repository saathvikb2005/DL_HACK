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
_lstm_scaler = None

LSTM_SEQ_LEN = 7
LSTM_FEATURES = ["pm25", "pm10", "no2", "co", "o3", "so2"]


# ----------------------------------------------------
# Model loading
# ----------------------------------------------------
def load_models():
    """Load ML models during API startup."""
    global _rf_model, _lstm_model, _lstm_scaler

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

    # LSTM + scaler
    scaler_path = settings.TRAINED_MODELS_DIR / "lstm_scaler.pkl"
    try:
        if settings.LSTM_MODEL_PATH.exists() and scaler_path.exists():
            from tensorflow.keras.models import load_model

            _lstm_model = load_model(str(settings.LSTM_MODEL_PATH))
            with open(scaler_path, "rb") as f:
                _lstm_scaler = pickle.load(f)
            logger.info("LSTM model + scaler loaded")
        else:
            missing = []
            if not settings.LSTM_MODEL_PATH.exists():
                missing.append("model")
            if not scaler_path.exists():
                missing.append("scaler")
            logger.warning("LSTM %s not found — heuristic fallback enabled", "+".join(missing))
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
    """Build a (1, LSTM_SEQ_LEN, 6) sequence for the LSTM model.

    Uses the last LSTM_SEQ_LEN readings of all 6 pollutants,
    normalized through the saved MinMaxScaler.
    """
    poll = req.historical_pollution

    def last_n(values, n, fallback=0.0):
        if not values:
            return [fallback] * n
        v = values[-n:]
        return [v[0]] * (n - len(v)) + v  # pad front if short

    pm25 = last_n(poll.pm25, LSTM_SEQ_LEN, req.current_aqi)
    pm10 = last_n(poll.pm10, LSTM_SEQ_LEN)
    no2 = last_n(poll.no2, LSTM_SEQ_LEN)
    co = last_n(poll.co, LSTM_SEQ_LEN)
    o3 = last_n(poll.o3, LSTM_SEQ_LEN)
    so2 = last_n(poll.so2, LSTM_SEQ_LEN)

    # Shape: (LSTM_SEQ_LEN, 6)
    raw = np.array([pm25, pm10, no2, co, o3, so2]).T

    # Normalize with the scaler used during training
    if _lstm_scaler is not None:
        raw = _lstm_scaler.transform(raw)

    return raw.reshape(1, LSTM_SEQ_LEN, len(LSTM_FEATURES))


# ----------------------------------------------------
# Heuristic fallback predictor
# ----------------------------------------------------
def _heuristic_predict(req: PredictionRequest):
    """Simple heuristic forecast when ML models are unavailable.

    Applies trend, weather adjustments, and diurnal pattern as
    *additive offsets* from the current AQI rather than compounding
    multiplicative factors (which would decay the AQI to 0).
    """
    pm25 = req.historical_pollution.pm25 or [req.current_aqi]
    current = req.current_aqi

    # Trend: average hourly change from recent readings
    if len(pm25) >= 6:
        recent = pm25[-6:]
        trend = (recent[-1] - recent[0]) / len(recent)
    else:
        trend = 0

    # Weather adjustments (additive, applied once, not compounded)
    wind_adj = -req.weather.wind_speed * 0.5          # wind disperses pollution
    rain_adj = -(req.weather.precipitation or 0) * 2  # rain washes out particles
    humid_adj = (req.weather.humidity - 50) * 0.1     # high humidity traps particles

    base_adj = wind_adj + rain_adj + humid_adj

    forecasts = []
    for hour in range(1, 49):
        # Damped trend
        damping = 0.97 ** hour
        aqi = current + trend * hour * damping + base_adj * damping

        # Diurnal pattern: rush-hour peaks
        hour_of_day = (datetime.now().hour + hour) % 24
        if 7 <= hour_of_day <= 10 or 18 <= hour_of_day <= 21:
            aqi += current * 0.03  # slight peak
        elif 1 <= hour_of_day <= 5:
            aqi -= current * 0.05  # overnight dip

        aqi = max(0, min(500, aqi))
        forecasts.append(round(aqi, 1))

    return forecasts


# ----------------------------------------------------
# Prediction engine
# ----------------------------------------------------
def predict_aqi(req: PredictionRequest, waqi_data=None, weather_data=None):

    model_used = "heuristic_baseline"

    # -------------------------
    # Try Random Forest first (more reliable for diverse cities)
    # LSTM is biased toward high AQI from Indian training data
    # -------------------------
    rf_ok = False

    if _rf_model is not None:
        try:
            features = _build_features(req)
            pred_24h = float(_rf_model.predict(features)[0])

            hourly_predictions = []

            for h in range(1, 49):
                ratio = h / 24
                pred = req.current_aqi + (pred_24h - req.current_aqi) * min(ratio, 1)
                hourly_predictions.append(round(max(0, min(500, pred)), 1))

            model_used = "random_forest"
            rf_ok = True

        except Exception:
            logger.exception("RF prediction failed — trying LSTM")

    # -------------------------
    # Try LSTM if RF unavailable (fallback)
    # -------------------------
    if not rf_ok and _lstm_model is not None and _lstm_scaler is not None:
        try:
            seq = _build_sequence(req)
            # LSTM outputs 1 value per call; iterate to build 48h forecast
            preds = []
            current_seq = seq.copy()
            for _ in range(48):
                p = float(_lstm_model.predict(current_seq, verbose=0).flatten()[0])
                preds.append(p)
                # Slide window: drop first timestep, append prediction as pm25
                new_row = current_seq[0, -1, :].copy()
                # Update the pm25 column (index 0) with the new prediction
                # Normalize: use scaler's pm25 min/max
                pm25_min = _lstm_scaler.data_min_[0]
                pm25_max = _lstm_scaler.data_max_[0]
                pm25_range = pm25_max - pm25_min if pm25_max > pm25_min else 1.0
                new_row[0] = (p - pm25_min) / pm25_range
                new_row = np.clip(new_row, 0, 1)
                current_seq = np.concatenate(
                    [current_seq[:, 1:, :], new_row.reshape(1, 1, -1)], axis=1
                )

            hourly_predictions = [max(0, min(500, round(v, 1))) for v in preds]
            model_used = "lstm"

        except Exception:
            logger.exception("LSTM prediction failed — using heuristic")
            hourly_predictions = _heuristic_predict(req)

    # -------------------------
    # Fallback to heuristic if neither ML model produced results
    # -------------------------
    if model_used == "heuristic_baseline":
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
    
    # Add weather-conditional recommendations for all AQI levels
    # Weather can affect comfort and health even when air quality is good
    weather_recommendations = []
    
    if req.weather.temperature > 30:
        weather_recommendations.append("High temperature increases health risks - stay hydrated and minimize outdoor exposure during peak heat hours")
    
    if req.weather.humidity > 80:
        weather_recommendations.append("High humidity makes breathing more difficult - sensitive groups should take extra precautions")
    
    if req.weather.wind_speed < 5:
        if worst_aqi > 50:  # Only warn about dispersion if AQI is elevated
            weather_recommendations.append("Low wind speed means pollutants are not dispersing - air quality may worsen")
    elif req.weather.wind_speed > 30:
        weather_recommendations.append("Strong winds may stir up dust and particles - wear protective masks if going outdoors")
    
    # Add weather recommendations to the list
    if weather_recommendations:
        recommendations.extend(weather_recommendations)

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