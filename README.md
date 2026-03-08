<!-- markdownlint-disable MD029 -->

# AI Wellness Companion - Complete Health Monitoring System

> **Integrated health monitoring system with 5 AI-powered modules, real-time avatar feedback, and orchestrated event management**

---

## 🎯 System Overview

The AI Wellness Companion is a comprehensive health monitoring platform that tracks:

- **👁️ Eye Health** - Blink rate, stare detection, screen time, yawn-based fatigue
- **🧍 Posture & Ergonomics** - Real-time posture scoring with MediaPipe
- **⌨️ Work Patterns** - Fatigue detection through typing behavior
- **🌬️ Air Quality** - AQI monitoring with weather-aware predictions
- **🏥 Lifestyle Health** - Disease risk prediction & mental health assessment

**Architecture:** 8 integrated components communicating through central orchestrator

---

## 📦 Project Structure

```text
DL_HACK/
├── 🎭 avatar_system/           # Orchestrator + 3D Avatar UI (Port 8765/5173)
├── 👁️  Eye_care/               # Blink/stare detection (MediaPipe)
├── 🧍 posture_detection/       # Posture analysis (MediaPipe Pose)
├── ⌨️  workpattern/             # Fatigue detection (Port 8001)
├── 🌬️  Air_quality_risk_pred/  # AQI prediction (Port 8002)
├── 🏥 vijitha/                 # Disease/stress prediction (Port 8000)
├── 🔗 module_bridge.py         # Event bridge to orchestrator
├── 🚀 launcher.py              # Unified system launcher
└── 📖 README.md                # Complete documentation (this file)
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.8+
python --version

# Install dependencies for all modules
pip install fastapi uvicorn mediapipe opencv-python scikit-learn
pip install requests pandas numpy pynput win10toast
```

### Launch Everything (Recommended)

```bash
# Start all modules at once
python launcher.py --all
```

**This starts:**

1. Orchestrator (WebSocket server on port 8765)
2. Avatar UI (Vite frontend on port 5173)
3. Eye Care (headless background mode)
4. Posture Detection (with GUI)
5. Workpattern monitor (background + API on 8001)
6. Air Quality API (port 8002)

**Note:** Vijitha module must be started manually:

```bash
cd vijitha
python main.py  # Runs on port 8000
```

### Launch Specific Components

```bash
# Orchestrator + Avatar only
python launcher.py

# Orchestrator only (no GUI)
python launcher.py --no-avatar
```

---

## 📋 Module Details

### 1️⃣ Eye Care Module

**Purpose:** Prevent digital eye strain through real-time monitoring

**Features:**

- Blink rate tracking (alerts if < 10 blinks/min)
- Continuous stare detection (alerts after 20s)
- Screen time monitoring (alerts at 40 min)
- 20-20-20 rule reminders
- Multi-backend notifications

**Usage:**

```bash
cd Eye_care
python main.py              # With webcam preview
python main.py --headless   # Background mode (no window)
```

**Events to Orchestrator:**

- `LOW_BLINK_RATE` - Dry eye risk detected
- `CONTINUOUS_STARE` - No blinks for 20+ seconds
- `LONG_SCREEN_TIME` - 40+ minutes continuous use

**Configuration:** `Eye_care/config.py`

---

### 2️⃣ Posture Detection Module

**Purpose:** Prevent musculoskeletal issues through posture monitoring

**Features:**

- 4-metric analysis (Neck/Shoulders/Spine/Rounded shoulders)
- Real-time posture scoring (0-100%)
- Visual feedback with score graph
- Issue-specific alerts (forward head, slouching, uneven shoulders)
- CSV data logging every 3 seconds

**Usage:**

```bash
cd posture_detection
python posture_detection.py
```

**Events to Orchestrator:**

- `BAD_POSTURE` - Score < 70% with specific issues

**Posture Thresholds:**

- Neck angle: ≥150° ideal
- Shoulder symmetry: <2% frame height
- Spine angle: ≥150° ideal

---

### 3️⃣ Workpattern Module

**Purpose:** Prevent work fatigue through typing behavior analysis

**Features:**

- Global keyboard/mouse monitoring (all apps)
- Personalized calibration (learns YOUR baseline in 5 min)
- 4-level fatigue detection (Healthy → Focused → Break Soon → Fatigue)
- Time-based wellness tips (20-20-20 rule, hydration, stretches)
- Windows notifications every 30 minutes
- Real-time API on port 8001

**Usage:**

```bash
cd workpattern
python integrated_monitor.py   # Starts monitor + API
# OR
START_INTEGRATED.bat          # Windows quick launch
```

**Events to Orchestrator:**

- `HIGH_FATIGUE` - Fatigue score ≥ 50%
- `LONG_SESSION` - Work duration > 90 minutes

**API Endpoints:**

- `GET /api/health` - Monitor status
- `GET /api/v1/realtime-status` - Current metrics + analysis
- `GET /api/docs` - API documentation

**Note:** First 5 minutes runs in calibration mode to learn your typing patterns

---

### 4️⃣ Air Quality Module

**Purpose:** Environmental health monitoring with predictive AQI

**Features:**

- EPA-compliant AQI calculation (6 pollutants)
- Random Forest ML predictions (24h/48h forecasts)
- Real-time weather integration (OpenWeatherMap)
- Weather-conditional recommendations
- Auto-location detection (IP geolocation)

**Usage:**

```bash
cd Air_quality_risk_pred
python -m uvicorn app.main:app --port 8002
```

**Events to Orchestrator:**

- `AQI_REPORT` - Periodic AQI updates
- `POOR_AIR_QUALITY` - AQI > 100 (Unhealthy)

**API Endpoints:**

- `POST /api/v1/predict/city` - Predict AQI for specific city
- `GET /api/v1/predict/auto` - Auto-detect location and predict
- `GET /api/docs` - API documentation

**Configuration:** Create `.env` file:

```env
AQI_WAQI_TOKEN=your_waqi_token_here
AQI_OWM_API_KEY=your_openweather_key_here
```

---

### 5️⃣ Vijitha Module (AI Health Platform)

**Purpose:** Lifestyle disease risk and mental health assessment

**Features:**

- Disease risk prediction (Heart Disease, Diabetes, Hypertension)
- Mental health & stress detection (text-based analysis)
- ML ensemble models (Logistic Regression, RF, Gradient Boosting)
- Emotion recognition (7 emotions: anxiety, worry, exhaustion, etc.)
- Professional help flag for critical cases

**Setup:**

```bash
cd vijitha
pip install -r requirements.txt

# Train models (first time only)
python prepare_data.py
python train_disease_model.py
python train_stress_model.py

# Start API server
python main.py  # Runs on port 8000
```

**Events to Orchestrator:**

- `HIGH_DISEASE_RISK` - Risk level = High/Critical
- `HIGH_STRESS` - Stress level = High/Critical

**API Endpoints:**

- `POST /api/v1/disease-risk` - Predict disease risks
- `POST /api/v1/stress-detection` - Analyze mental health
- `GET /api/docs` - API documentation

**Example Disease Risk Request:**

```json
{
  "age": 52,
  "bmi": 31.2,
  "systolic_bp": 145,
  "diastolic_bp": 95,
  "smoking": true,
  "physical_activity_hours": 1.5,
  "diet_quality_score": 4
}
```

**Example Stress Detection Request:**

```json
{
  "user_text": "I feel extremely anxious and overwhelmed. Work pressure is unbearable."
}
```

---

## 🔗 System Integration

### Event Flow Architecture

```text
Health Modules → module_bridge.py → Orchestrator (Port 8765) → Avatar UI (Port 5173)
```

### All Event Types

| Event | Source | Trigger | Avatar Response |
| ----- | ------ | ------- | --------------- |
| `LOW_BLINK_RATE` | Eye Care | < 10 blinks/min | "Blink more often!" |
| `CONTINUOUS_STARE` | Eye Care | 20s no blink | "Take an eye break!" |
| `LONG_SCREEN_TIME` | Eye Care | 40+ min | "Screen break time!" |
| `EXCESSIVE_YAWNING` | Eye Care | 3+ yawns in 5 min | "You need rest!" |
| `BAD_POSTURE` | Posture | Score < 70% | Issue-specific advice |
| `HIGH_FATIGUE` | Workpattern | Fatigue ≥ 50% | "Take a break!" |
| `LONG_SESSION` | Workpattern | 90+ min work | "Time to move!" |
| `POOR_AIR_QUALITY` | Air Quality | AQI > 100 | Weather-aware advice |
| `HIGH_DISEASE_RISK` | Vijitha | Risk = High | "See a doctor" |
| `HIGH_STRESS` | Vijitha | Stress = High | Breathing exercises |

### Bridge Implementation

Each module uses `module_bridge.py` to send events:

```python
from module_bridge import push_event

# Example: Send bad posture event
push_event('BAD_POSTURE', 'posture', {
    'posture_score': 45,
    'issues': ['Forward Head', 'Slouching']
})
```

**Non-blocking:** Events sent in background thread, won't slow down modules

---

## 🏥 Health Coverage

### Physical Health ✅

- **Eye Strain Prevention:** Blink tracking, stare detection, 20-20-20 rule
- **Musculoskeletal:** Posture monitoring, ergonomic alerts
- **Environmental:** Air quality awareness, weather-conditional advice

### Work-Life Balance ✅

- **Fatigue Detection:** Personalized typing behavior analysis
- **Break Management:** Time-based wellness tips
- **Session Tracking:** Work duration monitoring

### Lifestyle Disease Prevention ✅

- **Cardiovascular:** Heart disease risk (0-100%)
- **Metabolic:** Diabetes risk assessment
- **Hypertension:** Blood pressure risk scoring

### Mental Health ✅

- **Stress Detection:** Text-based sentiment analysis
- **Emotion Recognition:** 7 emotions tracked
- **Crisis Support:** Professional help recommendations

---

## 🛠️ System Administration

### Testing Integration

```bash
# Check orchestrator status
curl http://localhost:8765/api/status

# Test air quality API
curl http://localhost:8002/api/v1/predict/auto

# Test workpattern API
curl http://localhost:8001/api/health

# Test vijitha API
curl http://localhost:8000/health
```

### Common Issues

**Orchestrator won't start:**

- Port 8765 already in use: `netstat -ano | findstr :8765`
- Kill process: `taskkill /PID <pid> /F`

**MediaPipe slow import (Python 3.13):**

- Known TensorFlow loading issue
- Takes 30-60 seconds on first import
- Modules work normally after loading

**Webcam not detected:**

- Check `Eye_care/config.py` → `CAMERA_INDEX = 0`
- Try different index (1, 2, etc.) if you have multiple cameras

**Module not sending events:**

- Check orchestrator is running first
- Verify `module_bridge.py` exists in root
- Check module logs for errors

---

## 📚 Documentation

- **Detailed System Status:** [COMPLETE_SYSTEM_STATUS.md](COMPLETE_SYSTEM_STATUS.md)
- **Eye Care Integration:** [Eye_care/INTEGRATION_STATUS.md](Eye_care/INTEGRATION_STATUS.md)
- **Posture Integration:** [posture_detection/INTEGRATION_STATUS.md](posture_detection/INTEGRATION_STATUS.md)
- **Workpattern Integration:** [workpattern/INTEGRATION_STATUS.md](workpattern/INTEGRATION_STATUS.md)
- **Air Quality Integration:** [Air_quality_risk_pred/INTEGRATION_STATUS.md](Air_quality_risk_pred/INTEGRATION_STATUS.md)
- **Vijitha Integration:** [vijitha/INTEGRATION_STATUS.md](vijitha/INTEGRATION_STATUS.md)

---

## 🎨 Technology Stack

**Backend:**

- FastAPI + Uvicorn (REST APIs)
- WebSocket (Real-time bidirectional communication)
- Pydantic (Data validation and settings)

**Frontend:**

- Three.js (3D avatar rendering)
- Vite (Frontend build tool)
- @pixiv/three-vrm (VRM avatar loader)

**Machine Learning:**

- Scikit-learn (Random Forest, ensemble models)
- XGBoost (Gradient boosting)
- MediaPipe (Computer vision - face/pose detection)
- TensorFlow/Keras (LSTM models - optional)
- PyTorch + Transformers (BERT stress detection - optional)

**Computer Vision:**

- OpenCV (Webcam processing)
- MediaPipe Face Mesh (Eye tracking)
- MediaPipe Pose (Posture analysis)

**Monitoring & Input:**

- pynput (Global keyboard/mouse monitoring)
- win10toast (Windows notifications)
- plyer/winotify (Cross-platform notifications)

**External APIs:**

- WAQI (World Air Quality Index data)
- OpenWeatherMap (Weather data)
- ip-api.com (IP-based geolocation)

**Documentation:**

Main documentation is in this README.md file.

**Module-Specific Documentation:**

- [Air Quality Module](Air_quality_risk_pred/README.md) - AQI prediction details
- [Vijitha Module](vijitha/README.md) - Disease risk & mental health API
- [Workpattern Module](workpattern/README.md) - Fatigue detection details
- [Models Documentation](MODELS.md) - ML model inventory and training guides

---

## 📡 API Documentation

All FastAPI services automatically generate interactive API documentation:

### **Orchestrator (WebSocket Hub)**

- **Base URL:** `http://localhost:8765`
- **Health Check:** `GET http://localhost:8765/health`
- **Status Dashboard:** `GET http://localhost:8765/api/status`
- **WebSocket:** `ws://localhost:8765/ws` (Avatar connection)
- **Event Submission:** `POST http://localhost:8765/api/event`

### **Workpattern API**

- **Base URL:** `http://localhost:8001`
- **Interactive Docs:** `http://localhost:8001/docs` 📘
- **Health Check:** `GET http://localhost:8001/api/health`
- **Real-time Status:** `GET http://localhost:8001/api/v1/realtime-status`
- **Features:** Fatigue scoring, session analytics, personalized baseline

### **Air Quality Prediction API**

- **Base URL:** `http://localhost:8002`
- **Interactive Docs:** `http://localhost:8002/docs` 📘
- **Health Check:** `GET http://localhost:8002/health`
- **Auto-Predict (IP location):** `GET http://localhost:8002/api/v1/predict/auto`
- **Predict by City:** `POST http://localhost:8002/api/v1/predict/city`
- **Predict (Custom Data):** `POST http://localhost:8002/api/v1/predict`
- **AQI Categories:** `GET http://localhost:8002/api/v1/aqi-categories`

### **Vijitha Health Platform API**

- **Base URL:** `http://localhost:8000`
- **Interactive Docs:** `http://localhost:8000/api/docs` 📘
- **Health Check:** `GET http://localhost:8000/health`
- **Disease Risk:** `POST http://localhost:8000/api/v1/disease-risk`
- **Stress Detection:** `POST http://localhost:8000/api/v1/stress-detection`

### **Avatar Frontend**

- **Base URL:** `http://localhost:5173`
- **WebSocket Client:** Connects to orchestrator automatically
- **Features:** 3D VRM avatar, speech synthesis, chat interface, module status indicators

**Testing APIs:**

```bash
# Workpattern status
curl http://localhost:8001/api/v1/realtime-status

# Air quality auto-prediction (uses your IP location)
curl http://localhost:8002/api/v1/predict/auto

# Air quality by city name
curl -X POST http://localhost:8002/api/v1/predict/city \
  -H "Content-Type: application/json" \
  -d '{"city": "Seattle"}'

# Vijitha health check
curl http://localhost:8000/health

# Disease risk prediction
curl -X POST http://localhost:8000/api/v1/disease-risk \
  -H "Content-Type: application/json" \
  -d '{"age": 45, "bmi": 28.5, "smoking": true, "physical_activity_hours": 2}'

# Orchestrator system status
curl http://localhost:8765/api/status
```

---

## 🚀 Deployment Guide

### Quick Start (Development)

1. **Clone and Setup:**

```bash
# Clone repository
git clone <your-repo-url>
cd DL_HACK

# Run automated setup
setup.bat           # Windows
chmod +x setup.sh && ./setup.sh  # Linux/Mac
```

2. **Configure Environment:**

```bash
# Edit .env file (created by setup script)
# Add your API keys:
#   - WAQI_TOKEN: https://aqicn.org/data-platform/token/
#   - OWM_API_KEY: https://openweathermap.org/api
```

3. **Launch System:**

```bash
# Activate virtual environment
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/Mac

# Start all modules
python launcher.py --all

# OR use master launcher with full features
python MASTER_LAUNCHER.py --all
```

4. **Access Services:**

- Avatar UI: <http://localhost:5173>
- Orchestrator: <http://localhost:8765>
- API Docs: See section above

### Production Deployment

#### Environment Variables

```bash
# Required
AQI_WAQI_TOKEN=<your_token>
AQI_OWM_API_KEY=<your_key>

# Production CORS (comma-separated)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional port overrides
ORCHESTRATOR_PORT=8765
WORKPATTERN_PORT=8001
AIR_QUALITY_PORT=8002
VIJITHA_PORT=8000
AVATAR_UI_PORT=5173
```

#### System Requirements

- **OS:** Windows 10/11, Ubuntu 20.04+, macOS 11+
- **Python:** 3.8 or higher
- **Node.js:** 16+ (for avatar frontend)
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 500MB for models and dependencies
- **Webcam:** Required for Eye Care and Posture modules

#### Model Files Verification

```bash
# Check all models are present
python -c "import os; print('Air Quality:', os.path.exists('Air_quality_risk_pred/trained_models/rf_model.pkl'))"
python -c "import os; print('Vijitha:', len([f for f in os.listdir('vijitha/models') if f.endswith('.pkl')]) > 0)"
python -c "import os; print('Posture:', os.path.exists('posture_detection/posture_model.pkl'))"
```

#### Process Management (Production)

**Using systemd (Linux):**

```bash
# Create service file: /etc/systemd/system/wellness-companion.service
[Unit]
Description=AI Wellness Companion
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/DL_HACK
ExecStart=/path/to/.venv/bin/python launcher.py --all
Restart=always

[Install]
WantedBy=multi-user.target
```

**Using PM2 (Node.js process manager):**

```bash
pm2 start launcher.py --name wellness-companion --interpreter python
pm2 startup
pm2 save
```

#### Docker Deployment (Future Enhancement)

```dockerfile
# Dockerfile (planned)
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "launcher.py", "--all"]
```

#### Monitoring & Health Checks

**Health Check Endpoints:**

- Orchestrator: `http://localhost:8765/health`
- Workpattern: `http://localhost:8001/api/health`
- Air Quality: `http://localhost:8002/health`
- Vijitha: `http://localhost:8000/health`

**Monitoring Script:**

```bash
# healthcheck.sh
#!/bin/bash
curl -f http://localhost:8765/health || exit 1
curl -f http://localhost:8001/api/health || exit 1
curl -f http://localhost:8002/health || exit 1
curl -f http://localhost:8000/health || exit 1
```

#### Production Troubleshooting

**Port Conflicts:**

```bash
# Check if ports are in use
netstat -ano | findstr :8765    # Windows
lsof -i :8765                   # Linux/Mac

# Kill process using port
taskkill /PID <pid> /F          # Windows
kill -9 <pid>                   # Linux/Mac
```

**Missing API Keys:**

```text
[ERROR] WAQI token not configured
Solution: Add AQI_WAQI_TOKEN to .env file
Get token from: https://aqicn.org/data-platform/token/
```

**Model Loading Failures:**

```text
[WARNING] Models not found, using fallback
Solution: Check MODELS.md for training instructions
Note: Rule-based fallbacks work fine for workpattern module
```

**Virtual Environment Issues:**

```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Webcam Access Denied:**

- Windows: Settings → Privacy → Camera → Allow desktop apps
- Linux: Add user to `video` group: `sudo usermod -a -G video $USER`
- macOS: System Preferences → Security & Privacy → Camera

#### Performance Optimization

**Reduce Memory Usage:**

- Disable optional modules (comment out in launcher.py)
- Use LSTM model only if high accuracy needed (requires TensorFlow)
- Limit event history size in orchestrator

**Improve Startup Time:**

- Pre-download MediaPipe models
- Use model caching
- Enable lazy loading for ML models

---

## 🧭 Planned Roadmap

The following roadmap consolidates planned items already implied in module docs and current code behavior:

### Phase 1 - Stability & Integration

- Make `MASTER_LAUNCHER.py --all` the default full-system runner in docs (it already includes Vijitha startup).
- Add a single root `requirements.txt` (or install script) to reduce cross-module setup friction.
- Align module README files with the current runtime flow (`integrated_monitor.py`, real-time endpoints, orchestrator event flow).
- Add startup validation checks for required API keys (`WAQI`, `OpenWeatherMap`) and model files with clear error guidance.

### Phase 2 - Platform Features

- Add prediction/session persistence (history for stress, disease risk, fatigue, posture trends).
- Add authentication and rate limiting for public API endpoints.
- Add a consolidated historical analytics dashboard across all 5 health modules.
- Improve multi-user support for work-pattern calibration and profile storage.

### Phase 3 - AI Upgrades

- Upgrade stress NLP pipeline (BERT-level model as optional high-accuracy mode).
- Improve work fatigue model lifecycle (training reproducibility, model versioning, evaluation report export).
- Expand avatar conversational intelligence from rule-based responses to pluggable LLM backends.
- Add model confidence and drift monitoring for AQI, stress, and disease-risk predictions.

### Phase 4 - Production Readiness

- Containerize all services and add one-command deployment profiles.
- Harden observability (structured logs, health probes, alerting, trace IDs across modules).
- Security hardening for CORS, secrets, and network paths (including secure geolocation endpoint strategy).
- Add CI checks for smoke tests, endpoint contracts, and orchestrator event compatibility.

---

## 📝 License & Credits

**Created:** March 2026  
**Purpose:** Hackathon Project - AI Wellness Companion

**Key Features:**

- ✅ 5 health monitoring modules
- ✅ Real-time event orchestration
- ✅ 3D avatar feedback system
- ✅ ML-powered predictions
- ✅ Personalized calibration
- ✅ Weather-aware recommendations

---

## 🚀 Getting Started (Step-by-Step)

1. **Clone & Setup**

   ```bash
   cd DL_HACK
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt  # If exists
   ```

2. **Configure APIs (Air Quality only)**

   ```bash
   cd Air_quality_risk_pred
   # Create .env file with your API keys
   ```

3. **Train Vijitha Models (Optional)**

   ```bash
   cd vijitha
   python setup_and_train.bat  # Windows
   # OR
   python prepare_data.py && python train_disease_model.py && python train_stress_model.py
   ```

4. **Launch System**

   ```bash
   cd ..
   python launcher.py --all
   ```

5. **Start Vijitha (Manual)**

   ```bash
   cd vijitha
   python main.py
   ```

6. **Access Services**
   - Avatar UI: <http://localhost:5173>
   - Air Quality API: <http://localhost:8002/api/docs>
   - Workpattern API: <http://localhost:8001/api/docs>
   - Vijitha API: <http://localhost:8000/api/docs>

7. **Monitor Console**
   - Eye Care: Console notifications
   - Posture: GUI window with real-time score
   - Workpattern: Console updates every 30 seconds

---

Enjoy comprehensive health monitoring with AI! 🎉
