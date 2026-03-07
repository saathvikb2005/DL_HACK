"""
posture_detection.py
════════════════════
Real-time posture detection using MediaPipe Pose.

Features
────────
  • 33-landmark skeleton overlay
  • 3 posture metrics  →  Neck angle / Shoulder alignment / Spine angle
  • Rule-based OR ML posture score  (0–100 %)
  • Beep alert when bad posture is detected
  • Live score-history graph drawn directly in the frame (no matplotlib)
  • Automatic CSV logging  →  posture_scores.csv

Usage
─────
    python posture_detection.py

Press ESC to quit.
"""

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    RunningMode,
)
import numpy as np
import argparse
import csv
import os
import sys
import time
import threading
import urllib.request
from collections import deque
from datetime import datetime

# Suppress verbose TFLite / feedback-manager stderr logs
os.environ.setdefault("GLOG_minloglevel", "3")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

# Global stop signal — set this from outside to stop a headless session
_stop_event = threading.Event()

# ─── Model setup (auto-downloaded on first run) ───────────────────────────────

MODEL_FILE = "pose_landmarker_lite.task"
MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)

# BlazePose 33-landmark connections (same topology as old mp.POSE_CONNECTIONS)
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
    (11, 12),
    (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
    (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),
]

# Landmark indices used for posture metrics
IDX_LEFT_EAR       = 7
IDX_RIGHT_EAR      = 8
IDX_LEFT_SHOULDER  = 11
IDX_RIGHT_SHOULDER = 12
IDX_LEFT_HIP       = 23
IDX_RIGHT_HIP      = 24
IDX_LEFT_KNEE      = 25


def ensure_model():
    """Download the pose landmarker model on first run (~5 MB)."""
    if not os.path.exists(MODEL_FILE):
        print(f"[INFO] Downloading {MODEL_FILE} (~5 MB) ...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_FILE)
        print("[INFO] Model downloaded.")


def draw_pose(frame, landmarks, h, w):
    """Draw skeleton connections and landmark dots using plain OpenCV."""
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    for a, b in POSE_CONNECTIONS:
        if a < len(pts) and b < len(pts):
            cv2.line(frame, pts[a], pts[b], (245, 66, 230), 2, cv2.LINE_AA)
    for (x, y) in pts:
        cv2.circle(frame, (x, y), 4, (245, 117, 66), -1)

# ─── Notification / Alert ────────────────────────────────────────────────────

def _alert_worker(score: int, issues: list):
    """
    Show a Windows toast notification AND play a beep.
    Runs on a daemon thread so it never blocks the webcam loop.
    """
    # -- Beep ----------------------------------------------------------------
    try:
        import winsound
        winsound.Beep(1000, 400)
    except Exception:
        pass

    # -- Build issue-specific message ----------------------------------------
    issue_str = " + ".join(issues) if issues else "Poor Posture"
    if score < 30:
        title   = "Posture Alert - Critical!"
        message = f"Score: {score}%  |  {issue_str}. Sit upright NOW!"
    elif score < 50:
        title   = "Posture Alert - Bad Posture"
        message = f"Score: {score}%  |  {issue_str}. Please correct your posture."
    else:
        title   = "Posture Reminder"
        message = f"Score: {score}%  |  {issue_str}. Try to sit up straighter."

    print(f"[ALERT] {title} - {message}")

    # -- Windows Toast (winotify) -------------------------------------------
    notified = False
    try:
        from winotify import Notification, audio
        toast = Notification(
            app_id="Posture Detection",
            title=title,
            msg=message,
            duration="short",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
        notified = True
    except Exception as e:
        print(f"[ALERT] Toast failed ({e}), trying tkinter popup...")

    if notified:
        return

    # -- Fallback: tkinter popup (non-blocking) ------------------------------
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showwarning(title, message)
        root.destroy()
    except Exception as e:
        print(f"[ALERT] tkinter also failed ({e}). Check notifications manually.")


def trigger_alert(score: int, issues: list):
    """Fire notification + beep on a daemon thread (non-blocking)."""
    threading.Thread(target=_alert_worker, args=(score, issues), daemon=True).start()


def check_winotify():
    """Warn at startup if winotify is not available."""
    try:
        import winotify  # noqa: F401
        print("[INFO] Notifications: Windows toast (winotify) enabled.")
    except ImportError:
        print("[WARN] winotify not found - falling back to tkinter popups.")
        print("       Install it with: pip install winotify")

# ─── Geometry ─────────────────────────────────────────────────────────────────

def calculate_angle(a, b, c):
    """
    Return the angle (degrees) at vertex *b* formed by the three 2-D points
    a → b → c.  Result is always in [0, 180].
    """
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)
    radians = (
        np.arctan2(c[1] - b[1], c[0] - b[0]) -
        np.arctan2(a[1] - b[1], a[0] - b[0])
    )
    angle = np.abs(np.degrees(radians))
    return 360.0 - angle if angle > 180 else angle

# ─── Posture Scoring (0 – 100 per metric) ─────────────────────────────────────

def score_neck(angle: float) -> int:
    """
    Neck angle  =  ear → shoulder → hip.
    Ideal posture ≥ 150°  (relaxed but upright head).
    Forward-head posture pushes the angle below 130°.
    """
    if angle >= 150:
        return 100
    if angle >= 125:
        return int(60 + (angle - 125) * 1.6)
    return max(0, int(angle / 125 * 60))


def score_shoulder(diff_px: float, frame_h: int) -> int:
    """
    Shoulder-level symmetry.
    diff_px  =  |left_shoulder.y – right_shoulder.y|  in pixels.
    Expressed as % of frame height; ideal < 2 %.
    """
    pct = diff_px / frame_h * 100
    if pct < 2:
        return 100
    if pct < 5:
        return int(100 - (pct - 2) * 10)
    return max(0, int(70 - (pct - 5) * 5))


def score_spine(angle: float) -> int:
    """
    Spine angle  =  shoulder → hip → knee.
    Ideal posture ≥ 150°  (comfortably upright torso).
    Slouching pushes the angle below 120°.
    """
    if angle >= 150:
        return 100
    if angle >= 120:
        return int(60 + (angle - 120) * 1.33)
    return max(0, int(angle / 120 * 60))


def score_rounded_shoulders(sh_z_diff: float) -> int:
    """
    sh_z_diff = avg_shoulder_z - avg_hip_z  (MediaPipe normalized depth).
    Shoulders forward of hips produce a negative value.
    Z-depth from a webcam is noisy, so thresholds are relaxed.
    Good:     sh_z_diff >= -0.10  → 100
    Moderate: -0.25 to -0.10      → 100 → 50
    Bad:      <= -0.25            → 50  → 0
    """
    if sh_z_diff >= -0.10:
        return 100
    if sh_z_diff >= -0.25:
        return max(50, int(100 + (sh_z_diff + 0.10) * 333))
    return max(0, int(50 + (sh_z_diff + 0.25) * 333))


def detect_issues(n_s: int, s_s: int, sp_s: int, r_s: int) -> list:
    """Return list of specific bad-posture labels from individual scores."""
    issues = []
    if n_s  < 70: issues.append("Forward Head")
    if s_s  < 70: issues.append("Uneven Shoulders")
    if sp_s < 70: issues.append("Slouching")
    if r_s  < 70: issues.append("Rounded Shoulders")
    return issues


def posture_status(total: int, issues: list):
    """Return (status_string, BGR_colour) for the given score + issue list."""
    if total >= 70:
        return "Good Posture", (0, 210, 0)
    issue_str = " | ".join(issues) if issues else "Bad Posture"
    if total >= 50:
        return f"Moderate: {issue_str}", (0, 160, 255)
    return f"Bad: {issue_str}", (0, 0, 220)

# ─── CSV Logging ──────────────────────────────────────────────────────────────

CSV_FILE = "posture_scores.csv"
_HEADER  = [
    "timestamp", "neck_angle", "shoulder_diff", "spine_angle", "shoulder_z_diff",
    "neck_score", "shoulder_score", "spine_score", "rounded_score", "total_score", "status",
]

def init_csv():
    """Create or migrate CSV. Backs up old file if column schema changed."""
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            existing_header = f.readline().strip()
        if existing_header != ",".join(_HEADER):
            backup = CSV_FILE.replace(".csv", "_backup.csv")
            os.rename(CSV_FILE, backup)
            print(f"[INFO] CSV schema updated – old data moved to {backup}")
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(_HEADER)


def log_row(neck_a, sh_d, sp_a, sh_z, n_s, s_s, sp_s, r_s, total, status):
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            round(neck_a, 2), round(sh_d, 2), round(sp_a, 2), round(sh_z, 4),
            n_s, s_s, sp_s, r_s, total, status,
        ])

# ─── In-Frame Score-History Graph (pure OpenCV, no matplotlib) ────────────────

def draw_graph(frame, scores: list):
    """
    Draw a colour-coded line graph of the last N score readings
    in the top-right corner of *frame* using only OpenCV primitives.
    Green ≥ 70 | Orange 50-69 | Red < 50
    """
    if len(scores) < 2:
        return

    GW, GH = 280, 90
    h, w   = frame.shape[:2]
    x0, y0 = w - GW - 10, 10
    pad_b, pad_t = 5, 18
    plot_h = GH - pad_b - pad_t

    # Background + border
    cv2.rectangle(frame, (x0, y0), (x0 + GW, y0 + GH), (15, 15, 35), -1)
    cv2.rectangle(frame, (x0, y0), (x0 + GW, y0 + GH), (70, 70, 70),  1)

    cv2.putText(frame, "Score History",
                (x0 + 5, y0 + 12), cv2.FONT_HERSHEY_SIMPLEX,
                0.38, (180, 180, 180), 1, cv2.LINE_AA)

    # Horizontal guide lines at 25 / 50 / 75 %
    for g in (25, 50, 75):
        gy = y0 + GH - pad_b - int(g / 100 * plot_h)
        cv2.line(frame, (x0, gy), (x0 + GW, gy), (35, 35, 55), 1)
        cv2.putText(frame, str(g), (x0 + 2, gy - 1),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.28, (60, 60, 80), 1)

    recent = scores[-GW:]          # at most one point per pixel column
    n      = len(recent)

    pts = []
    for i, sc in enumerate(recent):
        px = x0 + int(i / max(n - 1, 1) * (GW - 4)) + 2
        py = y0 + GH - pad_b - int(sc / 100 * plot_h)
        py = max(y0 + pad_t, min(y0 + GH - pad_b, py))
        pts.append((px, py))

    for i in range(1, len(pts)):
        c = (0, 210, 0) if recent[i] >= 70 else (0, 160, 255) if recent[i] >= 50 else (0, 0, 220)
        cv2.line(frame, pts[i - 1], pts[i], c, 2, cv2.LINE_AA)

    # Annotate the most recent value
    if pts:
        cv2.putText(frame, f"{recent[-1]}%",
                    (pts[-1][0] - 16, pts[-1][1] - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)

# ─── HUD Overlay ──────────────────────────────────────────────────────────────

def draw_hud(frame, neck_a, sh_d, sp_a, sh_z, n_s, s_s, sp_s, r_s, total, status, color):
    h, w = frame.shape[:2]

    # Semi-transparent dark panel — expanded to fit 5 metrics
    overlay = frame.copy()
    cv2.rectangle(overlay, (5, 5), (370, 255), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

    def txt(text, pos, col=(220, 220, 220), scale=0.52, thick=1):
        cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                    scale, col, thick, cv2.LINE_AA)

    txt(f"Posture Score : {total}%",                              (15, 30),  (0, 215, 255), 0.72, 2)
    txt(f"Status : {status}",                                     (15, 57),  color,         0.50, 2)
    txt(f"Neck   Angle  : {neck_a:6.1f} deg  -> {n_s:3d}pts",    (15, 83))
    txt(f"Shoulder Diff : {sh_d:6.1f} px   -> {s_s:3d}pts",      (15, 105))
    txt(f"Spine  Angle  : {sp_a:6.1f} deg  -> {sp_s:3d}pts",     (15, 127))
    r_col = (0, 210, 0) if r_s >= 70 else (0, 160, 255) if r_s >= 50 else (0, 0, 220)
    txt(f"Round Shldrs  : {sh_z:+.3f} z    -> {r_s:3d}pts",      (15, 149), r_col)
    txt("Ideal: neck>160  sh<2%  spine>160  z>-0.05",             (15, 173), (100, 100, 100), 0.35)

    # Colour-coded progress bar along the bottom
    bx, by = 15, h - 35
    cv2.rectangle(frame, (bx, by), (bx + 300, by + 16), (40, 40, 40), -1)
    cv2.rectangle(frame, (bx, by), (bx + int(total * 3), by + 16), color, -1)
    txt(f"{total}%", (bx + 308, by + 13), (200, 200, 200), 0.46)

# ─── Optional ML Classifier ───────────────────────────────────────────────────

def load_clf():
    """Load posture_model.pkl if it exists (produced by train_classifier.py)."""
    path = "posture_model.pkl"
    if os.path.exists(path):
        import pickle
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


def ml_classify(clf, neck_a, sh_d, sp_a):
    """Return (status_string, BGR_colour) using the trained Random Forest."""
    pred = clf.predict([[neck_a, sh_d, sp_a]])[0]
    return (
        ("Good Posture (ML)",     (0, 210,   0)) if pred == 1
        else ("Bad Posture (ML)", (0,   0, 220))
    )

# ─── Main ─────────────────────────────────────────────────────────────────────

def main(headless: bool = False):
    # Allow --headless flag when run directly from CLI
    if not headless and len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Posture Detection")
        parser.add_argument("--headless", action="store_true",
                            help="Run without display window (background mode)")
        args = parser.parse_args()
        headless = args.headless

    _stop_event.clear()
    init_csv()
    ensure_model()
    check_winotify()
    clf = load_clf()
    if clf:
        print("[INFO] ML classifier loaded - using Random Forest predictions.")
    else:
        print("[INFO] No ML model found - using rule-based scoring.")
        print("       Run train_classifier.py to enable ML mode.")

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_FILE),
        running_mode=RunningMode.VIDEO,   # VIDEO mode provides image dims -> fixes NORM_RECT warning
        num_poses=1,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open webcam (device 0).")
        return

    score_history : list = []
    smooth_buf           = deque(maxlen=15)   # ~0.5 s rolling window
    last_log             = 0.0
    last_alert           = 0.0
    session_start        = time.time()
    good_seconds         = 0.0
    bad_seconds          = 0.0
    last_frame_t         = time.time()
    LOG_EVERY            = 3    # seconds between CSV writes
    ALERT_EVERY          = 15   # seconds between popup notifications
    # Cached per-frame values used on low-visibility frames (stale-but-safe)
    neck_a = sh_d = sp_a = sh_z_diff = 0.0
    n_s = s_s = sp_s = r_s = 100   # start optimistic so no false warnings
    total = smoothed = 0
    issues: list  = []
    status, color = "Good Posture", (0, 210, 0)

    print("[INFO] Posture Detection running.  Press ESC to quit.")

    with PoseLandmarker.create_from_options(options) as landmarker:
        frame_ts_ms = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Failed to grab frame.")
                break

            frame = cv2.flip(frame, 1)          # mirror - feels more natural
            h, w  = frame.shape[:2]

            rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result   = landmarker.detect_for_video(mp_image, frame_ts_ms)
            frame_ts_ms += 33   # ~30 fps timestamp increment in ms

            if result.pose_landmarks:
                lm = result.pose_landmarks[0]   # first detected person

                # -- Draw skeleton -----------------------------------------
                draw_pose(frame, lm, h, w)

                def pt(idx, _lm=lm, _w=w, _h=h):
                    """Return [x_px, y_px] for landmark index idx."""
                    return [_lm[idx].x * _w, _lm[idx].y * _h]

                l_ear = pt(IDX_LEFT_EAR)
                l_sh  = pt(IDX_LEFT_SHOULDER)
                r_sh  = pt(IDX_RIGHT_SHOULDER)
                l_hip = pt(IDX_LEFT_HIP)
                l_kn  = pt(IDX_LEFT_KNEE)

                now          = time.time()
                frame_dt     = now - last_frame_t
                last_frame_t = now

                # -- Compute metrics ----------------------------------------
                neck_a    = calculate_angle(l_ear, l_sh, l_hip)
                sh_d      = abs(l_sh[1] - r_sh[1])
                sp_a      = calculate_angle(l_sh, l_hip, l_kn)
                sh_z_diff = ((lm[IDX_LEFT_SHOULDER].z + lm[IDX_RIGHT_SHOULDER].z) / 2
                             - (lm[IDX_LEFT_HIP].z    + lm[IDX_RIGHT_HIP].z)    / 2)

                # -- Scores --------------------------------------------------
                n_s   = score_neck(neck_a)
                s_s   = score_shoulder(sh_d, h)
                sp_s  = score_spine(sp_a)
                r_s   = score_rounded_shoulders(sh_z_diff)
                total = (n_s + s_s + sp_s + r_s) // 4

                # -- Temporal smoothing: 15-frame rolling average (~0.5 s) --
                smooth_buf.append(total)
                smoothed = int(sum(smooth_buf) / len(smooth_buf))

                issues = detect_issues(n_s, s_s, sp_s, r_s)

                # -- Status derived from smoothed score --------------------
                if clf:
                    status, color = ml_classify(clf, neck_a, sh_d, sp_a)
                else:
                    status, color = posture_status(smoothed, issues)

                # -- Session time tracking ---------------------------------
                if smoothed >= 70:
                    good_seconds += frame_dt
                else:
                    bad_seconds  += frame_dt

                # -- Per-body visual warnings on the skeleton ----------------
                if r_s < 70:
                    lsh_px = (int(lm[IDX_LEFT_SHOULDER].x  * w), int(lm[IDX_LEFT_SHOULDER].y  * h))
                    rsh_px = (int(lm[IDX_RIGHT_SHOULDER].x * w), int(lm[IDX_RIGHT_SHOULDER].y * h))
                    cv2.circle(frame, lsh_px, 12, (0, 0, 220), 3)
                    cv2.circle(frame, rsh_px, 12, (0, 0, 220), 3)
                    mid_x = (lsh_px[0] + rsh_px[0]) // 2
                    mid_y = min(lsh_px[1], rsh_px[1]) - 14
                    cv2.putText(frame, "ROUNDED SHOULDERS", (mid_x - 95, mid_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 60, 255), 2, cv2.LINE_AA)
                if sp_s < 70:
                    hip_px = (int(lm[IDX_LEFT_HIP].x * w), int(lm[IDX_LEFT_HIP].y * h))
                    cv2.putText(frame, "SLOUCHING", (hip_px[0] + 10, hip_px[1] - 12),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 100, 255), 2, cv2.LINE_AA)
                if n_s < 70:
                    ear_px = (int(lm[IDX_LEFT_EAR].x * w), int(lm[IDX_LEFT_EAR].y * h))
                    cv2.putText(frame, "FORWARD HEAD", (ear_px[0] + 10, ear_px[1]),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 150, 255), 2, cv2.LINE_AA)

                # -- Notification alert: smoothed score guards false triggers --
                if (len(smooth_buf) >= 10
                        and smoothed < 70
                        and (now - last_alert) >= ALERT_EVERY):
                    trigger_alert(smoothed, issues)
                    last_alert = now

                # -- CSV logging ---------------------------------------------
                if (now - last_log) >= LOG_EVERY:
                    log_row(neck_a, sh_d, sp_a, sh_z_diff, n_s, s_s, sp_s, r_s, total, status)
                    score_history.append(smoothed)
                    last_log = now

                # -- HUD + graph ---------------------------------------------
                if not headless:
                    draw_hud(frame, neck_a, sh_d, sp_a, sh_z_diff, n_s, s_s, sp_s, r_s, smoothed, status, color)
                    draw_graph(frame, score_history)

            else:
                if not headless:
                    cv2.putText(
                        frame, "No Pose Detected - Adjust Camera",
                        (w // 8, h // 2), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (80, 80, 255), 2, cv2.LINE_AA,
                    )

            if headless:
                if _stop_event.is_set():
                    break
                time.sleep(0.001)
            else:
                cv2.imshow("Posture Detection", frame)
                if cv2.waitKey(1) & 0xFF == 27:     # ESC
                    break

    cap.release()
    if not headless:
        cv2.destroyAllWindows()
    # ── Session summary ───────────────────────────────────────────────────────
    total_t   = time.time() - session_start
    avg_score = int(sum(score_history) / max(len(score_history), 1))
    pct_good  = good_seconds / max(total_t, 1) * 100
    pct_bad   = bad_seconds  / max(total_t, 1) * 100
    print()
    print("══════════════════════════════════════════")
    print("  SESSION SUMMARY")
    print("══════════════════════════════════════════")
    print(f"  Duration      : {int(total_t // 60):02d}m {int(total_t % 60):02d}s")
    print(f"  Average score : {avg_score}%")
    print(f"  Good posture  : {pct_good:.0f}%  ({good_seconds:.0f}s)")
    print(f"  Poor posture  : {pct_bad:.0f}%  ({bad_seconds:.0f}s)")
    if score_history:
        print(f"  Worst score   : {min(score_history)}%")
    print("══════════════════════════════════════════")
    print(f"  Posture log   : {CSV_FILE}")
    print("══════════════════════════════════════════")


if __name__ == "__main__":
    main()
