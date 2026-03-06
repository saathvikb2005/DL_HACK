import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_disease_risk():
    """Test disease risk prediction endpoint"""
    print("\n" + "="*60)
    print("Testing Disease Risk Prediction API")
    print("="*60)
    
    # Sample patient data
    patient_data = {
        "age": 45,
        "bmi": 28.5,
        "systolic_bp": 140,
        "diastolic_bp": 90,
        "cholesterol": 220,
        "glucose": 110,
        "heart_rate": 75,
        "smoking": True,
        "alcohol": False,
        "physical_activity": 2,
        "physical_activity_hours": 3.5,
        "diet_quality_score": 6,
        "family_history": True,
        "stress_level": 7
    }
    
    try:
        response = requests.post(f"{BASE_URL}/disease-risk", json=patient_data)
        response.raise_for_status()
        
        result = response.json()
        print("\n✓ Request successful!")
        print("\nInput Data:")
        print(json.dumps(patient_data, indent=2))
        print("\nAPI Response:")
        print(json.dumps(result, indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")

def test_stress_detection():
    """Test stress detection endpoint"""
    print("\n" + "="*60)
    print("Testing Stress Detection API")
    print("="*60)
    
    # Sample text inputs
    test_texts = [
        "I have been feeling overwhelmed with work lately and can't seem to focus on anything. I'm constantly worried about deadlines.",
        "I feel great today! Everything is going smoothly and I'm really happy with my progress.",
        "Work is stressful but I'm managing. Taking breaks helps me stay balanced."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: {text[:60]}...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/stress-detection",
                json={"user_text": text}
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✓ Stress Level: {result['stress_level']}")
            print(f"  Stress Score: {result['stress_score']}")
            print(f"  Confidence: {result['confidence']:.2f}")
            print(f"  Emotions: {', '.join(result['detected_emotions'])}")
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error: {e}")

def main():
    print("\n🏥 AI Health Platform API Tests")
    print("="*60)
    print("Make sure the API server is running at http://localhost:8000")
    
    # Test both endpoints
    test_disease_risk()
    test_stress_detection()
    
    print("\n" + "="*60)
    print("✓ All tests completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
