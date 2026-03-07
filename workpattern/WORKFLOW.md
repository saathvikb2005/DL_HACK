# 🔄 WORKFLOW - Integrated Work Pattern System

## 📋 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOU TYPE ANYWHERE                            │
│         (WhatsApp, Chrome, Word, VS Code, etc.)                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              INTEGRATED MONITOR (Background)                    │
│  • Tracks keystrokes globally                                   │
│  • Tracks mouse clicks                                          │
│  • Calculates metrics every 30 seconds                          │
│  • Learns YOUR baseline (first 5 minutes)                       │
└───────┬────────────────────────────┬────────────────────────────┘
        │                            │
        │ Every 30 seconds           │ Stores data
        ▼                            ▼
┌──────────────────┐      ┌────────────────────────┐
│  TERMINAL        │      │  IN-MEMORY STORAGE     │
│  CONSOLE         │      │  • current_metrics     │
│                  │      │  • current_analysis    │
│  Real-time       │      │  • analysis_history    │
│  Updates:        │      └──────┬─────────────────┘
│                  │             │
│  [14:30:15]      │             │ API reads from here
│  ✅ Healthy      │             ▼
│  Score: 15%      │      ┌────────────────────────┐
│  Typing: 320/min │      │   FASTAPI SERVER       │
│  ─────────       │◄─────┤   (localhost:8001)     │
│  [14:30:45]      │      │                        │
│  🎯 Focused      │      │  3 NEW ENDPOINTS:      │
│  Score: 28%      │      │  /realtime-status      │
│                  │      │  /summary              │
│  ─────────       │      │  /stream               │
│  Every 30 min:   │      └────────┬───────────────┘
│  📊 SUMMARY      │               │
│  30 analyses     │               │ You access via browser
│  Avg: 35%        │               ▼
└──────────────────┘      ┌────────────────────────┐
                          │  YOUR BROWSER          │
                          │  localhost:8001/docs   │
                          │                        │
                          │  • See real-time data  │
                          │  • No manual input!    │
                          │  • Auto-updates        │
                          └────────────────────────┘
```

---

## 🎯 Step-by-Step Workflow

### 1️⃣ **Startup** (One Time)

```bash
# Start both monitor + API server
START_INTEGRATED.bat
```

**What happens**:
```
Monitor Window:
🚀 INTEGRATED WORK PATTERN SYSTEM
🔧 CALIBRATION MODE (if first time)
✓ Monitoring ALL applications
Monitoring your typing...

API Window:
INFO: Uvicorn running on http://0.0.0.0:8001
```

---

### 2️⃣ **Calibration** (First 5 Minutes)

**You**: Type normally in any app (WhatsApp, Chrome, etc.)

**Monitor Console**:
```
[CALIBRATION] Sample 1/10
  → Typing: 280 keys/min, Errors: 2.5%

[CALIBRATION] Sample 2/10
  → Typing: 295 keys/min, Errors: 2.1%

...

✅ CALIBRATION COMPLETE!
📊 Baseline: 287 keys/min, 2.3% errors
```

---

### 3️⃣ **Real-Time Monitoring** (Continuous)

#### Every 30 Seconds:

**Terminal Shows**:
```
[14:30:15] ✅ Healthy | Score: 15%
  → Typing: 290 keys/min (baseline: 287) | Mouse: 25 clicks/min
  → Work: 15m | Errors: 2.1%

[14:30:45] 🎯 Focused | Score: 28%
  → Typing: 310 keys/min (baseline: 287) | Mouse: 18 clicks/min
  → Work: 15m | Errors: 2.5%

[14:31:15] ⚠️ Break Soon | Score: 62%
  → Typing: 215 keys/min (baseline: 287) | Mouse: 42 clicks/min
  → Work: 90m | Errors: 4.8%
  ⚠ Typing 25% slower than baseline
  ⚠ More errors than usual
```

**API Updates Simultaneously** (no action needed!)

---

### 4️⃣ **Access Real-Time Data** (In Browser)

#### Option A: Swagger UI (Interactive)

Open: **http://localhost:8001/docs**

**You see**:
```
GET /api/v1/realtime-status
  Try it out → Execute
```

**Response** (NO INPUT NEEDED!):
```json
{
  "status": "active",
  "timestamp": "2026-03-07T14:30:15",
  "current_metrics": {
    "typing_speed": 290.0,
    "work_duration": 15.3,
    "error_rate": 0.021,
    "mouse_activity": 25.0
  },
  "current_analysis": {
    "fatigue_level": "Healthy",
    "fatigue_score": 15.0,
    "risk_indicators": [],
    "recommendations": ["Optimal work pattern", "Keep up the good pace"]
  },
  "session_info": {
    "session_duration": 15.3,
    "total_keystrokes": 4450,
    "baseline_typing": 287.0,
    "calibrated": true
  }
}
```

#### Option B: Live Stream

Open: **http://localhost:8001/api/v1/stream**

**You see** (auto-updates every 5 seconds):
```
data: {"timestamp":"2026-03-07T14:30:15","typing_speed":290,"fatigue_level":"Healthy","fatigue_score":15,"work_duration":15.3}

data: {"timestamp":"2026-03-07T14:30:20","typing_speed":295,"fatigue_level":"Healthy","fatigue_score":18,"work_duration":15.4}

data: {"timestamp":"2026-03-07T14:30:25","typing_speed":288,"fatigue_level":"Healthy","fatigue_score":16,"work_duration":15.5}
```

---

### 5️⃣ **30-Minute Summary** (Automatic)

#### In Terminal:
```
======================================================================
📊 30-MINUTE SUMMARY
======================================================================
⏱  Period: 30.2 minutes
⌨️  Total Keystrokes: 8,750
🖱  Total Mouse Clicks: 1,240

📈 Fatigue Analysis:
  • Average Score: 35.2%
  • Max Score: 68%
  • Min Score: 12%

📊 Distribution:
  • Healthy: 42 times (70.0%)
  • Focused: 12 times (20.0%)
  • Break Soon: 5 times (8.3%)
  • Fatigue: 1 times (1.7%)
======================================================================
```

#### In Browser API:

**GET** `http://localhost:8001/api/v1/summary`

**Response**:
```json
{
  "period_start": "2026-03-07T14:00:00",
  "period_end": "2026-03-07T14:30:00",
  "duration_minutes": 30.2,
  "total_keystrokes": 8750,
  "average_fatigue_score": 35.2,
  "max_fatigue_score": 68,
  "min_fatigue_score": 12,
  "fatigue_distribution": {
    "Healthy": 42,
    "Focused": 12,
    "Break Soon": 5,
    "Fatigue": 1
  },
  "total_analyses": 60,
  "baseline_typing": 287.0
}
```

---

## 🔄 Data Flow Timeline

```
Time    | You              | Monitor           | Terminal          | API Response
--------|------------------|-------------------|-------------------|------------------
00:00   | Start typing     | Captures keys     | [CALIBRATION]     | Status: waiting
00:30   |                  | Sample 1          | Sample 1/10       |
01:00   |                  | Sample 2          | Sample 2/10       |
...     |                  |                   |                   |
05:00   |                  | Calibrated! ✅    | ✅ COMPLETE!      | Calibrated: true
05:30   | Typing in Chrome | Analyze           | ✅ Healthy 15%    | GET /realtime → 15%
06:00   | Typing in Word   | Analyze           | ✅ Healthy 18%    | GET /realtime → 18%
06:30   | Still working    | Analyze           | 🎯 Focused 28%    | GET /realtime → 28%
...     |                  |                   |                   |
35:00   | (30 min mark)    | Generate summary  | 📊 SUMMARY        | GET /summary → JSON
35:30   | Typing in Code   | Analyze           | 🎯 Focused 32%    | GET /realtime → 32%
```

---

## 📡 API Endpoints Summary

| Endpoint | Method | Input Required? | Updates | Use Case |
|----------|--------|----------------|---------|----------|
| `/api/v1/realtime-status` | GET | ❌ NO | Every 30s | Current status |
| `/api/v1/summary` | GET | ❌ NO | Every 30min | Session summary |
| `/api/v1/stream` | GET | ❌ NO | Every 5s | Live stream |
| `/api/v1/analyze-pattern` | POST | ✅ YES | On demand | Manual testing |

---

## ✨ Key Features

1. **NO MANUAL INPUT** in `/realtime-status` - just open and see!
2. **Automatic Updates** - monitor runs in background
3. **Dual Output** - Terminal console + API server
4. **30-Minute Summaries** - automatic periodic reports
5. **Personalized** - learns YOUR typing baseline
6. **Works Everywhere** - any application, any text input

---

## 🚀 Quick Commands

```bash
# Start everything
START_INTEGRATED.bat

# View real-time in browser
http://localhost:8001/docs → GET /api/v1/realtime-status

# View live stream
http://localhost:8001/api/v1/stream

# Get 30-min summary
http://localhost:8001/api/v1/summary
```

**That's it! Type normally and see real-time results everywhere!** 🎯
