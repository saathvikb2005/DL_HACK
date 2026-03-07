"""
train_classifier.py
════════════════════
Train a Random Forest posture classifier from the CSV data collected by
posture_detection.py, then save the model so the main script can load it
automatically.

Usage
─────
    python train_classifier.py

Output
──────
    posture_model.pkl   ← loaded automatically by posture_detection.py

Requires
────────
    pip install pandas scikit-learn
"""

import os
import csv
import pickle
import numpy as np
from datetime import datetime

CSV_FILE    = "posture_scores.csv"
MODEL_FILE  = "posture_model.pkl"
FEATURES    = ["neck_angle", "shoulder_diff", "spine_angle"]
MIN_SAMPLES = 20          # minimum rows before training is meaningful

_HEADER = [
    "timestamp", "neck_angle", "shoulder_diff", "spine_angle",
    "neck_score", "shoulder_score", "spine_score", "total_score", "status",
]


def auto_label(total_score: float) -> int:
    """
    Derive a binary label from the rule-based total score.
      1  →  Good Posture  (total ≥ 70)
      0  →  Bad Posture
    You can relabel rows manually in the CSV for a more nuanced dataset.
    """
    return 1 if total_score >= 70 else 0


# ─── Synthetic data generator ─────────────────────────────────────────────────

def _neck_score(a):
    if a >= 160: return 100
    if a >= 140: return int(50 + (a - 140) * 2.5)
    return max(0, int(a / 140 * 50))

def _shoulder_score(d, frame_h=480):
    pct = d / frame_h * 100
    if pct < 2:  return 100
    if pct < 5:  return int(100 - (pct - 2) * 10)
    return max(0, int(70 - (pct - 5) * 5))

def _spine_score(a):
    if a >= 160: return 100
    if a >= 130: return int(50 + (a - 130) * (50 / 30))
    return max(0, int(a / 130 * 50))


def generate_synthetic_csv(n_good=150, n_bad=150):
    """
    Create posture_scores.csv with realistic synthetic samples so the
    classifier can be trained immediately — no webcam session required.

    Good posture  →  neck≈165–175°, shoulder_diff≈2–8 px, spine≈160–175°
    Bad  posture  →  neck≈120–145°, shoulder_diff≈10–30 px, spine≈110–145°
    """
    rng = np.random.default_rng(0)
    rows = []

    # Good posture samples
    for _ in range(n_good):
        na = float(rng.uniform(158, 178))
        sd = float(rng.uniform(2,   10))
        sp = float(rng.uniform(158, 178))
        ns, ss, sps = _neck_score(na), _shoulder_score(sd), _spine_score(sp)
        tot = (ns + ss + sps) // 3
        rows.append([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            round(na, 2), round(sd, 2), round(sp, 2),
            ns, ss, sps, tot, "Good Posture",
        ])

    # Bad posture samples
    for _ in range(n_bad):
        na = float(rng.uniform(110, 145))
        sd = float(rng.uniform(10,  35))
        sp = float(rng.uniform(100, 145))
        ns, ss, sps = _neck_score(na), _shoulder_score(sd), _spine_score(sp)
        tot = (ns + ss + sps) // 3
        rows.append([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            round(na, 2), round(sd, 2), round(sp, 2),
            ns, ss, sps, tot, "Bad Posture - Sit Straight!",
        ])

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(_HEADER)
        w.writerows(rows)

    print(f"[INFO] Generated {n_good + n_bad} synthetic samples → {CSV_FILE}")
    print("[INFO] Replace this file with real webcam data for better accuracy.")


# ─── Training ─────────────────────────────────────────────────────────────────

def train():
    # ── Dependency check ──────────────────────────────────────────────────────
    try:
        import pandas as pd
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report, accuracy_score
    except ImportError:
        print("[ERROR] Missing dependencies.  Run:  pip install pandas scikit-learn")
        return

    # ── Load or auto-generate data ────────────────────────────────────────────
    if not os.path.exists(CSV_FILE):
        print(f"[WARN] {CSV_FILE} not found.  Generating synthetic training data ...")
        generate_synthetic_csv()

    df = pd.read_csv(CSV_FILE, encoding="utf-8")
    print(f"[INFO] Loaded {len(df)} rows from {CSV_FILE}.")

    if len(df) < MIN_SAMPLES:
        print(f"[WARN] Only {len(df)} samples (need ≥ {MIN_SAMPLES}).")
        print("       Keep running posture_detection.py to collect more data, then retry.")
        return

    # ── Feature / label preparation ───────────────────────────────────────────
    df["label"] = df["total_score"].apply(auto_label)
    class_counts = df["label"].value_counts().to_dict()
    print(f"[INFO] Class distribution: Good={class_counts.get(1, 0)}  Bad={class_counts.get(0, 0)}")

    X = df[FEATURES].values
    y = df["label"].values

    # Stratify only when both classes are present
    stratify = y if len(np.unique(y)) > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=stratify
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # ── Evaluate ──────────────────────────────────────────────────────────────
    preds = clf.predict(X_test)
    acc   = accuracy_score(y_test, preds)
    print(f"\n[INFO] Test accuracy : {acc:.2%}\n")
    print(classification_report(y_test, preds, target_names=["Bad Posture", "Good Posture"]))

    # ── Feature importances ───────────────────────────────────────────────────
    print("[INFO] Feature importances:")
    for feat, imp in zip(FEATURES, clf.feature_importances_):
        bar = "█" * int(imp * 40)
        print(f"  {feat:<22} {bar}  {imp:.3f}")

    # ── Save model ────────────────────────────────────────────────────────────
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(clf, f)
    print(f"\n[INFO] Model saved → {MODEL_FILE}")
    print("[INFO] Restart posture_detection.py to activate ML classification mode.")


if __name__ == "__main__":
    train()
