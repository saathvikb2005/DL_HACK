"""
Inference engine for Deep Learning LSTM model
"""
import numpy as np
import joblib
import os

os.environ['KERAS_BACKEND'] = 'numpy'

try:
    import keras
    KERAS_AVAILABLE = True
except:
    KERAS_AVAILABLE = False

class WorkPatternPredictor:
    """Real-time work pattern analysis using Deep Learning LSTM"""
    
    def __init__(self, model_dir='models'):
        self.model = None
        self.scaler = None
        self.feature_columns = [
            'typing_speed', 'idle_time', 'work_duration', 'keystroke_variance',
            'error_rate', 'mouse_activity', 'session_intensity',
            'prev_typing_speed_1', 'prev_typing_speed_2',
            'prev_work_duration_1', 'prev_idle_time_1'
        ]
        self.class_names = ['Healthy', 'Focused', 'Break Soon', 'Fatigue']
        self.history = []
        self.sequence_length = 5
        self.load_models(model_dir)
    
    def load_models(self, model_dir):
        """Load trained Deep Learning LSTM model"""
        model_path = os.path.join(model_dir, 'work_pattern_dl.pkl')
        scaler_path = os.path.join(model_dir, 'scaler.pkl')
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                print("✓ Deep Learning LSTM model loaded")
            except Exception as e:
                print(f"⚠ Failed to load model: {e}")
                print("Using rule-based fallback")
        else:
            print("⚠ Model files not found. Using rule-based fallback.")
    
    def prepare_features(self, input_data):
        """Prepare features with historical context"""
        session_intensity = input_data['typing_speed'] / 500.0
        
        if len(self.history) >= 2:
            prev_typing_1 = self.history[-1]['typing_speed']
            prev_typing_2 = self.history[-2]['typing_speed']
            prev_work_1 = self.history[-1]['work_duration']
            prev_idle_1 = self.history[-1]['idle_time']
        elif len(self.history) == 1:
            prev_typing_1 = self.history[-1]['typing_speed']
            prev_typing_2 = input_data['typing_speed']
            prev_work_1 = self.history[-1]['work_duration']
            prev_idle_1 = self.history[-1]['idle_time']
        else:
            prev_typing_1 = input_data['typing_speed']
            prev_typing_2 = input_data['typing_speed']
            prev_work_1 = input_data['work_duration']
            prev_idle_1 = input_data['idle_time']
        
        features = [
            input_data['typing_speed'],
            input_data['idle_time'],
            input_data['work_duration'],
            input_data['keystroke_variance'],
            input_data['error_rate'],
            input_data['mouse_activity'],
            session_intensity,
            prev_typing_1,
            prev_typing_2,
            prev_work_1,
            prev_idle_1
        ]
        
        self.history.append(input_data)
        if len(self.history) > 5:
            self.history.pop(0)
        
        return np.array([features])
    
    def predict(self, input_data):
        """Make prediction using Deep Learning LSTM"""
        features = self.prepare_features(input_data)
        
        if self.model is not None:
            # Normalize
            features_scaled = (features - self.scaler['mean']) / self.scaler['std']
            
            # Create sequence for LSTM
            sequence = np.repeat(features_scaled[np.newaxis, :, :], self.sequence_length, axis=1)
            
            # Predict with Deep Learning model
            predictions = self.model.predict(sequence)
            predicted_class = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class])
            fatigue_score = float(predictions[0][2] * 50 + predictions[0][3] * 100)
        else:
            predicted_class, confidence = self._rule_based_prediction(input_data)
            fatigue_score = predicted_class * 33.3
        
        result = {
            'fatigue_level': self.class_names[predicted_class],
            'fatigue_score': round(fatigue_score, 1),
            'confidence': round(confidence, 2),
            'risk_indicators': self._identify_risks(input_data, predicted_class),
            'recommendations': self._generate_recommendations(input_data, predicted_class),
            'break_needed': predicted_class >= 2,
            'predicted_class': int(predicted_class)
        }
        
        return result
    
    def _rule_based_prediction(self, data):
        """Fallback rule-based prediction"""
        score = 0
        
        if data['work_duration'] > 120:
            score += 3
        elif data['work_duration'] > 90:
            score += 2
        elif data['work_duration'] > 60:
            score += 1
        
        if data['idle_time'] < 1:
            score += 2
        elif data['idle_time'] < 3:
            score += 1
        
        if data['error_rate'] > 0.05:
            score += 2
        elif data['error_rate'] > 0.03:
            score += 1
        
        if data['typing_speed'] < 250:
            score += 2
        elif data['typing_speed'] < 280:
            score += 1
        
        if score >= 6:
            return 3, 0.80
        elif score >= 4:
            return 2, 0.75
        elif score >= 2:
            return 1, 0.70
        else:
            return 0, 0.85
    
    def _identify_risks(self, data, predicted_class):
        """Identify specific risk factors"""
        risks = []
        
        if data['work_duration'] > 120:
            risks.append(f"Very long work session ({data['work_duration']:.0f} minutes)")
        elif data['work_duration'] > 90:
            risks.append(f"Extended work session ({data['work_duration']:.0f} minutes)")
        
        if data['idle_time'] < 2:
            risks.append("Insufficient breaks")
        
        if data['error_rate'] > 0.05:
            risks.append("High error rate - possible fatigue")
        elif data['error_rate'] > 0.03:
            risks.append("Rising error rate")
        
        if data['typing_speed'] < 250:
            risks.append("Significantly reduced typing speed")
        
        if data['keystroke_variance'] > 35:
            risks.append("Irregular typing rhythm - inconsistent focus")
        
        if data['mouse_activity'] > 45:
            risks.append("High mouse activity - possible distraction")
        
        if not risks:
            risks.append("No significant risks detected")
        
        return risks
    
    def _generate_recommendations(self, data, predicted_class):
        """Generate personalized recommendations"""
        recommendations = []
        
        if predicted_class == 3:
            recommendations.append("🚨 Take an immediate 15-20 minute break")
            recommendations.append("Stand up and move around to restore circulation")
            recommendations.append("Step away from computer completely")
            recommendations.append("Consider ending work session if possible")
        elif predicted_class == 2:
            recommendations.append("⚠ Take a 10-minute break within next 15 minutes")
            recommendations.append("Stand up and stretch")
            recommendations.append("Look away from screen (20-20-20 rule)")
            recommendations.append("Hydrate - drink water")
        elif predicted_class == 1:
            recommendations.append("✓ Good work pattern - maintain current pace")
            recommendations.append("Remember to take short breaks every 45-60 minutes")
            recommendations.append("Stay hydrated")
        else:
            recommendations.append("✓ Healthy work pattern")
            recommendations.append("Continue with regular break intervals")
            recommendations.append("Maintain good posture")
        
        if data['error_rate'] > 0.04:
            recommendations.append("High error rate detected - slow down for accuracy")
        
        if data['work_duration'] > 90 and predicted_class < 2:
            recommendations.append("Consider taking a short break soon (90+ min work session)")
        
        return recommendations
    
    def reset_history(self):
        """Reset historical context"""
        self.history = []

predictor = None

def get_predictor():
    """Get or create predictor instance"""
    global predictor
    if predictor is None:
        predictor = WorkPatternPredictor()
    return predictor
