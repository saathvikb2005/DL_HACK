<!-- markdownlint-disable MD024 -->

# AI Health Platform - Quick Start Guide

## 🚀 Quick Setup (Automated)

### Option 1: One-Click Setup (Windows)

```bash
setup_and_train.bat
```

### Option 2: One-Click Setup (Linux/Mac)

```bash
chmod +x setup_and_train.sh
./setup_and_train.sh
```

This will automatically:

1. Install all dependencies
2. Download and prepare datasets
3. Train disease risk models (Logistic Regression, Random Forest, Gradient Boosting)
4. Train stress detection models (TF-IDF + Naive Bayes)
5. Save trained models for API use

---

## 📋 Manual Setup

### Step 1: Install Dependencies

```bash
# Install from project root
cd ..
pip install -r requirements.txt
cd vijitha
```

### Step 2: Prepare Datasets

```bash
python prepare_data.py
```

Creates synthetic datasets and downloads real ones if available.

### Step 3: Train ML Models

```bash
# Train disease risk prediction models
python train_disease_model.py

# Train mental health stress detection models
python train_stress_model.py
```

### Step 4: Start API Server

```bash
python main.py
```

The API will be available at `<http://localhost:8000>`

**📖 Interactive Docs:** <http://localhost:8000/api/docs>

---

## API Endpoints

### Health Check

**GET** `/health`

```json
{
  "status": "healthy",
  "message": "AI Health Platform API is running",
  "version": "1.0.0"
}
```

---

## 1️⃣ Lifestyle Disease Risk Predictor

**POST** `/api/v1/disease-risk`

### Request Example

```json
{
  "age": 45,
  "bmi": 28.5,
  "systolic_bp": 140,
  "diastolic_bp": 90,
  "smoking": true,
  "physical_activity_hours": 2.5,
  "diet_quality_score": 5
}
```

### Response Example

```json
{
  "heart_disease_risk": 31.5,
  "diabetes_risk": 24.2,
  "hypertension_risk": 45.8,
  "risk_level": "Moderate",
  "recommendations": [
    "Increase physical activity to at least 30 minutes daily",
    "Reduce salt intake",
    "Quit smoking",
    "Monitor blood pressure regularly"
  ]
}
```

### Input Parameters

| Field | Type | Range | Description |
| ----- | ---- | ----- | ----------- |
| age | int | 0-150 | Age in years |
| bmi | float | 10-60 | Body Mass Index |
| systolic_bp | int | 60-250 | Systolic blood pressure (mmHg) |
| diastolic_bp | int | 30-150 | Diastolic blood pressure (mmHg) |
| smoking | bool | - | Current smoker (true/false) |
| physical_activity_hours | float | 0-24 | Physical activity hours per week |
| diet_quality_score | int | 1-10 | Diet quality score (1=poor, 10=excellent) |

### Output Parameters

| Field | Type | Description |
| ----- | ---- | ----------- |
| heart_disease_risk | float | Heart disease risk percentage (0-100) |
| diabetes_risk | float | Diabetes risk percentage (0-100) |
| hypertension_risk | float | Hypertension risk percentage (0-100) |
| risk_level | string | Low/Moderate/High |
| recommendations | array | List of health recommendations |

### Models Used

- Logistic Regression
- Random Forest
- Gradient Boosting

### Dataset Sources

- UCI Heart Disease Dataset
- PIMA Diabetes Dataset
- Kaggle health datasets

---

## 2️⃣ Mental Health Stress Detection

**POST** `/api/v1/stress-detection`

### Request Example

```json
{
  "user_text": "I feel very anxious and unable to sleep because of work pressure. My mind keeps running and I can't focus on anything.",
  "age": 32,
  "gender": "M"
}
```

### Response Example

```json
{
  "stress_level": "Moderate",
  "stress_score": 65.5,
  "confidence": 0.87,
  "detected_emotions": ["anxiety", "worry", "exhaustion"],
  "suggested_actions": [
    "Practice breathing exercises (4-7-8 breathing technique)",
    "Reduce screen time before bed",
    "Improve sleep schedule - aim for 7-8 hours",
    "Take short breaks during work",
    "Practice meditation or mindfulness"
  ],
  "professional_help_needed": false
}
```

### Input Parameters

| Field | Type | Length | Description |
| ----- | ---- | ------ | ----------- |
| user_text | string | 10-2000 | User text or questionnaire responses |
| age | int | Optional | Age in years |
| gender | string | Optional | Gender (M/F/Other) |

### Output Parameters

| Field | Type | Description |
| ----- | ---- | ----------- |
| stress_level | string | Low/Moderate/High/Critical |
| stress_score | float | Numerical stress score (0-100) |
| confidence | float | Model confidence (0-1) |
| detected_emotions | array | Detected emotions from text |
| suggested_actions | array | Recommended interventions |
| professional_help_needed | bool | Whether professional help is needed |

### Models Available

#### Basic

- TF-IDF + Naive Bayes

#### Advanced

- BERT (transformer-based NLP model)

### Dataset Sources

- Kaggle mental health datasets
- Reddit mental health dataset
- Sentiment analysis datasets

---

## Testing with cURL

### Test Disease Risk Predictor

```bash
curl -X POST "http://localhost:8000/api/v1/disease-risk" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "bmi": 28.5,
    "systolic_bp": 140,
    "diastolic_bp": 90,
    "smoking": true,
    "physical_activity_hours": 2.5,
    "diet_quality_score": 5
  }'
```

### Test Stress Detection

```bash
curl -X POST "http://localhost:8000/api/v1/stress-detection" \
  -H "Content-Type: application/json" \
  -d '{
    "user_text": "I feel very anxious and unable to sleep because of work pressure.",
    "age": 32
  }'
```

---

## Interactive API Documentation

Once the server is running, visit:

- **Swagger UI**: <http://localhost:8000/api/docs>
- **ReDoc**: <http://localhost:8000/api/redoc>

---

## Project Structure

```text
vijitha/
├── main.py              # FastAPI application
├── models.py            # Pydantic data models
└── README.md           # This file

**Note:** Dependencies are in the root `../requirements.txt` file.
```

---

## Future Enhancements

1. **ML Model Integration**
   - Load trained sklearn/PyTorch models
   - Implement proper prediction logic
   - Add model versioning

2. **Authentication**
   - JWT token authentication
   - Rate limiting

3. **Database**
   - Store prediction history
   - User profiles

4. **Advanced NLP**
   - Integrate BERT for better stress detection
   - Multi-language support

5. **Monitoring**
   - Add logging
   - Performance metrics
   - Error tracking

---

## License

MIT
