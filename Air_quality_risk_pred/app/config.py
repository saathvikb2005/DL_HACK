from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List, Tuple


class Settings(BaseSettings):
    """
    Central configuration for the AI Health Hub AQI Predictor.
    Values can be overridden using environment variables.
    """

    # ------------------------------------------------
    # App Info
    # ------------------------------------------------
    APP_NAME: str = "Air Quality Health Risk Predictor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ------------------------------------------------
    # API Keys (loaded from .env)
    # ------------------------------------------------
    WAQI_TOKEN: str
    OWM_API_KEY: str

    # ------------------------------------------------
    # Paths
    # ------------------------------------------------
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    TRAINED_MODELS_DIR: Path = BASE_DIR / "trained_models"
    DATA_DIR: Path = BASE_DIR / "data"

    # Model files
    RF_MODEL_PATH: Path = TRAINED_MODELS_DIR / "rf_model.pkl"
    LSTM_MODEL_PATH: Path = TRAINED_MODELS_DIR / "lstm_model.keras"

    # ------------------------------------------------
    # AQI Breakpoints (US EPA Standard)
    # ------------------------------------------------
    AQI_BREAKPOINTS: List[Tuple[int, int, str, str, str]] = [
        (0, 50, "Good", "green", "Air quality is satisfactory."),
        (51, 100, "Moderate", "yellow", "Acceptable; moderate concern for sensitive people."),
        (101, 150, "Unhealthy for Sensitive Groups", "orange", "Sensitive groups may experience health effects."),
        (151, 200, "Unhealthy", "red", "Everyone may begin to experience health effects."),
        (201, 300, "Very Unhealthy", "purple", "Health alert: serious health effects possible."),
        (301, 500, "Hazardous", "maroon", "Emergency conditions. Entire population affected."),
    ]

    model_config = {
        "env_file": ".env",
        "env_prefix": "AQI_",
    }


settings = Settings()

# Ensure important directories exist
settings.TRAINED_MODELS_DIR.mkdir(exist_ok=True)
settings.DATA_DIR.mkdir(exist_ok=True)


# ------------------------------------------------
# AQI Utilities
# ------------------------------------------------
def get_aqi_category(aqi: float) -> dict:
    """Return AQI category details."""
    for low, high, category, color, description in settings.AQI_BREAKPOINTS:
        if low <= aqi <= high:
            return {
                "category": category,
                "color": color,
                "description": description,
            }

    return {
        "category": "Beyond Index",
        "color": "maroon",
        "description": "AQI exceeds standard scale.",
    }


def get_health_recommendations(aqi: float) -> List[str]:
    """Return health recommendations based on AQI level."""

    if aqi <= 50:
        return ["Air quality is good. Enjoy outdoor activities."]

    elif aqi <= 100:
        return [
            "Sensitive individuals should limit prolonged outdoor exertion."
        ]

    elif aqi <= 150:
        return [
            "Sensitive groups should reduce outdoor exertion.",
            "Keep windows closed.",
            "Use air purifiers indoors if possible."
        ]

    elif aqi <= 200:
        return [
            "Avoid prolonged outdoor exercise.",
            "Wear an N95 or KN95 mask outdoors.",
            "Use indoor air purifiers.",
            "Keep windows and doors closed."
        ]

    elif aqi <= 300:
        return [
            "Avoid outdoor activity.",
            "Wear an N95 mask if you must go outside.",
            "Run air purifiers continuously.",
            "People with asthma should keep inhalers nearby."
        ]

    else:
        return [
            "Stay indoors and avoid going outside.",
            "Seal windows and doors.",
            "Run air purifiers continuously.",
            "Seek medical help if experiencing breathing issues."
        ]