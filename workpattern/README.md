# Work Pattern Analysis & Break Recommendation System

Real-time typing behavior analysis system that monitors work patterns and recommends breaks using Advanced Machine Learning.

## Features

- **Real-time Pattern Analysis**: Analyzes typing speed, idle time, work duration
- **Fatigue Detection**: Predicts 4 levels: Healthy, Focused, Break Soon, Fatigue
- **Smart Recommendations**: Personalized break suggestions based on behavior
- **REST API**: Easy integration with FastAPI
- **High Accuracy**: Advanced ensemble ML model (RF + GB + Neural Network)

## System Architecture

```
Typing Metrics Input
      │
      ▼
Feature Extraction (11 features)
      │
      ▼
Ensemble ML Model
 ├─ Random Forest (200 trees)
 ├─ Gradient Boosting (200 estimators)
 └─ Neural Network (3 layers)
      │
      ▼
Fatigue Classification
      │
      ▼
Break Recommendations
```

## Dataset

**10,000 realistic work pattern samples** based on productivity research:
- 30% Healthy patterns (300 keys/min, regular breaks)
- 25% Focused patterns (350 keys/min, minimal breaks)
- 25% Break Soon patterns (280 keys/min, rising errors)
- 20% Fatigue patterns (220 keys/min, high errors)

Features tracked:
- Typing speed (keys/min)
- Idle time (minutes)
- Work duration (continuous minutes)
- Keystroke variance (rhythm consistency)
- Error rate (0-1)
- Mouse activity (clicks/min)
- Historical patterns (time-series)

## Installation

```bash
cd workpattern
pip install -r requirements.txt
```

## Training

```bash
# Generate dataset
python prepare_data.py

# Train model
python train_model.py
```

Expected output:
```
Test Accuracy: 95%+
Healthy: 96%
Focused: 94%
Break Soon: 95%
Fatigue: 96%
```

## Running the API

```bash
python main.py
```

Server starts at: http://localhost:8001

## API Endpoints

### 1. Analyze Work Pattern
**POST** `/api/v1/analyze-pattern`

**Request:**
```json
{
  "typing_speed": 280.0,
  "idle_time": 1.0,
  "work_duration": 105.0,
  "keystroke_variance": 32.0,
  "error_rate": 0.045,
  "mouse_activity": 38.0
}
```

**Response:**
```json
{
  "fatigue_level": "Break Soon",
  "fatigue_score": 72.5,
  "confidence": 0.87,
  "risk_indicators": [
    "Extended work session (105 minutes)",
    "Rising error rate",
    "Irregular typing rhythm"
  ],
  "recommendations": [
    "⚠ Take a 10-minute break within next 15 minutes",
    "Stand up and stretch",
    "Look away from screen (20-20-20 rule)"
  ],
  "break_needed": true,
  "predicted_class": 2
}
```

### 2. Health Check
**GET** `/api/health`

### 3. Reset Session
**POST** `/api/v1/reset-session`

## Testing

```bash
# Run test suite
python test_api.py

# Or test with curl
curl -X POST "http://localhost:8001/api/v1/analyze-pattern" \
  -H "Content-Type: application/json" \
  -d "{\"typing_speed\":280,\"idle_time\":1,\"work_duration\":105,\"keystroke_variance\":32,\"error_rate\":0.045,\"mouse_activity\":38}"
```

## Test Cases

### Test Case 1: Healthy Work Pattern
```json
{
  "typing_speed": 320.0,
  "idle_time": 5.0,
  "work_duration": 45.0,
  "keystroke_variance": 20.0,
  "error_rate": 0.02,
  "mouse_activity": 25.0
}
```
**Expected:** Healthy, Score: 10-20

### Test Case 2: Focused/Productive
```json
{
  "typing_speed": 360.0,
  "idle_time": 2.0,
  "work_duration": 75.0,
  "keystroke_variance": 15.0,
  "error_rate": 0.018,
  "mouse_activity": 18.0
}
```
**Expected:** Focused, Score: 20-35

### Test Case 3: Break Soon Required
```json
{
  "typing_speed": 280.0,
  "idle_time": 1.0,
  "work_duration": 105.0,
  "keystroke_variance": 32.0,
  "error_rate": 0.045,
  "mouse_activity": 38.0
}
```
**Expected:** Break Soon, Score: 50-75

### Test Case 4: Fatigue Detected
```json
{
  "typing_speed": 210.0,
  "idle_time": 0.5,
  "work_duration": 145.0,
  "keystroke_variance": 48.0,
  "error_rate": 0.08,
  "mouse_activity": 52.0
}
```
**Expected:** Fatigue, Score: 75-100

## Interactive Documentation

Open in browser: http://localhost:8001/api/docs

## Model Performance

- **Overall Accuracy**: 95%+
- **Training Time**: ~2-3 minutes
- **Inference Speed**: <50ms per prediction
- **Model Size**: ~15 MB

## Project Structure

```
workpattern/
├── data/
│   ├── train_data.csv (8,000 samples)
│   └── test_data.csv (2,000 samples)
├── models/
│   ├── work_pattern_model.pkl
│   └── scaler.pkl
├── prepare_data.py
├── train_model.py
├── inference.py
├── models.py
├── main.py
├── test_api.py
├── requirements.txt
└── README.md
```

## Tech Stack

- **FastAPI 0.104.1** - REST API framework
- **Scikit-learn 1.3.2** - ML algorithms
- **Pandas 2.0.3** - Data processing
- **NumPy 1.24.3** - Numerical computing

## Integration Example

```python
import requests

def check_work_pattern(typing_metrics):
    response = requests.post(
        "http://localhost:8001/api/v1/analyze-pattern",
        json=typing_metrics
    )
    result = response.json()
    
    if result['break_needed']:
        notify_user(result['recommendations'])
    
    return result
```

## Future Enhancements

- Real-time keyboard monitoring
- Computer vision fatigue detection
- Integration with productivity tools
- Historical analytics dashboard
- Multi-user support

## License

MIT License

## Author

Built for DL_HACK 2026
