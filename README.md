# AI Wellness Companion - Complete Health Monitoring System

> **Integrated health monitoring system with 5 AI-powered modules, real-time avatar feedback, and orchestrated event management**

---

## 🎯 System Overview

The AI Wellness Companion is a comprehensive health monitoring platform that tracks:

- **👁️ Eye Health** - Blink rate, stare detection, screen time
- **🧍 Posture & Ergonomics** - Real-time posture scoring with MediaPipe
- **⌨️ Work Patterns** - Fatigue detection through typing behavior
- **🌬️ Air Quality** - AQI monitoring with weather-aware predictions
- **🏥 Lifestyle Health** - Disease risk prediction & mental health assessment

**Architecture:** 8 integrated components communicating through central orchestrator

---

## 📦 Project Structure

```
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
```
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

```
Health Modules → module_bridge.py → Orchestrator (Port 8765) → Avatar UI (Port 5173)
```

### All Event Types

| Event | Source | Trigger | Avatar Response |
|-------|--------|---------|-----------------|
| `LOW_BLINK_RATE` | Eye Care | < 10 blinks/min | "Blink more often!" |
| `CONTINUOUS_STARE` | Eye Care | 20s no blink | "Take an eye break!" |
| `LONG_SCREEN_TIME` | Eye Care | 40+ min | "Screen break time!" |
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

### Troubleshooting

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
**Main Documentation:** This README.md file contains all essential information

**Module-Specific READMEs:**
- [Air Quality Module](Air_quality_risk_pred/README.md) - AQI prediction details
- [Vijitha Module](vijitha/README.md) - Disease risk & mental health API
- [Workpattern Module](workpattern/README.md) - Fatigue detection details
- Three.js (3D avatar rendering)

**Monitoring:**
- pynput (Global keyboard/mouse)
- OpenCV (Webcam processing)

**APIs:**
- WAQI (Air quality data)
- OpenWeatherMap (Weather data)
- ip-api.com (Geolocation)

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
   - Avatar UI: http://localhost:5173
   - Air Quality API: http://localhost:8002/api/docs
   - Workpattern API: http://localhost:8001/api/docs
   - Vijitha API: http://localhost:8000/api/docs

7. **Monitor Console**
   - Eye Care: Console notifications
   - Posture: GUI window with real-time score
   - Workpattern: Console updates every 30 seconds

---

**Enjoy comprehensive health monitoring with AI! 🎉**
