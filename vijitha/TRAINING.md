# AI Health Platform - Complete ML Training Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Prepare Datasets
```bash
python prepare_data.py
```
This will:
- Download UCI Heart Disease and PIMA Diabetes datasets (if available)
- Create synthetic datasets for training
- Preprocess and engineer features
- Save processed data to `data/` folder

### Step 3: Train Models
```bash
# Train disease risk models (Logistic Regression, Random Forest, Gradient Boosting)
python train_disease_model.py

# Train stress detection models (TF-IDF + Naive Bayes, optional BERT)
python train_stress_model.py
```

### Step 4: Run API Server
```bash
python main.py
```

Visit: http://localhost:8000/api/docs

---

## 📊 Project Structure

```
vijitha/
├── main.py                      # FastAPI server (auto-loads trained models)
├── models.py                    # Pydantic schemas for API
├── inference.py                 # Model inference utilities
├── prepare_data.py             # Dataset preparation
├── train_disease_model.py      # Train disease risk models
├── train_stress_model.py       # Train stress detection models
├── requirements.txt            # Python dependencies
├── README.md                   # Quick start guide
├── TRAINING.md                 # This file - detailed training guide
│
├── data/
│   ├── raw/                    # Raw datasets
│   │   ├── heart_disease.csv
│   │   ├── diabetes.csv
│   │   ├── lifestyle_disease_synthetic.csv
│   │   └── mental_health_synthetic.csv
│   └── processed/              # Processed datasets
│       ├── lifestyle_disease_processed.csv
│       └── mental_health_processed.csv
│
└── models/                     # Trained models (created after training)
    ├── heart_disease_model.pkl
    ├── heart_disease_scaler.pkl
    ├── diabetes_model.pkl
    ├── diabetes_scaler.pkl
    ├── hypertension_model.pkl
    ├── hypertension_scaler.pkl
    ├── stress_tfidf_model.pkl
    ├── stress_vectorizer.pkl
    └── stress_label_encoder.pkl
```

---

## 🔬 Training Details

### 1️⃣ Lifestyle Disease Risk Predictor

**Features Used:**
- Age
- BMI
- Systolic & Diastolic Blood Pressure
- Smoking status
- Physical activity hours
- Diet quality score
- Engineered features: BP ratio, age-BMI interaction, risk score

**Models Trained:**
- **Logistic Regression**: Fast, interpretable baseline
- **Random Forest**: Ensemble method, handles non-linear relationships
- **Gradient Boosting**: Best performance, sequential ensemble

**Target Diseases:**
- Heart Disease
- Diabetes
- Hypertension

**Training Process:**
1. Data split: 80% train, 20% test (stratified)
2. Feature scaling using StandardScaler
3. 5-fold cross-validation
4. Model evaluation using AUC-ROC
5. Save best performing model for each disease

**Expected Performance:**
- AUC-ROC: 0.70-0.85 (synthetic data)
- Better with real datasets

---

### 2️⃣ Mental Health Stress Detection

**Input:** Text (10-2000 characters)

**Models Trained:**
- **TF-IDF + Naive Bayes** (Basic): Fast, lightweight
- **BERT** (Advanced): Optional, requires more resources

**Stress Levels:**
- Low (0-30)
- Moderate (30-50)
- High (50-75)
- Critical (75-100)

**Training Process:**
1. Text preprocessing and cleaning
2. TF-IDF vectorization (max 5000 features, bigrams)
3. Train Multinomial Naive Bayes classifier
4. 5-fold cross-validation
5. Save model, vectorizer, and label encoder

**Expected Performance:**
- Accuracy: 0.75-0.85 (TF-IDF model)
- Accuracy: 0.85-0.92 (BERT model)

---

## 📦 Dataset Sources

### Real Datasets (Download if available)

1. **UCI Heart Disease Dataset**
   - URL: https://archive.ics.uci.edu/ml/datasets/heart+disease
   - Features: 13 clinical features
   - Samples: 303

2. **PIMA Diabetes Dataset**
   - URL: https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database
   - Features: 8 medical features
   - Samples: 768

3. **Mental Health Datasets**
   - Kaggle: https://www.kaggle.com/datasets?search=mental+health
   - Reddit Mental Health Dataset
   - Sentiment140, ISEAR, GoEmotions

### Synthetic Datasets

The system generates high-quality synthetic datasets if real data is unavailable:

- **Lifestyle Disease**: 5,000 samples with correlated features
- **Mental Health**: 3,000 text samples across stress levels

---

## 🧪 Testing Models

### Test Disease Risk Model
```python
from inference import get_disease_predictor

predictor = get_disease_predictor()
predictor.load_models()

test_input = {
    'age': 45,
    'bmi': 28.5,
    'systolic_bp': 140,
    'diastolic_bp': 90,
    'smoking': True,
    'physical_activity_hours': 2.5,
    'diet_quality_score': 5
}

predictions = predictor.predict(test_input)
print(predictions)
# {'heart_disease': 31.5, 'diabetes': 24.2, 'hypertension': 45.8}
```

### Test Stress Detection Model
```python
from inference import get_stress_predictor

predictor = get_stress_predictor()
predictor.load_model()

text = "I feel very anxious and unable to sleep because of work pressure."
result = predictor.predict(text)
print(result)
# {'stress_level': 'High', 'stress_score': 70.0, 'confidence': 0.89}
```

---

## 🔧 Customization

### Add More Features

Edit [train_disease_model.py](train_disease_model.py):
```python
self.feature_columns = [
    'age', 'bmi', 'systolic_bp', 'diastolic_bp',
    'smoking', 'physical_activity_hours', 'diet_quality_score',
    'cholesterol',  # Add new feature
    'glucose',      # Add new feature
    # ... more features
]
```

### Use Real Datasets

1. Download datasets manually
2. Place CSV files in `data/raw/`
3. Update column names in [prepare_data.py](prepare_data.py)
4. Run preprocessing and training

### Tune Hyperparameters

Edit model configurations in [train_disease_model.py](train_disease_model.py):
```python
models_to_train = {
    'random_forest': RandomForestClassifier(
        n_estimators=200,      # Increase trees
        max_depth=15,          # Increase depth
        min_samples_split=5,   # Add constraint
        random_state=42
    ),
    # ... other models
}
```

---

## 📈 Model Performance Monitoring

### Evaluate Trained Models

Both training scripts include evaluation metrics:
- Accuracy
- Precision, Recall, F1-Score
- ROC-AUC Score
- Confusion Matrix
- Cross-validation scores

### Example Output
```
==================================================
TRAINING MODELS FOR HEART DISEASE
==================================================

RANDOM FOREST
----------------------------------------
Cross-val AUC: 0.8234 (+/- 0.0456)

==================================================
EVALUATION RESULTS FOR HEART DISEASE
==================================================

RANDOM FOREST
----------------------------------------
AUC-ROC: 0.8156

Classification Report:
              precision    recall  f1-score   support

           0       0.82      0.85      0.83       500
           1       0.84      0.81      0.82       500

    accuracy                           0.83      1000
```

---

## 🚨 Troubleshooting

### Models Not Loading

**Problem:** API shows "No trained models found"

**Solution:**
```bash
# Check if models directory exists
ls models/

# Re-train models
python train_disease_model.py
python train_stress_model.py
```

### Low Accuracy

**Problem:** Model accuracy < 70%

**Solutions:**
1. Use real datasets instead of synthetic
2. Increase training samples
3. Add more features
4. Tune hyperparameters
5. Try ensemble methods

### BERT Training Fails

**Problem:** Out of memory or transformers errors

**Solutions:**
1. Skip BERT (TF-IDF model works fine)
2. Reduce batch size in training arguments
3. Use smaller model (distilbert instead of bert-base)
4. Train on GPU if available

---

## 🔄 Continuous Improvement

### Retrain with New Data

```bash
# Add new data to data/raw/
# Re-run preprocessing
python prepare_data.py

# Retrain models
python train_disease_model.py
python train_stress_model.py

# Models are automatically loaded on next API restart
python main.py
```

### A/B Testing

Run multiple model versions:
```python
# Save models with version numbers
joblib.dump(model, f"models/heart_disease_v2_model.pkl")

# Load specific version in inference.py
```

---

## 📚 Additional Resources

- **Scikit-learn**: https://scikit-learn.org/stable/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Transformers**: https://huggingface.co/docs/transformers/
- **UCI ML Repository**: https://archive.ics.uci.edu/ml/

---

## ✅ Checklist

- [ ] Install dependencies
- [ ] Prepare datasets
- [ ] Train disease risk models
- [ ] Train stress detection models
- [ ] Test models via inference
- [ ] Start FastAPI server
- [ ] Test API endpoints
- [ ] Deploy to production

---

**Need Help?** Check the API documentation at http://localhost:8000/api/docs after starting the server.
