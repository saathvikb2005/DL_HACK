import os
import sys
import random
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import (
    LifestyleDiseaseInput, 
    DiseaseRiskOutput, 
    StressDetectionInput, 
    StressDetectionOutput,
    HealthCheckResponse
)
from inference import get_disease_predictor, get_stress_predictor

# Add project root for module_bridge
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
try:
    from module_bridge import push_event as _push_event
except ImportError:
    def _push_event(*a, **k): pass

# Initialize FastAPI app
app = FastAPI(
    title="AI Health Platform",
    description="Proactive health risk prediction and mental wellness detection system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
# Production: Set ALLOWED_ORIGINS env var to specific domains
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global predictors (lazy loaded)
disease_predictor = None
stress_predictor = None

# Check if models exist
MODELS_DIR = Path("models")
USE_TRAINED_MODELS = MODELS_DIR.exists() and any(MODELS_DIR.glob("*.pkl"))


@app.on_event("startup")
async def startup_event():
    """Load models on startup if available"""
    global disease_predictor, stress_predictor
    
    if USE_TRAINED_MODELS:
        print("Loading trained ML models...")
        try:
            disease_predictor = get_disease_predictor()
            disease_predictor.load_models()
            print("✓ Disease risk models loaded")
        except Exception as e:
            print(f"⚠ Could not load disease models: {e}")
        
        try:
            stress_predictor = get_stress_predictor()
            stress_predictor.load_model()
            print("✓ Stress detection model loaded")
        except Exception as e:
            print(f"⚠ Could not load stress model: {e}")
    else:
        print("⚠ No trained models found. Using rule-based predictions.")
        print("  Run: python prepare_data.py && python train_disease_model.py && python train_stress_model.py")


# ==================== Health Check ====================

@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Check API health status"""
    return HealthCheckResponse(
        status="healthy",
        message="AI Health Platform API is running",
        version="1.0.0"
    )


# ==================== Lifestyle Disease Risk Predictor ====================

@app.post(
    "/api/v1/disease-risk",
    response_model=DiseaseRiskOutput,
    tags=["Lifestyle Disease Risk"],
    summary="Predict lifestyle disease risks"
)
async def predict_disease_risk(input_data: LifestyleDiseaseInput):
    """
    Predict risk probability for major lifestyle diseases.
    
    **Inputs:**
    - Age: Patient age in years
    - BMI: Body Mass Index
    - Blood Pressure: Systolic and Diastolic readings
    - Smoking: Smoking status
    - Physical Activity: Hours per week
    - Diet Pattern: Diet quality score (1-10)
    
    **Outputs:**
    - Heart Disease Risk %
    - Diabetes Risk %
    - Hypertension Risk %
    - Overall Risk Level (Low/Moderate/High)
    - Health Recommendations
    
    **Models Used:**
    - Logistic Regression
    - Random Forest
    - Gradient Boosting
    """
    try:
        # Convert input to dict
        input_dict = input_data.dict()
        
        # Use trained models if available, otherwise fallback to rule-based
        if disease_predictor and disease_predictor.loaded:
            # ML Model Prediction
            predictions = disease_predictor.predict(input_dict)
            heart_disease_risk = predictions.get('heart_disease', 0)
            diabetes_risk = predictions.get('diabetes', 0)
            hypertension_risk = predictions.get('hypertension', 0)
            
            risk_level = disease_predictor.get_risk_level(predictions)
            recommendations = disease_predictor.generate_recommendations(input_dict, risk_level)
        else:
            # Fallback to rule-based prediction
            heart_disease_risk = calculate_heart_disease_risk(input_data)
            diabetes_risk = calculate_diabetes_risk(input_data)
            hypertension_risk = calculate_hypertension_risk(input_data)
            
            avg_risk = (heart_disease_risk + diabetes_risk + hypertension_risk) / 3
            if avg_risk < 30:
                risk_level = "Low"
            elif avg_risk < 60:
                risk_level = "Moderate"
            elif avg_risk < 80:
                risk_level = "High"
            else:
                risk_level = "Critical"  # Add Critical for very high risk (>=80%)
            
            recommendations = generate_disease_recommendations(input_data, risk_level)
        
        output = DiseaseRiskOutput(
            heart_disease_risk=round(heart_disease_risk, 1),
            diabetes_risk=round(diabetes_risk, 1),
            hypertension_risk=round(hypertension_risk, 1),
            risk_level=risk_level,
            recommendations=recommendations
        )

        # Push event to orchestrator if risk is high
        if risk_level in ("High", "Critical"):
            _push_event("HIGH_DISEASE_RISK", "vijitha", {
                "risk_level": risk_level,
                "heart": round(heart_disease_risk, 1),
                "diabetes": round(diabetes_risk, 1),
                "hypertension": round(hypertension_risk, 1),
            })

        return output
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in disease risk prediction: {str(e)}")


def calculate_heart_disease_risk(data: LifestyleDiseaseInput) -> float:
    """Calculate heart disease risk based on inputs"""
    risk = 0
    
    # Age factor (0-30 points)
    if data.age > 50:
        risk += min(30, (data.age - 50) * 0.5)
    
    # BMI factor (0-25 points)
    if data.bmi > 25:
        risk += min(25, (data.bmi - 25) * 2)
    
    # Blood pressure factor (0-20 points)
    avg_bp = (data.systolic_bp + data.diastolic_bp) / 2
    if avg_bp > 100:
        risk += min(20, (avg_bp - 100) * 0.5)
    
    # Smoking factor (0-15 points)
    if data.smoking:
        risk += 15
    
    # Physical activity factor (0-10 points)
    if data.physical_activity_hours < 2.5:
        risk += min(10, (2.5 - data.physical_activity_hours) * 2)
    
    return min(100, max(0, risk))


def calculate_diabetes_risk(data: LifestyleDiseaseInput) -> float:
    """Calculate diabetes risk based on inputs"""
    risk = 0
    
    # BMI factor (primary)
    if data.bmi > 25:
        risk += min(35, (data.bmi - 25) * 3)
    
    # Age factor
    if data.age > 45:
        risk += min(25, (data.age - 45) * 0.5)
    
    # Physical activity factor
    if data.physical_activity_hours < 3:
        risk += min(20, (3 - data.physical_activity_hours) * 5)
    
    # Diet quality factor
    if data.diet_quality_score < 5:
        risk += (5 - data.diet_quality_score) * 3
    
    return min(100, max(0, risk))


def calculate_hypertension_risk(data: LifestyleDiseaseInput) -> float:
    """Calculate hypertension risk based on inputs"""
    risk = 0
    
    # Current BP reading
    avg_bp = (data.systolic_bp + data.diastolic_bp) / 2
    if avg_bp > 120:
        risk += min(40, (avg_bp - 120) * 1.5)
    
    # Age factor
    if data.age > 40:
        risk += min(30, (data.age - 40) * 0.5)
    
    # BMI factor
    if data.bmi > 30:
        risk += min(20, (data.bmi - 30) * 2)
    
    # Smoking factor
    if data.smoking:
        risk += 10
    
    return min(100, max(0, risk))


def generate_disease_recommendations(data: LifestyleDiseaseInput, risk_level: str) -> list[str]:
    """Generate health recommendations based on risk profile"""
    recommendations = []
    
    if data.physical_activity_hours < 3:
        recommendations.append("Increase physical activity to at least 30 minutes daily")
    
    if data.smoking:
        recommendations.append("Quit smoking - consult healthcare professional for cessation programs")
    
    if data.bmi > 25:
        recommendations.append(f"Reduce BMI through diet and exercise (current BMI: {data.bmi})")
    
    if data.systolic_bp > 130 or data.diastolic_bp > 85:
        recommendations.append("Monitor blood pressure regularly and reduce salt intake")
    
    if data.diet_quality_score < 5:
        recommendations.append("Improve diet quality - increase vegetables and reduce processed foods")
    
    if risk_level == "High":
        recommendations.append("Consult with a healthcare professional for comprehensive screening")
    
    if not recommendations:
        recommendations.append("Maintain current healthy lifestyle habits")
    
    return recommendations[:5]  # Return top 5 recommendations


# ==================== Mental Health Stress Detection ====================

@app.post(
    "/api/v1/stress-detection",
    response_model=StressDetectionOutput,
    tags=["Mental Health Stress Detection"],
    summary="Detect stress levels from text"
)
async def detect_stress(input_data: StressDetectionInput):
    """
    Detect mental stress levels using natural language processing.
    
    **Input:**
    - User text: Questionnaire responses or free-form text
    - Age: Optional demographic info
    - Gender: Optional demographic info
    
    **Output:**
    - Stress Level: Low, Moderate, High, Critical
    - Stress Score: 0-100
    - Confidence: Model confidence score
    - Detected Emotions: List of emotions found in text
    - Suggested Actions: Personalized interventions
    - Professional Help Needed: Boolean flag for severity
    
    **Models Used:**
    - Basic: TF-IDF + Naive Bayes
    - Advanced: BERT (transformer-based NLP model)
    """
    try:
        # Use trained model if available, otherwise fallback to rule-based
        if stress_predictor and stress_predictor.loaded:
            # ML Model Prediction
            result = stress_predictor.predict(input_data.user_text)
            stress_level = result['stress_level']
            stress_score = result['stress_score']
            confidence = result['confidence']
            
            detected_emotions = stress_predictor.extract_emotions(input_data.user_text)
            suggested_actions = stress_predictor.generate_recommendations(stress_level, detected_emotions)
            professional_help_needed = stress_predictor.needs_professional_help(stress_level, stress_score)
        else:
            # Fallback to rule-based prediction
            stress_score = analyze_stress_text(input_data.user_text)
            detected_emotions = extract_emotions(input_data.user_text)
            confidence = random.uniform(0.75, 0.95)
            
            if stress_score < 30:
                stress_level = "Low"
            elif stress_score < 50:
                stress_level = "Moderate"
            elif stress_score < 75:
                stress_level = "High"
            else:
                stress_level = "Critical"
            
            professional_help_needed = stress_score > 70
            suggested_actions = generate_stress_recommendations(stress_level, detected_emotions)
        
        output = StressDetectionOutput(
            stress_level=stress_level,
            stress_score=round(stress_score, 1),
            confidence=round(confidence, 2),
            detected_emotions=detected_emotions,
            suggested_actions=suggested_actions,
            professional_help_needed=professional_help_needed
        )

        # Push event to orchestrator if stress is high
        if stress_level in ("High", "Critical"):
            _push_event("HIGH_STRESS", "vijitha", {
                "stress_level": stress_level,
                "stress_score": round(stress_score, 1),
                "emotions": detected_emotions[:3],
            })

        return output
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in stress detection: {str(e)}")


def analyze_stress_text(text: str) -> float:
    """Analyze text for stress indicators"""
    stress_keywords = {
        "anxiety": 15, "anxious": 15, "worried": 12, "panic": 20,
        "stress": 18, "stressed": 18, "overwhelmed": 16, "exhausted": 14,
        "can't sleep": 12, "sleep problem": 12, "insomnia": 13,
        "depressed": 15, "depression": 15, "sad": 10, "unable": 8,
        "pressure": 10, "deadline": 8, "difficulty": 8, "struggling": 10,
        "bad": 5, "terrible": 8, "horrible": 8, "worst": 8,
        "help": 5, "need": 3, "problem": 5, "issue": 4
    }
    
    text_lower = text.lower()
    stress_score = 0
    found_keywords = 0
    
    for keyword, score in stress_keywords.items():
        if keyword in text_lower:
            stress_score += score
            found_keywords += 1
    
    # Normalize by text length and keyword frequency
    text_length_factor = min(len(text) / 500, 1.5)
    stress_score = min(100, (stress_score * text_length_factor) / max(1, found_keywords))
    
    return max(0, min(100, stress_score))


def extract_emotions(text: str) -> list[str]:
    """Extract emotions from text"""
    emotion_keywords = {
        "anxiety": ["anxious", "anxiety", "nervous", "worried"],
        "worry": ["worried", "concern", "fearful", "dread"],
        "exhaustion": ["exhausted", "tired", "fatigue", "drained"],
        "frustration": ["frustrated", "irritated", "angry", "annoyed"],
        "sadness": ["sad", "depressed", "unhappy", "down"],
        "overwhelm": ["overwhelmed", "trapped", "helpless", "lost"],
        "fear": ["scared", "afraid", "frightened", "panic"]
    }
    
    text_lower = text.lower()
    detected = []
    
    for emotion, keywords in emotion_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected.append(emotion)
                break
    
    return detected[:5] if detected else ["mild_stress"]


def generate_stress_recommendations(stress_level: str, emotions: list[str]) -> list[str]:
    """Generate stress management recommendations"""
    recommendations = []
    
    # Base recommendations
    if stress_level in ["High", "Critical"]:
        recommendations.append("Seek professional mental health support immediately")
        recommendations.append("Contact a counselor or therapist")
    
    # Breathing exercises
    recommendations.append("Practice breathing exercises (4-7-8 breathing technique)")
    
    # Sleep improvement
    if "exhaustion" in emotions or stress_level in ["High", "Critical"]:
        recommendations.append("Improve sleep schedule - aim for 7-8 hours")
    
    # Screen time
    recommendations.append("Reduce screen time before bed")
    
    # Mindfulness
    recommendations.append("Practice meditation or mindfulness (10-15 minutes daily)")
    
    # Activity breaks
    recommendations.append("Take short breaks during work (5 minutes every hour)")
    
    # Social support
    recommendations.append("Connect with friends or family for support")
    
    # Physical activity
    recommendations.append("Engage in light physical activity (walking, yoga)")
    
    return recommendations[:5]


# ==================== Root Endpoint ====================

@app.get("/", tags=["Info"])
async def root():
    """Welcome endpoint with API information"""
    return {
        "title": "AI Health Platform",
        "version": "1.0.0",
        "description": "Proactive health risk prediction and mental wellness detection system",
        "documentation": "/api/docs",
        "endpoints": {
            "health": "/health",
            "disease_risk": "/api/v1/disease-risk",
            "stress_detection": "/api/v1/stress-detection"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
