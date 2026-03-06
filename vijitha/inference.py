"""
Model inference utilities for disease risk and stress detection
"""
import joblib
import pandas as pd
from pathlib import Path
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

MODELS_DIR = Path("models")


class DiseaseRiskInference:
    """Inference engine for disease risk prediction"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.features = {}
        self.loaded = False
    
    def load_models(self):
        """Load all trained disease models"""
        if self.loaded:
            return
        
        print("Loading disease risk models...")
        diseases = ['heart_disease', 'diabetes', 'hypertension']
        
        for disease in diseases:
            try:
                model_path = MODELS_DIR / f"{disease}_model.pkl"
                scaler_path = MODELS_DIR / f"{disease}_scaler.pkl"
                features_path = MODELS_DIR / f"{disease}_features.pkl"
                
                if model_path.exists():
                    self.models[disease] = joblib.load(model_path)
                    self.scalers[disease] = joblib.load(scaler_path)
                    self.features[disease] = joblib.load(features_path)
                    print(f"  ✓ Loaded {disease} model")
            except Exception as e:
                print(f"  ✗ Error loading {disease} model: {e}")
        
        self.loaded = len(self.models) > 0
        return self.loaded
    
    def prepare_input(self, input_data: dict) -> dict:
        """Prepare and engineer features from input"""
        # Calculate derived features
        features = input_data.copy()
        
        # Blood pressure ratio
        if 'systolic_bp' in features and 'diastolic_bp' in features:
            features['bp_ratio'] = features['systolic_bp'] / features['diastolic_bp']
        
        # Age-BMI interaction
        if 'age' in features and 'bmi' in features:
            features['age_bmi_interaction'] = features['age'] * features['bmi']
            features['age_squared'] = features['age'] ** 2
        
        # BMI-Cholesterol interaction
        if 'bmi' in features and 'cholesterol' in features:
            features['bmi_cholesterol_interaction'] = features['bmi'] * features['cholesterol'] / 100
        
        # Risk score calculation
        risk_score = 0
        if features.get('age', 0) > 50:
            risk_score += 0.2
        if features.get('bmi', 0) > 30:
            risk_score += 0.3
        if features.get('smoking', False):
            risk_score += 0.3
        if features.get('physical_activity_hours', 10) < 3:
            risk_score += 0.2
        features['risk_score'] = risk_score
        
        # Set default values for optional features
        features.setdefault('cholesterol', 200)
        features.setdefault('glucose', 100)
        features.setdefault('family_history', 0)
        
        # Convert boolean to int
        if 'smoking' in features:
            features['smoking'] = int(features['smoking'])
        if 'family_history' in features and isinstance(features['family_history'], bool):
            features['family_history'] = int(features['family_history'])
        
        return features
    
    def predict(self, input_data: dict) -> Dict[str, float]:
        """Predict disease risks"""
        if not self.loaded:
            if not self.load_models():
                raise RuntimeError("No trained models available")
        
        # Prepare features
        features = self.prepare_input(input_data)
        
        # Predict for each disease
        predictions = {}
        
        for disease, model in self.models.items():
            try:
                # Select required features
                required_features = self.features[disease]
                X = pd.DataFrame([features])[required_features]
                
                # Scale
                X_scaled = self.scalers[disease].transform(X)
                
                # Predict probability
                risk_prob = model.predict_proba(X_scaled)[0, 1] * 100
                predictions[disease] = round(risk_prob, 1)
                
            except Exception as e:
                print(f"Error predicting {disease}: {e}")
                predictions[disease] = 0.0
        
        return predictions
    
    def get_risk_level(self, predictions: Dict[str, float]) -> str:
        """Determine overall risk level"""
        avg_risk = sum(predictions.values()) / len(predictions) if predictions else 0
        
        if avg_risk < 30:
            return "Low"
        elif avg_risk < 60:
            return "Moderate"
        else:
            return "High"
    
    def generate_recommendations(self, input_data: dict, risk_level: str) -> List[str]:
        """Generate personalized health recommendations"""
        recommendations = []
        
        # Physical activity
        if input_data.get('physical_activity_hours', 0) < 3:
            recommendations.append("Increase physical activity to at least 150 minutes per week (30 min daily)")
        
        # Smoking
        if input_data.get('smoking', False):
            recommendations.append("Quit smoking - consult healthcare professional for cessation programs")
        
        # BMI
        bmi = input_data.get('bmi', 0)
        if bmi > 30:
            recommendations.append(f"Work on weight management - current BMI ({bmi:.1f}) is in obese range")
        elif bmi > 25:
            recommendations.append(f"Consider weight reduction - current BMI ({bmi:.1f}) is above normal range")
        
        # Blood pressure
        systolic = input_data.get('systolic_bp', 0)
        diastolic = input_data.get('diastolic_bp', 0)
        if systolic > 140 or diastolic > 90:
            recommendations.append("Monitor blood pressure regularly and reduce sodium intake")
        elif systolic > 130 or diastolic > 85:
            recommendations.append("Keep blood pressure in check through diet and lifestyle")
        
        # Diet
        diet_score = input_data.get('diet_quality_score', 10)
        if diet_score < 5:
            recommendations.append("Improve diet quality - increase vegetables, fruits, and whole grains")
        elif diet_score < 7:
            recommendations.append("Continue improving diet quality")
        
        # Risk-based recommendations
        if risk_level == "High":
            recommendations.append("Schedule comprehensive health screening with healthcare provider")
            recommendations.append("Consider consultation with a nutritionist or fitness trainer")
        elif risk_level == "Moderate":
            recommendations.append("Regular health check-ups are recommended")
        
        # General wellness
        if not recommendations:
            recommendations.append("Maintain current healthy lifestyle habits")
            recommendations.append("Continue regular health check-ups")
        
        return recommendations[:5]  # Return top 5


class StressDetectionInference:
    """Inference engine for stress detection"""
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.loaded = False
    
    def load_model(self):
        """Load trained stress detection model"""
        if self.loaded:
            return
        
        print("Loading stress detection model...")
        
        try:
            self.model = joblib.load(MODELS_DIR / "stress_tfidf_model.pkl")
            self.vectorizer = joblib.load(MODELS_DIR / "stress_vectorizer.pkl")
            self.label_encoder = joblib.load(MODELS_DIR / "stress_label_encoder.pkl")
            print("  ✓ Loaded TF-IDF stress model")
            self.loaded = True
        except Exception as e:
            print(f"  ✗ Error loading stress model: {e}")
            self.loaded = False
        
        return self.loaded
    
    def predict(self, text: str) -> dict:
        """Predict stress level from text"""
        if not self.loaded:
            if not self.load_model():
                raise RuntimeError("No trained stress model available")
        
        # Vectorize text
        X_tfidf = self.vectorizer.transform([text])
        
        # Predict
        pred_encoded = self.model.predict(X_tfidf)[0]
        pred_proba = self.model.predict_proba(X_tfidf)[0]
        
        # Decode
        stress_level = self.label_encoder.inverse_transform([pred_encoded])[0]
        confidence = float(pred_proba.max())
        
        # Get stress score (0-100)
        stress_mapping = {'Low': 15, 'Moderate': 45, 'High': 70, 'Critical': 90}
        stress_score = stress_mapping.get(stress_level, 50)
        
        return {
            'stress_level': stress_level,
            'stress_score': float(stress_score),
            'confidence': confidence
        }
    
    def extract_emotions(self, text: str) -> List[str]:
        """Extract emotions from text"""
        emotion_keywords = {
            "anxiety": ["anxious", "anxiety", "nervous", "worried", "panic"],
            "worry": ["worried", "concern", "fearful", "dread"],
            "exhaustion": ["exhausted", "tired", "fatigue", "drained", "worn out"],
            "frustration": ["frustrated", "irritated", "angry", "annoyed"],
            "sadness": ["sad", "depressed", "unhappy", "down", "miserable"],
            "overwhelm": ["overwhelmed", "trapped", "helpless", "lost", "stuck"],
            "fear": ["scared", "afraid", "frightened", "panic", "terrified"]
        }
        
        text_lower = text.lower()
        detected = []
        
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(emotion)
                    break
        
        return detected[:5] if detected else ["mild_stress"]
    
    def generate_recommendations(self, stress_level: str, emotions: List[str]) -> List[str]:
        """Generate stress management recommendations"""
        recommendations = []
        
        # Critical/High stress - immediate help
        if stress_level in ["Critical", "High"]:
            recommendations.append("Consider seeking professional mental health support")
            if stress_level == "Critical":
                recommendations.append("Contact a counselor or therapist immediately")
        
        # Breathing exercises
        recommendations.append("Practice breathing exercises (4-7-8 technique: 4 sec in, 7 sec hold, 8 sec out)")
        
        # Sleep management
        if "exhaustion" in emotions or stress_level in ["High", "Critical"]:
            recommendations.append("Prioritize sleep - aim for 7-8 hours with consistent schedule")
        
        # Screen time
        recommendations.append("Reduce screen time, especially before bed")
        
        # Mindfulness
        if stress_level in ["Moderate", "High", "Critical"]:
            recommendations.append("Practice mindfulness meditation (10-15 minutes daily)")
        
        # Activity and breaks
        recommendations.append("Take regular breaks during work (5-minute breaks every hour)")
        
        # Physical activity
        if "anxiety" in emotions or stress_level in ["High", "Critical"]:
            recommendations.append("Engage in physical activity - walking, yoga, or light exercise")
        
        # Social support
        if stress_level in ["High", "Critical"]:
            recommendations.append("Reach out to friends, family, or support groups")
        
        return recommendations[:5]
    
    def needs_professional_help(self, stress_level: str, stress_score: float) -> bool:
        """Determine if professional help is recommended"""
        return stress_level == "Critical" or stress_score > 70


# Global instances (lazy loaded)
_disease_predictor = None
_stress_predictor = None


def get_disease_predictor() -> DiseaseRiskInference:
    """Get or create disease risk predictor instance"""
    global _disease_predictor
    if _disease_predictor is None:
        _disease_predictor = DiseaseRiskInference()
    return _disease_predictor


def get_stress_predictor() -> StressDetectionInference:
    """Get or create stress detection predictor instance"""
    global _stress_predictor
    if _stress_predictor is None:
        _stress_predictor = StressDetectionInference()
    return _stress_predictor
