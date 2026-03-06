# Air Quality Health Risk Predictor

Predicts future AQI (next 24–48 hours) and provides health warnings & safety recommendations.
Integrates live data from **WAQI** (World Air Quality Index) and **OpenWeatherMap** APIs.

## Project Structure

```
Air_quality_risk_pred/
│
├── app/                              # Main application package
│   ├── __init__.py                   # Package marker
│   ├── main.py                       # FastAPI entry point, CORS, lifespan, root routes
│   ├── config.py                     # Settings (API keys, paths), AQI breakpoints, health recommendations
│   │
│   ├── schemas/                      # Pydantic data models
│   │   ├── __init__.py
│   │   └── prediction.py            # Request/Response schemas (CityPredictionRequest, PredictionRequest,
│   │                                #   PredictionResponse, WeatherData, PollutantReading, HourlyForecast, etc.)
│   │
│   ├── services/                     # Business logic & external API integrations
│   │   ├── __init__.py
│   │   ├── prediction_service.py     # Core prediction engine — loads RF/LSTM models, heuristic fallback,
│   │   │                             #   feature engineering, health risk classification, recommendations
│   │   ├── waqi_service.py           # WAQI API client — fetches live AQI, pollutant breakdown,
│   │   │                             #   daily forecasts (PM2.5, PM10, O3, UVI)
│   │   └── weather_service.py        # OpenWeatherMap API client — fetches temperature, humidity,
│   │                                 #   wind speed, pressure, weather description
│   │
│   ├── routes/                       # API endpoint definitions
│   │   ├── __init__.py
│   │   └── prediction.py            # POST /api/v1/predict/city  — simple city-name endpoint (auto-fetches APIs)
│   │                                #   POST /api/v1/predict       — full manual endpoint (all data provided)
│   │                                #   GET  /api/v1/aqi-categories — list AQI breakpoint categories
│   │
│   └── models/                       # ML training & data processing scripts
│       ├── __init__.py
│       ├── preprocess.py             # Stage 2: Data cleaning — reads raw city_day.csv, handles missing values,
│       │                             #   renames columns, adds prev_aqi feature, outputs city_day_clean.csv
│       ├── train_rf.py               # Stage 4: Trains Random Forest Regressor on clean data
│       │                             #   Features: pm25, pm10, no2, co, o3, so2, prev_aqi → predicts AQI
│       └── train_lstm.py             # Stage 4: Trains LSTM time-series model on clean data
│                                     #   7-day sequences of pollutants → predicts next-day AQI
│
├── data/                             # Dataset storage
│   ├── city_day.csv                  # Raw CPCB dataset (29K+ rows, 26 Indian cities, 2015–2020)
│   └── city_day_clean.csv            # [Generated] Clean dataset after running preprocess.py
│
├── trained_models/                   # Saved ML model files
│   ├── random_forest_aqi.pkl         # [Generated] Trained RF model
│   ├── lstm_aqi.keras                # [Generated] Trained LSTM model
│   └── lstm_scaler.pkl               # [Generated] Feature scaler for LSTM inference
│
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

## What Each File Does

### Core App
| File | Purpose |
|------|---------|
| `app/main.py` | Creates the FastAPI app, sets up CORS, loads ML models on startup, registers routes, serves `/` and `/health` |
| `app/config.py` | Stores API keys (WAQI, OpenWeatherMap), file paths, AQI breakpoint table (0–500 scale with 6 categories), and generates health recommendations per AQI level |

### Schemas
| File | Purpose |
|------|---------|
| `app/schemas/prediction.py` | Defines all Pydantic models — `CityPredictionRequest` (just a city name), `PredictionRequest` (full manual input), `PredictionResponse` (AQI forecast + health warnings + recommendations + hourly/daily forecasts + live data summary) |

### Services
| File | Purpose |
|------|---------|
| `app/services/prediction_service.py` | The brain — loads trained RF/LSTM models at startup, builds feature vectors, runs predictions (with heuristic fallback if no model exists), classifies health risk, generates warnings |
| `app/services/waqi_service.py` | Calls WAQI API → returns current AQI, pollutant sub-indices (PM2.5, PM10, NO2, O3, SO2, CO), daily forecasts, city geo-coordinates |
| `app/services/weather_service.py` | Calls OpenWeatherMap API → returns temperature (°C), humidity (%), wind speed (km/h), pressure (hPa), weather description |

### Routes
| File | Purpose |
|------|---------|
| `app/routes/prediction.py` | Three endpoints: `POST /predict/city` (auto-fetches live data by city name), `POST /predict` (manual with all data), `GET /aqi-categories` (reference table) |

### ML Pipeline
| File | Purpose |
|------|---------|
| `app/models/preprocess.py` | Reads raw `city_day.csv` → cleans missing values, renames columns, adds `prev_aqi` feature → saves `city_day_clean.csv` |
| `app/models/train_rf.py` | Trains Random Forest on 7 features → outputs MAE, R², feature importances → saves `random_forest_aqi.pkl` |
| `app/models/train_lstm.py` | Trains LSTM on 7-day pollutant sequences → outputs MAE → saves `lstm_aqi.keras` + `lstm_scaler.pkl` |

## Quick Start

```bash
cd Air_quality_risk_pred
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

## ML Pipeline (Run Once)

```bash
# Step 1: Clean the raw dataset
python -m app.models.preprocess

# Step 2: Train Random Forest (fast, recommended)
python -m app.models.train_rf

# Step 3 (optional): Train LSTM (needs TensorFlow)
pip install tensorflow
python -m app.models.train_lstm --epochs 50
```

## API Endpoints

| Method | Path                        | Description                                       |
|--------|-----------------------------|----------------------------------------------------|
| GET    | `/`                         | Service info                                       |
| GET    | `/health`                   | Health check                                       |
| POST   | `/api/v1/predict/city`      | Simple: just pass `{"city": "Delhi"}` → full prediction |
| POST   | `/api/v1/predict`           | Manual: provide all data yourself                  |
| GET    | `/api/v1/aqi-categories`    | List all AQI breakpoint categories                 |

## System Flow

```
User sends city name (e.g. "Delhi")
        ↓
Backend fetches live AQI from WAQI API
        ↓
Backend fetches weather from OpenWeatherMap API
        ↓
Data sent to ML prediction service
        ↓
RF/LSTM model predicts AQI (24–48h)
        ↓
System classifies health risk level
        ↓
Returns: predicted AQI + warnings + recommendations
```

## Dataset
- **Source**: CPCB (Central Pollution Control Board, India)
- **File**: `data/city_day.csv`
- **Columns**: City, Date, PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3, Benzene, Toluene, Xylene, AQI, AQI_Bucket
- **Coverage**: 26 cities, 2015–2020, ~29,500 rows
