"""
Stage 4 — Train Random Forest AQI Regressor.
"""

import argparse
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from app.config import settings

DATA_PATH = settings.DATA_DIR / "city_day_clean.csv"
MODEL_PATH = settings.RF_MODEL_PATH

FEATURE_COLS = ["pm25", "pm10", "no2", "co", "o3", "so2", "prev_aqi"]
TARGET_COL = "aqi"


def train(csv_path: str):

    print(f"Loading dataset: {csv_path}")

    df = pd.read_csv(csv_path)

    missing = [c for c in FEATURE_COLS + [TARGET_COL] if c not in df.columns]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])

    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training Random Forest...")

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"\nMAE: {mae:.2f}")
    print(f"R² : {r2:.4f}")

    settings.TRAINED_MODELS_DIR.mkdir(exist_ok=True)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print(f"\nModel saved to {MODEL_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(DATA_PATH))
    args = parser.parse_args()

    train(args.data)