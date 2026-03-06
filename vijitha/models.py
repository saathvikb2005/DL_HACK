from pydantic import BaseModel, Field
from typing import Optional


# ==================== Lifestyle Disease Risk Predictor Models ====================

class LifestyleDiseaseInput(BaseModel):
    """Input model for lifestyle disease risk prediction"""
    age: int = Field(..., ge=0, le=150, description="Age in years")
    bmi: float = Field(..., ge=10, le=60, description="Body Mass Index")
    systolic_bp: int = Field(..., ge=60, le=250, description="Systolic blood pressure")
    diastolic_bp: int = Field(..., ge=30, le=150, description="Diastolic blood pressure")
    smoking: bool = Field(..., description="Current smoker (true/false)")
    physical_activity_hours: float = Field(..., ge=0, le=24, description="Physical activity hours per week")
    diet_quality_score: int = Field(..., ge=1, le=10, description="Diet quality score (1-10)")
    
    class Config:
        example = {
            "age": 45,
            "bmi": 28.5,
            "systolic_bp": 140,
            "diastolic_bp": 90,
            "smoking": True,
            "physical_activity_hours": 2.5,
            "diet_quality_score": 5
        }


class DiseaseRiskOutput(BaseModel):
    """Output model for disease risk predictions"""
    heart_disease_risk: float = Field(..., ge=0, le=100, description="Heart disease risk percentage")
    diabetes_risk: float = Field(..., ge=0, le=100, description="Diabetes risk percentage")
    hypertension_risk: float = Field(..., ge=0, le=100, description="Hypertension risk percentage")
    risk_level: str = Field(..., description="Overall risk level: Low, Moderate, High")
    recommendations: list[str] = Field(..., description="Health recommendations")
    
    class Config:
        example = {
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


# ==================== Mental Health Stress Detection Models ====================

class StressDetectionInput(BaseModel):
    """Input model for stress level detection"""
    user_text: str = Field(..., min_length=10, max_length=2000, description="User text or questionnaire responses")
    age: Optional[int] = Field(None, ge=0, le=150, description="Age (optional)")
    gender: Optional[str] = Field(None, description="Gender (optional)")
    
    class Config:
        example = {
            "user_text": "I feel very anxious and unable to sleep because of work pressure. My mind keeps running and I can't focus on anything.",
            "age": 32,
            "gender": "M"
        }


class StressDetectionOutput(BaseModel):
    """Output model for stress detection"""
    stress_level: str = Field(..., description="Stress level: Low, Moderate, High, Critical")
    stress_score: float = Field(..., ge=0, le=100, description="Numerical stress score (0-100)")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence (0-1)")
    detected_emotions: list[str] = Field(..., description="Detected emotions from text")
    suggested_actions: list[str] = Field(..., description="Recommended interventions")
    professional_help_needed: bool = Field(..., description="Whether professional help is recommended")
    
    class Config:
        example = {
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
            "professional_help_needed": False
        }


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    version: str
    
    class Config:
        example = {
            "status": "healthy",
            "message": "AI Health Platform API is running",
            "version": "1.0.0"
        }
