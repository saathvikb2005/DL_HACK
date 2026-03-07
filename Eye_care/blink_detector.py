"""
Blink Detector — MediaPipe FaceLandmarker with:
• EAR smoothing
• 10-second auto calibration
• Blink pattern detection
• EAR velocity detection for fast blinks
"""

import os
import time
import urllib.request
import numpy as np
import mediapipe as mp
from collections import deque
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from config import EAR_CONSEC_FRAMES

BLINK_MIN_FRAMES = 1
BLINK_MAX_FRAMES = EAR_CONSEC_FRAMES * 2  # upper bound for valid blink duration

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]


MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "face_landmarker.task")


def _ensure_model():
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 0:
        return

    os.makedirs(MODEL_DIR, exist_ok=True)

    tmp_path = MODEL_PATH + ".tmp"
    print("Downloading MediaPipe Face Landmarker model...")
    try:
        urllib.request.urlretrieve(MODEL_URL, tmp_path)
        os.replace(tmp_path, MODEL_PATH)
        print("Model downloaded successfully.")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


class BlinkDetector:

    def __init__(self):

        _ensure_model()

        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)

        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=1,
            running_mode=vision.RunningMode.IMAGE
        )

        self.landmarker = vision.FaceLandmarker.create_from_options(options)

        self._consec_frames = 0
        self.blink_count = 0
        self.last_ear = 0.0
        self.face_detected = False

        # EAR smoothing buffer
        self.ear_history = deque(maxlen=5)

        # EAR velocity history (detect rapid drops)
        self.prev_ear = None

        # Calibration variables
        self.calibration_start = time.time()
        self.calibration_duration = 10
        self.calibration_values = []
        self.calibrated = False
        self.dynamic_threshold = 0.24

    @staticmethod
    def _ear(landmarks, eye_indices, w, h):

        pts = np.array(
            [(landmarks[i].x * w, landmarks[i].y * h) for i in eye_indices],
            dtype=np.float64
        )

        v1 = np.linalg.norm(pts[1] - pts[5])
        v2 = np.linalg.norm(pts[2] - pts[4])
        h1 = np.linalg.norm(pts[0] - pts[3])

        if h1 == 0:
            return 0

        return (v1 + v2) / (2.0 * h1)

    def process_frame(self, frame):

        h, w = frame.shape[:2]

        rgb = frame[:, :, ::-1]
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        results = self.landmarker.detect(mp_image)

        output = {
            "face_detected": False,
            "ear": 0.0,
            "blink_happened": False,
            "blink_count": self.blink_count,
            "face_distance_ratio": 0.0,
        }

        if not results.face_landmarks:
            self.face_detected = False
            return output

        landmarks = results.face_landmarks[0]
        self.face_detected = True

        # Calculate EAR
        left_ear = self._ear(landmarks, LEFT_EYE, w, h)
        right_ear = self._ear(landmarks, RIGHT_EYE, w, h)
        ear_raw = (left_ear + right_ear) / 2

        # Smooth EAR
        self.ear_history.append(ear_raw)
        ear = sum(self.ear_history) / len(self.ear_history)

        self.last_ear = ear

        # ─── Calibration Phase ───
        if not self.calibrated:
            self.calibration_values.append(ear)

            if time.time() - self.calibration_start >= self.calibration_duration:

                avg_ear = np.mean(self.calibration_values)

                # Dynamic threshold based on user's eye shape
                self.dynamic_threshold = avg_ear * 0.75

                self.calibrated = True

                print("\nCalibration complete")
                print(f"Average EAR: {avg_ear:.3f}")
                print(f"Dynamic Blink Threshold: {self.dynamic_threshold:.3f}\n")

        threshold = self.dynamic_threshold

        blink_happened = False

        # EAR velocity detection (detect fast blink drops)
        ear_drop = 0
        if self.prev_ear is not None:
            ear_drop = self.prev_ear - ear

        self.prev_ear = ear

        # Blink pattern detection
        if ear < threshold:
            self._consec_frames += 1
        else:
            if BLINK_MIN_FRAMES <= self._consec_frames <= BLINK_MAX_FRAMES:
                self.blink_count += 1
                blink_happened = True
            self._consec_frames = 0

        # Fast blink detection using EAR drop speed
        if ear_drop > 0.05:
            self._consec_frames = 1

        # Face distance estimation
        left_outer = landmarks[LEFT_EYE[0]]
        right_outer = landmarks[RIGHT_EYE[0]]
        face_distance_ratio = abs(left_outer.x - right_outer.x)

        output.update({
            "face_detected": True,
            "ear": round(ear, 4),
            "blink_happened": blink_happened,
            "blink_count": self.blink_count,
            "face_distance_ratio": round(face_distance_ratio, 4),
        })

        return output

    def reset_blink_count(self):
        self.blink_count = 0

    def close(self):
        if self.landmarker:
            try:
                self.landmarker.close()
            except Exception:
                pass