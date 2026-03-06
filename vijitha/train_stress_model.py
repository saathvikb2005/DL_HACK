"""
Train NLP models for mental health stress detection
Uses TF-IDF + Naive Bayes (basic) and BERT (advanced)
"""
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Optional: Try to import transformers for BERT
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
    import torch
    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False
    print("⚠ Transformers not available. Will train only TF-IDF model.")

# Paths
PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


class StressDetectionTrainer:
    """Train stress detection models"""
    
    def __init__(self):
        self.tfidf_model = None
        self.vectorizer = None
        self.label_encoder = None
    
    def load_data(self):
        """Load preprocessed mental health data"""
        print("Loading data...")
        df = pd.read_csv(PROCESSED_DIR / "mental_health_processed.csv")
        print(f"✓ Loaded {len(df)} samples")
        print(f"\nStress level distribution:")
        print(df['stress_level'].value_counts())
        return df
    
    def train_tfidf_model(self, df):
        """Train TF-IDF + Naive Bayes model"""
        print("\n" + "="*60)
        print("TRAINING TF-IDF + NAIVE BAYES MODEL")
        print("="*60)
        
        # Prepare data
        X = df['text']
        y = df['stress_level']
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\nTraining samples: {len(X_train)}")
        print(f"Test samples: {len(X_test)}")
        
        # TF-IDF Vectorization
        print("\nVectorizing text...")
        self.vectorizer = TfidfVectorizer(
            max_features=8000,
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.9,
            stop_words='english',
            sublinear_tf=True,
            use_idf=True
        )
        
        X_train_tfidf = self.vectorizer.fit_transform(X_train)
        X_test_tfidf = self.vectorizer.transform(X_test)
        
        print(f"✓ Vocabulary size: {len(self.vectorizer.vocabulary_)}")
        
        # Encode labels
        self.label_encoder = LabelEncoder()
        y_train_encoded = self.label_encoder.fit_transform(y_train)
        y_test_encoded = self.label_encoder.transform(y_test)
        
        # Train Naive Bayes
        print("\nTraining Naive Bayes classifier...")
        self.tfidf_model = MultinomialNB(alpha=0.05, fit_prior=True)
        self.tfidf_model.fit(X_train_tfidf, y_train_encoded)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.tfidf_model, X_train_tfidf, y_train_encoded, 
            cv=5, scoring='accuracy'
        )
        print(f"Cross-val accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        # Evaluate
        y_pred = self.tfidf_model.predict(X_test_tfidf)
        accuracy = accuracy_score(y_test_encoded, y_pred)
        
        print(f"\n{'='*60}")
        print("TEST SET RESULTS")
        print("="*60)
        print(f"Accuracy: {accuracy:.4f}")
        print("\nClassification Report:")
        print(classification_report(
            y_test_encoded, y_pred, 
            target_names=self.label_encoder.classes_
        ))
        
        # Save models
        print("\nSaving models...")
        joblib.dump(self.tfidf_model, MODELS_DIR / "stress_tfidf_model.pkl")
        joblib.dump(self.vectorizer, MODELS_DIR / "stress_vectorizer.pkl")
        joblib.dump(self.label_encoder, MODELS_DIR / "stress_label_encoder.pkl")
        
        print("✓ TF-IDF model saved")
        
        return accuracy
    
    def train_bert_model(self, df):
        """Train BERT model for stress detection (optional)"""
        if not BERT_AVAILABLE:
            print("\n⚠ Skipping BERT training - transformers not installed")
            return None
        
        print("\n" + "="*60)
        print("TRAINING BERT MODEL")
        print("="*60)
        
        try:
            # Prepare data
            X = df['text'].tolist()
            y = df['stress_level_encoded'].tolist()
            
            # Split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Load pre-trained BERT
            model_name = "distilbert-base-uncased"
            print(f"\nLoading {model_name}...")
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=4  # Low, Moderate, High, Critical
            )
            
            # Tokenize
            print("Tokenizing texts...")
            train_encodings = tokenizer(X_train, truncation=True, padding=True, max_length=128)
            test_encodings = tokenizer(X_test, truncation=True, padding=True, max_length=128)
            
            # Create dataset
            class StressDataset(torch.utils.data.Dataset):
                def __init__(self, encodings, labels):
                    self.encodings = encodings
                    self.labels = labels
                
                def __getitem__(self, idx):
                    item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
                    item['labels'] = torch.tensor(self.labels[idx])
                    return item
                
                def __len__(self):
                    return len(self.labels)
            
            train_dataset = StressDataset(train_encodings, y_train)
            test_dataset = StressDataset(test_encodings, y_test)
            
            # Training arguments (lightweight)
            training_args = TrainingArguments(
                output_dir=str(MODELS_DIR / "bert_stress"),
                num_train_epochs=3,
                per_device_train_batch_size=8,
                per_device_eval_batch_size=8,
                warmup_steps=100,
                weight_decay=0.01,
                logging_dir=str(MODELS_DIR / "logs"),
                logging_steps=50,
                evaluation_strategy="epoch",
                save_strategy="epoch",
                load_best_model_at_end=True,
            )
            
            # Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=test_dataset,
            )
            
            # Train
            print("\nTraining BERT model (this may take a while)...")
            trainer.train()
            
            # Evaluate
            print("\nEvaluating BERT model...")
            eval_results = trainer.evaluate()
            print(f"Evaluation results: {eval_results}")
            
            # Save
            print("\nSaving BERT model...")
            model.save_pretrained(MODELS_DIR / "bert_stress_model")
            tokenizer.save_pretrained(MODELS_DIR / "bert_stress_model")
            
            print("✓ BERT model saved")
            
            return eval_results
            
        except Exception as e:
            print(f"✗ Error training BERT model: {e}")
            print("Continuing with TF-IDF model only...")
            return None


class StressPredictor:
    """Load and use trained stress detection models"""
    
    def __init__(self, use_bert=False):
        self.use_bert = use_bert and BERT_AVAILABLE
        self.tfidf_model = None
        self.vectorizer = None
        self.label_encoder = None
        self.bert_model = None
        self.bert_tokenizer = None
    
    def load_models(self):
        """Load trained models"""
        print("Loading stress detection models...")
        
        try:
            # Load TF-IDF model
            self.tfidf_model = joblib.load(MODELS_DIR / "stress_tfidf_model.pkl")
            self.vectorizer = joblib.load(MODELS_DIR / "stress_vectorizer.pkl")
            self.label_encoder = joblib.load(MODELS_DIR / "stress_label_encoder.pkl")
            print("✓ Loaded TF-IDF model")
        except Exception as e:
            print(f"✗ Error loading TF-IDF model: {e}")
        
        # Try to load BERT if requested
        if self.use_bert:
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                self.bert_tokenizer = AutoTokenizer.from_pretrained(MODELS_DIR / "bert_stress_model")
                self.bert_model = AutoModelForSequenceClassification.from_pretrained(MODELS_DIR / "bert_stress_model")
                print("✓ Loaded BERT model")
            except Exception as e:
                print(f"⚠ Could not load BERT model: {e}")
                print("Falling back to TF-IDF model")
                self.use_bert = False
    
    def predict(self, text):
        """Predict stress level from text"""
        if self.use_bert and self.bert_model:
            return self._predict_bert(text)
        else:
            return self._predict_tfidf(text)
    
    def _predict_tfidf(self, text):
        """Predict using TF-IDF model"""
        # Vectorize
        X_tfidf = self.vectorizer.transform([text])
        
        # Predict
        pred_encoded = self.tfidf_model.predict(X_tfidf)[0]
        pred_proba = self.tfidf_model.predict_proba(X_tfidf)[0]
        
        # Decode
        stress_level = self.label_encoder.inverse_transform([pred_encoded])[0]
        confidence = pred_proba.max()
        
        return {
            'stress_level': stress_level,
            'confidence': float(confidence),
            'probabilities': {
                level: float(prob) 
                for level, prob in zip(self.label_encoder.classes_, pred_proba)
            }
        }
    
    def _predict_bert(self, text):
        """Predict using BERT model"""
        # Tokenize
        inputs = self.bert_tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
            max_length=128
        )
        
        # Predict
        with torch.no_grad():
            outputs = self.bert_model(**inputs)
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=-1)[0]
        
        # Get prediction
        pred_idx = torch.argmax(probs).item()
        confidence = probs[pred_idx].item()
        
        stress_levels = ['Low', 'Moderate', 'High', 'Critical']
        stress_level = stress_levels[pred_idx]
        
        return {
            'stress_level': stress_level,
            'confidence': float(confidence),
            'probabilities': {
                level: float(prob) 
                for level, prob in zip(stress_levels, probs)
            }
        }


def main():
    """Main training pipeline"""
    print("\n" + "="*60)
    print("STRESS DETECTION MODEL TRAINING")
    print("="*60)
    
    # Train models
    trainer = StressDetectionTrainer()
    
    # Load data
    df = trainer.load_data()
    
    # Train TF-IDF model (always)
    tfidf_accuracy = trainer.train_tfidf_model(df)
    
    # Train BERT model (optional)
    if BERT_AVAILABLE:
        try:
            trainer.train_bert_model(df)
        except Exception as e:
            print(f"\n⚠ BERT training failed: {e}")
            print("Continuing with TF-IDF model only")
    
    # Test loading and prediction
    print("\n" + "="*60)
    print("TESTING MODEL INFERENCE")
    print("="*60)
    
    predictor = StressPredictor(use_bert=False)
    predictor.load_models()
    
    # Test predictions
    test_texts = [
        "I feel good and relaxed today.",
        "I'm worried about work deadlines.",
        "I feel very anxious and unable to sleep because of work pressure.",
        "I can't cope anymore, everything is falling apart."
    ]
    
    for text in test_texts:
        result = predictor.predict(text)
        print(f"\nText: {text}")
        print(f"Prediction: {result['stress_level']} (confidence: {result['confidence']:.3f})")
    
    print("\n✓ Training and testing complete!")


if __name__ == "__main__":
    main()
