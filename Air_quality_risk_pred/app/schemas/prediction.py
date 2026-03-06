from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class WeatherData(BaseModel):
    """Current weather conditions at the location."""
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity %")
    wind_speed: float = Field(..., ge=0, description="Wind speed in km/h")
    wind_direction: Optional[float] = Field(None, ge=0, le=360, description="Wind direction in degrees")
    pressure: Optional[float] = Field(None, description="Atmospheric pressure in hPa")
    precipitation: Optional[float] = Field(0.0, ge=0, description="Precipitation in mm")


class PollutantReading(BaseModel):
    """Current pollutant concentrations."""
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    so2: Optional[float] = None
    co: Optional[float] = None


class DailyForecastEntry(BaseModel):
    """Single-day forecast entry."""
    day: str
    avg: float
    min: float
    max: float


class HistoricalPollutionData(BaseModel):
    """Historical pollution readings (last 24–72 hours)."""

    pm25: List[float] = Field(..., description="PM2.5 readings hourly")
    pm10: List[float] = Field(default_factory=list)
    no2: List[float] = Field(default_factory=list)
    o3: List[float] = Field(default_factory=list)
    so2: List[float] = Field(default_factory=list)
    co: List[float] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class CityPredictionRequest(BaseModel):
    """
    Simple request where backend fetches all external data automatically.
    """

    city: str = Field(..., min_length=1, max_length=200, description="City name")

    model_config = {
        "json_schema_extra": {
            "example": {"city": "Delhi"}
        }
    }


class PredictionRequest(BaseModel):
    """
    Full manual prediction request (useful for testing models).
    """

    location: str = Field(..., min_length=1, max_length=200)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    current_aqi: float = Field(..., ge=0, le=500)

    weather: WeatherData
    historical_pollution: HistoricalPollutionData

    model_config = {
        "json_schema_extra": {
            "example": {
                "location": "Delhi",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "current_aqi": 165,
                "weather": {
                    "temperature": 32.0,
                    "humidity": 55,
                    "wind_speed": 8.5,
                    "wind_direction": 220,
                    "pressure": 1008,
                    "precipitation": 0.0
                },
                "historical_pollution": {
                    "pm25": [85, 90, 88, 92, 95, 100, 98, 105]
                }
            }
        }
    }


# ---------------------------------------------------------------------------
# Forecast Models
# ---------------------------------------------------------------------------

class HourlyForecast(BaseModel):
    """Forecast for a single future hour."""

    hour: int = Field(..., description="Hours ahead (1–48)")
    predicted_aqi: float
    category: str
    color: str
    confidence: Optional[float] = Field(None, description="Model confidence score")


class DailyForecast(BaseModel):
    """Daily pollutant forecast (from WAQI API)."""

    pollutant: str
    forecasts: List[DailyForecastEntry]


# ---------------------------------------------------------------------------
# Live Data Summary
# ---------------------------------------------------------------------------

class LiveDataSummary(BaseModel):
    """Summary of live API data used in prediction."""

    waqi_aqi: Optional[float] = None
    dominant_pollutant: Optional[str] = None
    pollutants: Optional[PollutantReading] = None

    weather_description: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None


# ---------------------------------------------------------------------------
# Response Model
# ---------------------------------------------------------------------------

class PredictionResponse(BaseModel):
    """Main prediction response."""

    location: str

    current_aqi: float
    current_category: str

    predicted_aqi_24h: float
    predicted_category_24h: str

    predicted_aqi_48h: float
    predicted_category_48h: str

    health_risk_level: str
    health_warnings: List[str]
    recommendations: List[str]

    hourly_forecast: List[HourlyForecast]

    daily_forecast: List[DailyForecast] = Field(default_factory=list)

    live_data: Optional[LiveDataSummary] = None

    model_used: str

    predicted_at: datetime