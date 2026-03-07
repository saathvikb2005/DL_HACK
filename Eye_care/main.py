"""
EyeGuard — Background Eye Strain Detection System for Developers

Runs silently, monitors eye behavior via webcam, and sends desktop
notifications when eye strain is detected.

Usage:
    python main.py             # Normal mode (with live preview window)
    python main.py --headless  # Background mode (no window, minimal CPU)
    python main.py --debug     # Show EAR values and face landmarks overlay
"""

import cv2
import time
import argparse
import logging
import sys

from config import CAMERA_INDEX, CAPTURE_FPS, PROCESS_EVERY_N_FRAMES
from blink_detector import BlinkDetector
from fatigue_detector import FatigueDetector
from notification_service import NotificationService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run(headless: bool = False, debug: bool = False):
    """Main monitoring loop."""
    logger.info("🛡️  EyeGuard starting...")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        logger.error("Cannot open webcam (index %d). Exiting.", CAMERA_INDEX)
        sys.exit(1)

    # Set low resolution + FPS to save CPU
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, CAPTURE_FPS)

    blink_det = BlinkDetector()
    fatigue_det = FatigueDetector()
    notifier = NotificationService()

    frame_count = 0
    frame_delay = 1.0 / CAPTURE_FPS
    last_status_log = time.time()

    logger.info("👁️  Monitoring started. Press Ctrl+C or 'q' to stop.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame. Retrying...")
                time.sleep(1)
                continue

            frame_count += 1

            # Only process every Nth frame to save CPU
            if frame_count % PROCESS_EVERY_N_FRAMES != 0:
                if not headless:
                    cv2.imshow("EyeGuard", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                time.sleep(frame_delay)
                continue

            # ── Detect eyes ──
            result = blink_det.process_frame(frame)

            # ── Check fatigue ──
            events = fatigue_det.update(
                blink_happened=result["blink_happened"],
                face_detected=result["face_detected"],
            )

            # ── Send notifications ──
            status = fatigue_det.get_status()
            for event in events:
                extra = ""
                if event == "low_blink":
                    extra = f"Blink rate: {status['blink_rate']}/min"
                elif event == "long_screen_time":
                    extra = f"Screen time: {status['screen_time_min']:.0f} minutes"
                notifier.notify(event, extra_info=extra)

            # ── Log status periodically ──
            if time.time() - last_status_log >= 30:
                if result["face_detected"]:
                    logger.info(
                        "Status: blinks=%d  rate=%.1f/min  stare=%.0fs  screen=%.0fmin  EAR=%.3f",
                        result["blink_count"],
                        status["blink_rate"],
                        status["stare_duration_sec"],
                        status["screen_time_min"],
                        result["ear"],
                    )
                else:
                    logger.info("Status: face not detected (user away)")
                last_status_log = time.time()

            # ── Display window (if not headless) ──
            if not headless:
                display = frame.copy()
                _draw_hud(display, result, status, debug)
                cv2.imshow("EyeGuard", display)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            time.sleep(frame_delay)

    except KeyboardInterrupt:
        logger.info("Stopped by user.")
    finally:
        blink_det.close()
        cap.release()
        if not headless:
            cv2.destroyAllWindows()
        logger.info("EyeGuard shut down.")


def _draw_hud(frame, result, status, debug):
    """Draw a simple heads-up display on the preview window."""
    h, w = frame.shape[:2]
    color_ok = (0, 200, 0)
    color_warn = (0, 100, 255)

    face_text = "Face: Detected" if result["face_detected"] else "Face: Not Found"
    face_color = color_ok if result["face_detected"] else color_warn
    cv2.putText(frame, face_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, face_color, 2)

    if result["face_detected"]:
        # Blink info
        blink_color = color_warn if status["blink_rate"] < 10 else color_ok
        cv2.putText(
            frame,
            f"Blinks: {result['blink_count']}  Rate: {status['blink_rate']:.0f}/min",
            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, blink_color, 1,
        )

        # Screen time
        st_color = color_warn if status["screen_time_min"] >= 30 else color_ok
        cv2.putText(
            frame,
            f"Screen: {status['screen_time_min']:.0f} min",
            (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, st_color, 1,
        )

        # Stare duration
        stare_color = color_warn if status["stare_duration_sec"] >= 15 else color_ok
        cv2.putText(
            frame,
            f"Stare: {status['stare_duration_sec']:.0f}s",
            (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, stare_color, 1,
        )

        if debug:
            cv2.putText(
                frame,
                f"EAR: {result['ear']:.4f}  Dist: {result['face_distance_ratio']:.3f}",
                (10, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1,
            )

    # Bottom bar
    cv2.putText(
        frame,
        "EyeGuard | Press 'q' to quit",
        (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1,
    )
    if result["face_detected"] and result["ear"] is not None:
        cv2.putText(
            frame,
            f"EAR: {result['ear']:.3f}",
            (400, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EyeGuard — Background Eye Strain Detector")
    parser.add_argument("--headless", action="store_true", help="Run without preview window")
    parser.add_argument("--debug", action="store_true", help="Show EAR values and debug info")
    args = parser.parse_args()
    run(headless=args.headless, debug=args.debug)
