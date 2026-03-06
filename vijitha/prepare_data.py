"""
Dataset preparation and downloading utilities
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
import requests
from sklearn.model_selection import train_test_split

# Create data directories
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

for directory in [DATA_DIR, RAW_DIR, PROCESSED_DIR]:
    directory.mkdir(exist_ok=True)


# ==================== Disease Risk Datasets ====================

def download_heart_disease_data():
    """Download UCI Heart Disease Dataset"""
    print("Downloading UCI Heart Disease Dataset...")
    
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
    
    column_names = [
        'age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg',
        'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal', 'target'
    ]
    
    try:
        df = pd.read_csv(url, names=column_names, na_values='?')
        
        # Binary classification: 0 = no disease, 1+ = disease
        df['target'] = df['target'].apply(lambda x: 1 if x > 0 else 0)
        
        # Save raw data
        output_path = RAW_DIR / "heart_disease.csv"
        df.to_csv(output_path, index=False)
        print(f"✓ Heart disease data saved to {output_path}")
        print(f"  Shape: {df.shape}, Missing values: {df.isnull().sum().sum()}")
        
        return df
    except Exception as e:
        print(f"✗ Error downloading heart disease data: {e}")
        return None


def download_diabetes_data():
    """
    Download PIMA Diabetes Dataset
    Note: This requires manual download from Kaggle or using Kaggle API
    """
    print("Downloading PIMA Diabetes Dataset...")
    
    # Option 1: Direct URL (if available)
    url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
    
    column_names = [
        'pregnancies', 'glucose', 'blood_pressure', 'skin_thickness',
        'insulin', 'bmi', 'diabetes_pedigree', 'age', 'outcome'
    ]
    
    try:
        df = pd.read_csv(url, names=column_names)
        
        # Save raw data
        output_path = RAW_DIR / "diabetes.csv"
        df.to_csv(output_path, index=False)
        print(f"✓ Diabetes data saved to {output_path}")
        print(f"  Shape: {df.shape}, Positive cases: {df['outcome'].sum()}")
        
        return df
    except Exception as e:
        print(f"✗ Error downloading diabetes data: {e}")
        print("  Please download manually from: https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database")
        return None


def create_synthetic_lifestyle_data(n_samples=8000):
    """
    Create synthetic lifestyle disease dataset for training
    This combines features from multiple sources
    """
    print(f"Creating synthetic lifestyle dataset with {n_samples} samples...")
    
    np.random.seed(42)
    
    # Generate synthetic features with realistic correlations
    age = np.random.randint(18, 90, n_samples)
    
    # BMI correlated with age
    bmi_base = np.random.normal(27, 5, n_samples)
    bmi = (bmi_base + (age - 40) * 0.05).clip(15, 50)
    
    # Blood pressure correlated with age and BMI
    systolic_base = np.random.normal(120, 15, n_samples)
    systolic_bp = (systolic_base + (age - 30) * 0.3 + (bmi - 25) * 0.5).clip(90, 200)
    diastolic_bp = (systolic_bp * 0.65 + np.random.normal(0, 5, n_samples)).clip(60, 130)
    
    smoking = np.random.binomial(1, 0.25, n_samples)
    
    # Physical activity inversely correlated with age and BMI
    activity_base = np.random.exponential(4, n_samples)
    physical_activity_hours = (activity_base - (age - 30) * 0.02 - (bmi - 25) * 0.1).clip(0, 20)
    
    # Diet quality correlated with activity
    diet_quality_score = (5 + physical_activity_hours * 0.3 + np.random.normal(0, 1.5, n_samples)).clip(1, 10).astype(int)
    
    # Cholesterol correlated with BMI and age
    cholesterol = (180 + (bmi - 25) * 2 + (age - 40) * 0.5 + np.random.normal(0, 30, n_samples)).clip(120, 350)
    
    # Glucose correlated with BMI
    glucose = (90 + (bmi - 25) * 1.5 + np.random.normal(0, 20, n_samples)).clip(70, 300)
    
    # Family history (new feature)
    family_history = np.random.binomial(1, 0.3, n_samples)
    
    data = {
        'age': age,
        'bmi': bmi,
        'systolic_bp': systolic_bp,
        'diastolic_bp': diastolic_bp,
        'smoking': smoking,
        'physical_activity_hours': physical_activity_hours,
        'diet_quality_score': diet_quality_score,
        'cholesterol': cholesterol,
        'glucose': glucose,
        'family_history': family_history,
    }
    
    df = pd.DataFrame(data)
    
    # Generate targets based on risk factors with better thresholds
    heart_risk = (
        (df['age'] > 50).astype(int) * 18 +
        (df['age'] > 65).astype(int) * 12 +
        (df['bmi'] > 30).astype(int) * 16 +
        (df['systolic_bp'] > 140).astype(int) * 18 +
        (df['systolic_bp'] > 160).astype(int) * 10 +
        (df['smoking']).astype(int) * 22 +
        (df['physical_activity_hours'] < 2.5).astype(int) * 12 +
        (df['cholesterol'] > 240).astype(int) * 14 +
        (df['family_history']).astype(int) * 15 +
        np.random.normal(0, 8, n_samples)
    )
    df['heart_disease'] = (heart_risk > 42).astype(int)
    
    diabetes_risk = (
        (df['bmi'] > 30).astype(int) * 28 +
        (df['bmi'] > 35).astype(int) * 12 +
        (df['age'] > 45).astype(int) * 16 +
        (df['glucose'] > 126).astype(int) * 35 +
        (df['glucose'] > 140).astype(int) * 15 +
        (df['physical_activity_hours'] < 3).astype(int) * 12 +
        (df['diet_quality_score'] < 5).astype(int) * 14 +
        (df['family_history']).astype(int) * 18 +
        np.random.normal(0, 8, n_samples)
    )
    df['diabetes'] = (diabetes_risk > 48).astype(int)
    
    hypertension_risk = (
        (df['systolic_bp'] > 140).astype(int) * 32 +
        (df['systolic_bp'] > 160).astype(int) * 15 +
        (df['diastolic_bp'] > 90).astype(int) * 22 +
        (df['bmi'] > 30).astype(int) * 18 +
        (df['age'] > 40).astype(int) * 12 +
        (df['age'] > 60).astype(int) * 8 +
        (df['smoking']).astype(int) * 14 +
        (df['family_history']).astype(int) * 12 +
        np.random.normal(0, 8, n_samples)
    )
    df['hypertension'] = (hypertension_risk > 43).astype(int)
    
    # Save
    output_path = RAW_DIR / "lifestyle_disease_synthetic.csv"
    df.to_csv(output_path, index=False)
    print(f"✓ Synthetic lifestyle data saved to {output_path}")
    print(f"  Heart disease: {df['heart_disease'].sum()} cases")
    print(f"  Diabetes: {df['diabetes'].sum()} cases")
    print(f"  Hypertension: {df['hypertension'].sum()} cases")
    
    return df


# ==================== Mental Health Datasets ====================

def create_synthetic_mental_health_data(n_samples=5000):
    """
    Create synthetic mental health text dataset
    This generates sample texts with stress indicators
    """
    print(f"Creating synthetic mental health dataset with {n_samples} samples...")
    
    np.random.seed(42)
    
    # Stress level templates
    low_stress_phrases = [
        "I feel good and relaxed today.",
        "Everything is going well at work.",
        "I'm enjoying my daily routine.",
        "I feel calm and peaceful.",
        "Life has been pretty manageable lately.",
        "I'm sleeping well and feeling energized.",
        "Work is balanced and I have time for hobbies.",
    ]
    
    moderate_stress_phrases = [
        "I feel somewhat anxious about upcoming deadlines.",
        "Work has been a bit overwhelming lately.",
        "I'm having trouble sleeping occasionally.",
        "I feel worried about several things.",
        "Sometimes I feel stressed but it's manageable.",
        "I'm tired from work pressure.",
        "I feel a bit overwhelmed with responsibilities.",
    ]
    
    high_stress_phrases = [
        "I feel very anxious and unable to sleep because of work pressure.",
        "I'm constantly worried and can't focus on anything.",
        "The stress is overwhelming and affecting my health.",
        "I feel exhausted and depressed all the time.",
        "I can't cope with the pressure anymore.",
        "I'm having panic attacks and anxiety episodes.",
        "Everything feels hopeless and I'm struggling daily.",
        "My mind keeps racing and I feel trapped.",
    ]
    
    critical_stress_phrases = [
        "I can't sleep at all and feel like I'm falling apart.",
        "I have severe anxiety and depression that won't go away.",
        "I feel completely helpless and don't know what to do.",
        "The stress is unbearable and I need immediate help.",
        "I'm having constant panic attacks and can't function.",
        "Everything is falling apart and I can't handle it anymore.",
    ]
    
    data = []
    
    for i in range(n_samples):
        # Distribute stress levels (balanced)
        rand = np.random.random()
        if rand < 0.25:  # 25% low stress
            text = np.random.choice(low_stress_phrases)
            stress_level = "Low"
            stress_score = np.random.uniform(0, 30)
        elif rand < 0.50:  # 25% moderate stress
            text = np.random.choice(moderate_stress_phrases)
            stress_level = "Moderate"
            stress_score = np.random.uniform(30, 50)
        elif rand < 0.75:  # 25% high stress
            text = np.random.choice(high_stress_phrases)
            stress_level = "High"
            stress_score = np.random.uniform(50, 75)
        else:  # 25% critical stress
            text = np.random.choice(critical_stress_phrases)
            stress_level = "Critical"
            stress_score = np.random.uniform(75, 100)
        
        # Add variations
        text = text + " " + np.random.choice([
            "", "I don't know what to do.", "Need advice.",
            "How can I improve this?", "Seeking help."
        ])
        
        data.append({
            'text': text.strip(),
            'stress_level': stress_level,
            'stress_score': stress_score,
            'age': np.random.randint(18, 70),
            'gender': np.random.choice(['M', 'F', 'Other'])
        })
    
    df = pd.DataFrame(data)
    
    # Save
    output_path = RAW_DIR / "mental_health_synthetic.csv"
    df.to_csv(output_path, index=False)
    print(f"✓ Mental health data saved to {output_path}")
    print(f"  Stress distribution:")
    print(df['stress_level'].value_counts())
    
    return df


def combine_real_datasets(heart_df, diabetes_df):
    """
    Combine real UCI Heart Disease and PIMA Diabetes datasets
    into unified format for multi-disease prediction
    """
    print("\nCombining real medical datasets...")
    
    # Process Heart Disease Dataset
    # UCI Heart Disease: age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, target
    heart_processed = pd.DataFrame({
        'age': heart_df['age'],
        'bmi': np.random.normal(27, 5, len(heart_df)).clip(18, 45),  # BMI not in original, estimate
        'systolic_bp': heart_df['trestbps'],
        'diastolic_bp': heart_df['trestbps'] * 0.67,  # Estimate diastolic
        'smoking': ((heart_df.get('sex', 0) == 1) & (np.random.random(len(heart_df)) < 0.3)).astype(int),
        'physical_activity_hours': np.random.exponential(3, len(heart_df)).clip(0, 15),
        'diet_quality_score': np.random.randint(3, 9, len(heart_df)),
        'cholesterol': heart_df['chol'],
        'glucose': heart_df.get('fbs', 100) * 20 + 80,  # Estimate from fasting blood sugar
        'family_history': np.random.binomial(1, 0.3, len(heart_df)),
        'heart_disease': heart_df['target']
    })
    
    # Process PIMA Diabetes Dataset  
    # PIMA: pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree, age, outcome
    diabetes_processed = pd.DataFrame({
        'age': diabetes_df['age'],
        'bmi': diabetes_df['bmi'],
        'systolic_bp': diabetes_df['blood_pressure'] * 1.5,  # Estimate systolic
        'diastolic_bp': diabetes_df['blood_pressure'],
        'smoking': np.random.binomial(1, 0.25, len(diabetes_df)),
        'physical_activity_hours': np.where(diabetes_df['bmi'] > 30, 
                                           np.random.exponential(2, len(diabetes_df)),
                                           np.random.exponential(4, len(diabetes_df))).clip(0, 15),
        'diet_quality_score': (10 - (diabetes_df['bmi'] - 20) * 0.2).clip(1, 10).astype(int),
        'cholesterol': 180 + diabetes_df['bmi'] * 2 + np.random.normal(0, 20, len(diabetes_df)),
        'glucose': diabetes_df['glucose'],
        'family_history': (diabetes_df['diabetes_pedigree'] > 0.5).astype(int),
        'diabetes': diabetes_df['outcome']
    })
    
    # Assign heart disease to diabetes dataset based on risk factors
    diabetes_processed['heart_disease'] = (
        ((diabetes_processed['age'] > 50) & (diabetes_processed['bmi'] > 30)) |
        ((diabetes_processed['systolic_bp'] > 140) & (diabetes_processed['cholesterol'] > 240))
    ).astype(int)
    
    # Assign diabetes to heart disease dataset based on risk factors  
    heart_processed['diabetes'] = (
        ((heart_processed['bmi'] > 30) & (heart_processed['glucose'] > 126)) |
        (heart_processed['family_history'] == 1)
    ).astype(int)
    
    # Combine datasets
    combined = pd.concat([heart_processed, diabetes_processed], ignore_index=True)
    
    # Add hypertension based on blood pressure
    combined['hypertension'] = (
        (combined['systolic_bp'] > 140) | (combined['diastolic_bp'] > 90)
    ).astype(int)
    
    # Feature engineering
    combined['bp_ratio'] = combined['systolic_bp'] / combined['diastolic_bp'].replace(0, np.nan)
    combined['age_bmi_interaction'] = combined['age'] * combined['bmi']
    combined['age_squared'] = combined['age'] ** 2
    combined['bmi_cholesterol_interaction'] = combined['bmi'] * combined['cholesterol'] / 100
    combined['risk_score'] = (
        (combined['age'] > 50).astype(int) * 0.2 +
        (combined['bmi'] > 30).astype(int) * 0.3 +
        (combined['smoking']).astype(int) * 0.3 +
        (combined['physical_activity_hours'] < 3).astype(int) * 0.2
    )
    
    # Handle any missing values - use median for numeric, mode for categorical
    for col in combined.columns:
        if combined[col].dtype in ['float64', 'int64']:
            combined[col] = combined[col].fillna(combined[col].median())
        else:
            combined[col] = combined[col].fillna(combined[col].mode()[0] if len(combined[col].mode()) > 0 else 0)
    
    # Drop any remaining rows with NaN (should be none but just to be safe)
    initial_len = len(combined)
    combined = combined.dropna()
    if len(combined) < initial_len:
        print(f"  Dropped {initial_len - len(combined)} rows with missing values")
    
    # Ensure all values are numeric
    combined = combined.apply(pd.to_numeric, errors='coerce')
    combined = combined.fillna(combined.median())
    
    print(f"✓ Combined dataset: {len(combined)} samples")
    print(f"  - From UCI Heart Disease: {len(heart_processed)} samples")
    print(f"  - From PIMA Diabetes: {len(diabetes_processed)} samples")
    print(f"\nDisease distribution:")
    print(f"  Heart Disease: {combined['heart_disease'].sum()} ({combined['heart_disease'].mean()*100:.1f}%)")
    print(f"  Diabetes: {combined['diabetes'].sum()} ({combined['diabetes'].mean()*100:.1f}%)")
    print(f"  Hypertension: {combined['hypertension'].sum()} ({combined['hypertension'].mean()*100:.1f}%)")
    
    return combined


# ==================== Data Preprocessing ====================

def preprocess_lifestyle_data():
    """Preprocess lifestyle disease data for training"""
    print("\nPreprocessing lifestyle disease data...")
    
    # Try to load REAL datasets first
    heart_df = None
    diabetes_df = None
    
    try:
        heart_df = pd.read_csv(RAW_DIR / "heart_disease.csv")
        print(f"✓ Loaded real heart disease data: {len(heart_df)} samples")
    except:
        print("⚠ Real heart disease data not found")
    
    try:
        diabetes_df = pd.read_csv(RAW_DIR / "diabetes.csv")
        print(f"✓ Loaded real diabetes data: {len(diabetes_df)} samples")
    except:
        print("⚠ Real diabetes data not found")
    
    # Combine real datasets or use synthetic
    if heart_df is not None and diabetes_df is not None:
        print("\n🎯 Using REAL medical datasets for training!")
        df = combine_real_datasets(heart_df, diabetes_df)
    else:
        print("\n⚠ Using synthetic dataset (real data not available)")
        try:
            df = pd.read_csv(RAW_DIR / "lifestyle_disease_synthetic.csv")
        except:
            print("Creating synthetic dataset...")
            df = create_synthetic_lifestyle_data()
    
    # Handle missing values
    df = df.fillna(df.median())
    
    # Feature engineering
    df['bp_ratio'] = df['systolic_bp'] / df['diastolic_bp']
    df['age_bmi_interaction'] = df['age'] * df['bmi']
    df['age_squared'] = df['age'] ** 2
    df['bmi_cholesterol_interaction'] = df['bmi'] * df['cholesterol'] / 100
    df['risk_score'] = (
        (df['age'] > 50).astype(int) * 0.2 +
        (df['bmi'] > 30).astype(int) * 0.3 +
        (df['smoking']).astype(int) * 0.3 +
        (df['physical_activity_hours'] < 3).astype(int) * 0.2
    )
    
    # Save processed data
    output_path = PROCESSED_DIR / "lifestyle_disease_processed.csv"
    df.to_csv(output_path, index=False)
    print(f"✓ Processed data saved to {output_path}")
    
    return df


def preprocess_mental_health_data():
    """Preprocess mental health text data"""
    print("\nPreprocessing mental health data...")
    
    # Try to use real data if available
    try:
        # Check if we have any real mental health datasets
        real_files = list(RAW_DIR.glob("mental_health_real*.csv"))
        if real_files:
            print(f"✓ Found {len(real_files)} real mental health dataset(s)")
            df = pd.read_csv(real_files[0])
            print("🎯 Using REAL mental health data for training!")
        else:
            df = pd.read_csv(RAW_DIR / "mental_health_synthetic.csv")
            print("⚠ Using synthetic mental health data")
    except:
        print("Creating synthetic dataset...")
        df = create_synthetic_mental_health_data()
    
    # Text preprocessing
    df['text'] = df['text'].str.lower().str.strip()
    df['text_length'] = df['text'].str.len()
    df['word_count'] = df['text'].str.split().str.len()
    
    # Encode stress levels
    stress_mapping = {'Low': 0, 'Moderate': 1, 'High': 2, 'Critical': 3}
    df['stress_level_encoded'] = df['stress_level'].map(stress_mapping)
    
    # Save processed data
    output_path = PROCESSED_DIR / "mental_health_processed.csv"
    df.to_csv(output_path, index=False)
    print(f"✓ Processed data saved to {output_path}")
    
    return df


# ==================== Main ====================

def prepare_all_datasets():
    """Download and prepare all datasets"""
    print("=" * 60)
    print("DATASET PREPARATION")
    print("=" * 60)
    
    # Download real datasets (if available)
    print("\n1. Downloading real datasets...")
    download_heart_disease_data()
    download_diabetes_data()
    
    # Create synthetic datasets
    print("\n2. Creating synthetic datasets...")
    create_synthetic_lifestyle_data()
    create_synthetic_mental_health_data()
    
    # Preprocess all data
    print("\n3. Preprocessing datasets...")
    preprocess_lifestyle_data()
    preprocess_mental_health_data()
    
    print("\n" + "=" * 60)
    print("✓ Dataset preparation complete!")
    print("=" * 60)
    print(f"\nData saved in:")
    print(f"  - Raw data: {RAW_DIR}")
    print(f"  - Processed data: {PROCESSED_DIR}")


if __name__ == "__main__":
    prepare_all_datasets()
