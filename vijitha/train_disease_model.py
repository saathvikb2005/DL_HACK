"""
Train ML models for lifestyle disease risk prediction
Uses Logistic Regression, Random Forest, and Gradient Boosting
"""
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')

# Paths
PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


class DiseaseRiskPredictor:
    """Train and save disease risk prediction models"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = [
            'age', 'bmi', 'systolic_bp', 'diastolic_bp',
            'smoking', 'physical_activity_hours', 'diet_quality_score',
            'cholesterol', 'glucose', 'family_history',
            'bp_ratio', 'age_bmi_interaction', 'risk_score',
            'age_squared', 'bmi_cholesterol_interaction'
        ]
    
    def load_data(self):
        """Load preprocessed data"""
        print("Loading data...")
        df = pd.read_csv(PROCESSED_DIR / "lifestyle_disease_processed.csv")
        print(f"✓ Loaded {len(df)} samples")
        return df
    
    def prepare_features(self, df, target_col):
        """Prepare features and target"""
        # Select features that exist in the dataframe
        available_features = [col for col in self.feature_columns if col in df.columns]
        
        X = df[available_features]
        y = df[target_col]
        
        return X, y, available_features
    
    def train_models(self, X_train, y_train, disease_name):
        """Train multiple models"""
        print(f"\n{'='*60}")
        print(f"Training models for {disease_name}")
        print(f"{'='*60}")
        
        models_to_train = {
            'logistic_regression': LogisticRegression(
                max_iter=2000, 
                random_state=42, 
                C=0.5,
                class_weight='balanced',
                solver='liblinear'
            ),
            'random_forest': RandomForestClassifier(
                n_estimators=100, 
                random_state=42, 
                max_depth=12,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100, 
                random_state=42, 
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                min_samples_split=5
            ),
            'xgboost': XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric='logloss',
                use_label_encoder=False,
                n_jobs=-1,
                verbosity=0
            )
        }
        
        trained_models = {}
        
        for model_name, model in models_to_train.items():
            print(f"\n{model_name.upper()}")
            print("-" * 40)
            
            # Train
            model.fit(X_train, y_train)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc')
            print(f"Cross-val AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
            
            trained_models[model_name] = model
        
        return trained_models
    
    def evaluate_models(self, models, X_test, y_test, disease_name):
        """Evaluate trained models"""
        print(f"\n{'='*60}")
        print(f"Evaluation Results for {disease_name}")
        print(f"{'='*60}")
        
        best_model_name = None
        best_auc = 0
        
        for model_name, model in models.items():
            print(f"\n{model_name.upper()}")
            print("-" * 40)
            
            # Predictions
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Metrics
            auc = roc_auc_score(y_test, y_pred_proba)
            print(f"AUC-ROC: {auc:.4f}")
            
            print("\nClassification Report:")
            print(classification_report(y_test, y_pred))
            
            # Track best model
            if auc > best_auc:
                best_auc = auc
                best_model_name = model_name
        
        print(f"\n✓ Best model: {best_model_name} (AUC: {best_auc:.4f})")
        return best_model_name
    
    def train_disease_model(self, df, disease_name, target_col):
        """Train models for a specific disease"""
        print(f"\n{'#'*60}")
        print(f"# {disease_name.upper()}")
        print(f"{'#'*60}")
        
        # Prepare data
        X, y, features = self.prepare_features(df, target_col)
        
        print(f"\nFeatures used: {features}")
        print(f"Positive cases: {y.sum()} ({y.mean()*100:.1f}%)")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train models
        models = self.train_models(X_train_scaled, y_train, disease_name)
        
        # Evaluate
        best_model_name = self.evaluate_models(
            models, X_test_scaled, y_test, disease_name
        )
        
        # Save best model and scaler
        best_model = models[best_model_name]
        model_path = MODELS_DIR / f"{disease_name.lower().replace(' ', '_')}_model.pkl"
        scaler_path = MODELS_DIR / f"{disease_name.lower().replace(' ', '_')}_scaler.pkl"
        
        joblib.dump(best_model, model_path)
        joblib.dump(scaler, scaler_path)
        joblib.dump(features, MODELS_DIR / f"{disease_name.lower().replace(' ', '_')}_features.pkl")
        
        print(f"\n✓ Model saved: {model_path}")
        print(f"✓ Scaler saved: {scaler_path}")
        
        return best_model, scaler, features
    
    def train_all(self):
        """Train all disease prediction models"""
        print("\n" + "="*60)
        print("DISEASE RISK MODEL TRAINING")
        print("="*60)
        
        # Load data
        df = self.load_data()
        
        # Train models for each disease
        diseases = [
            ('Heart Disease', 'heart_disease'),
            ('Diabetes', 'diabetes'),
            ('Hypertension', 'hypertension')
        ]
        
        for disease_name, target_col in diseases:
            if target_col in df.columns:
                model, scaler, features = self.train_disease_model(
                    df, disease_name, target_col
                )
                self.models[disease_name] = model
                self.scalers[disease_name] = scaler
            else:
                print(f"\n⚠ Warning: {target_col} not found in dataset. Skipping...")
        
        print("\n" + "="*60)
        print("✓ ALL MODELS TRAINED SUCCESSFULLY")
        print("="*60)
        print(f"\nModels saved in: {MODELS_DIR}")


class EnsemblePredictor:
    """Ensemble predictor that combines multiple models"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.features = {}
    
    def load_models(self):
        """Load all trained models"""
        print("\nLoading trained models...")
        
        diseases = ['heart_disease', 'diabetes', 'hypertension']
        
        for disease in diseases:
            try:
                model_path = MODELS_DIR / f"{disease}_model.pkl"
                scaler_path = MODELS_DIR / f"{disease}_scaler.pkl"
                features_path = MODELS_DIR / f"{disease}_features.pkl"
                
                self.models[disease] = joblib.load(model_path)
                self.scalers[disease] = joblib.load(scaler_path)
                self.features[disease] = joblib.load(features_path)
                
                print(f"✓ Loaded {disease} model")
            except Exception as e:
                print(f"✗ Error loading {disease} model: {e}")
    
    def predict(self, input_data):
        """Predict risk for all diseases"""
        predictions = {}
        
        for disease, model in self.models.items():
            try:
                # Prepare features
                features = self.features[disease]
                X = pd.DataFrame([input_data])[features]
                
                # Scale
                X_scaled = self.scalers[disease].transform(X)
                
                # Predict probability
                risk_prob = model.predict_proba(X_scaled)[0, 1] * 100
                predictions[disease] = round(risk_prob, 1)
            except Exception as e:
                print(f"Error predicting {disease}: {e}")
                predictions[disease] = 0.0
        
        return predictions


def main():
    """Main training pipeline"""
    # Train all models
    trainer = DiseaseRiskPredictor()
    trainer.train_all()
    
    # Test loading and prediction
    print("\n" + "="*60)
    print("TESTING MODEL INFERENCE")
    print("="*60)
    
    predictor = EnsemblePredictor()
    predictor.load_models()
    
    # Test prediction
    test_input = {
        'age': 45,
        'bmi': 28.5,
        'systolic_bp': 140,
        'diastolic_bp': 90,
        'smoking': 1,
        'physical_activity_hours': 2.5,
        'diet_quality_score': 5,
        'bp_ratio': 140/90,
        'age_bmi_interaction': 45 * 28.5,
        'risk_score': 0.5
    }
    
    print("\nTest input:", test_input)
    predictions = predictor.predict(test_input)
    print("\nPredictions:")
    for disease, risk in predictions.items():
        print(f"  {disease}: {risk}%")
    
    print("\n✓ Training and testing complete!")


if __name__ == "__main__":
    main()
