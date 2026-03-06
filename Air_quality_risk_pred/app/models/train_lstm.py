"""
Stage 4 — Train LSTM AQI Time-Series model.
"""

import argparse
import pickle
import numpy as np
import pandas as pd

from app.config import settings

DATA_PATH = settings.DATA_DIR / "city_day_clean.csv"
MODEL_PATH = settings.LSTM_MODEL_PATH
SCALER_PATH = settings.TRAINED_MODELS_DIR / "lstm_scaler.pkl"

SEQUENCE_LENGTH = 7
FEATURE_COLS = ["pm25", "pm10", "no2", "co", "o3", "so2"]


def create_sequences(data, targets, seq_len):
    X, y = [], []

    for i in range(len(data) - seq_len):
        X.append(data[i : i + seq_len])
        y.append(targets[i + seq_len])

    return np.array(X), np.array(y)


def train(csv_path: str, epochs: int):

    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    from sklearn.preprocessing import MinMaxScaler

    print(f"Loading dataset: {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["date"])
    df = df.sort_values(["city", "date"]).reset_index(drop=True)

    scaler = MinMaxScaler()

    scaler.fit(df[FEATURE_COLS].values)

    all_X, all_y = [], []

    for city, group in df.groupby("city"):

        if len(group) < SEQUENCE_LENGTH + 1:
            continue

        features = scaler.transform(group[FEATURE_COLS].values)
        targets = group["aqi"].values

        X_city, y_city = create_sequences(features, targets, SEQUENCE_LENGTH)

        all_X.append(X_city)
        all_y.append(y_city)

    if not all_X:
        raise ValueError("No sequences created. Check dataset.")

    X = np.concatenate(all_X)
    y = np.concatenate(all_y)

    split = int(len(X) * 0.8)

    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(SEQUENCE_LENGTH, len(FEATURE_COLS))),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.2),
        Dense(16, activation="relu"),
        Dense(1)
    ])

    model.compile(optimizer="adam", loss="mse", metrics=["mae"])

    early_stop = EarlyStopping(patience=5, restore_best_weights=True)

    model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=epochs,
        batch_size=32,
        callbacks=[early_stop]
    )

    settings.TRAINED_MODELS_DIR.mkdir(exist_ok=True)

    model.save(str(MODEL_PATH))

    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    print(f"LSTM model saved to {MODEL_PATH}")
    print(f"Scaler saved to {SCALER_PATH}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(DATA_PATH))
    parser.add_argument("--epochs", type=int, default=50)

    args = parser.parse_args()

    train(args.data, args.epochs)