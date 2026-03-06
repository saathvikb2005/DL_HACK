"""
Stage 2 — Data Cleaning & Preprocessing
"""

from pathlib import Path
import pandas as pd
from app.config import settings

RAW_PATH = settings.DATA_DIR / "city_day.csv"
CLEAN_PATH = settings.DATA_DIR / "city_day_clean.csv"

RENAME_MAP = {
    "City": "city",
    "Date": "date",
    "PM2.5": "pm25",
    "PM10": "pm10",
    "NO2": "no2",
    "CO": "co",
    "O3": "o3",
    "SO2": "so2",
    "AQI": "aqi",
    "AQI_Bucket": "aqi_bucket",
}

FEATURE_COLS = ["pm25", "pm10", "no2", "co", "o3", "so2"]


def preprocess():
    print(f"Reading dataset: {RAW_PATH}")

    df = pd.read_csv(RAW_PATH)

    # Rename columns
    df = df.rename(columns=RENAME_MAP)

    keep = ["city", "date"] + FEATURE_COLS + ["aqi", "aqi_bucket"]
    df = df[[c for c in keep if c in df.columns]]

    # Parse dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    df = df.sort_values(["city", "date"]).reset_index(drop=True)

    print(f"Rows before cleaning: {len(df)}")

    # Remove rows without AQI
    df = df.dropna(subset=["aqi"])

    # Fill pollutants
    for col in FEATURE_COLS:
        df[col] = df.groupby("city")[col].transform(lambda s: s.ffill().bfill())

    for col in FEATURE_COLS:
        df[col] = df[col].fillna(df[col].median())

    # Previous AQI feature
    df["prev_aqi"] = df.groupby("city")["aqi"].shift(1)
    df["prev_aqi"] = df["prev_aqi"].fillna(df["aqi"])

    # Clip negatives
    for col in FEATURE_COLS + ["aqi", "prev_aqi"]:
        df[col] = df[col].clip(lower=0)

    settings.DATA_DIR.mkdir(exist_ok=True)

    df.to_csv(CLEAN_PATH, index=False)

    print(f"\nClean dataset saved to {CLEAN_PATH}")
    print(f"Final shape: {df.shape}")
    print(f"Cities: {df['city'].nunique()}")


if __name__ == "__main__":
    preprocess()