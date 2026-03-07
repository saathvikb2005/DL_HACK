import time
from config import LOW_BLINK_RATE, CONTINUOUS_STARE_SEC, MAX_SCREEN_TIME_MIN


class FatigueDetector:

    def __init__(self):

        now = time.time()

        self._window_start = now
        self._window_blinks = 0
        self.blink_rate = 0

        self._last_blink_time = now
        self.stare_duration = 0

        self._session_start = now
        self._face_last_seen = now
        self.screen_time_min = 0

        self._away_threshold = 10

    def update(self, blink_happened, face_detected):

        now = time.time()
        events = []

        if face_detected:

            if now - self._face_last_seen > self._away_threshold:
                self._session_start = now
                self._window_start = now
                self._window_blinks = 0
                self._last_blink_time = now

            self._face_last_seen = now
            self.screen_time_min = (now - self._session_start) / 60

        if blink_happened:
            self._window_blinks += 1
            self._last_blink_time = now

        window_elapsed = now - self._window_start

        if window_elapsed >= 60:

            self.blink_rate = self._window_blinks / (window_elapsed / 60)

            if self.blink_rate < LOW_BLINK_RATE and face_detected:
                events.append("low_blink")

            self._window_start = now
            self._window_blinks = 0

        if face_detected:

            self.stare_duration = now - self._last_blink_time

            if self.stare_duration >= CONTINUOUS_STARE_SEC:
                events.append("continuous_stare")
                self._last_blink_time = now

        if face_detected and self.screen_time_min >= MAX_SCREEN_TIME_MIN:
            events.append("long_screen_time")
            self._session_start = now

        return events

    def get_status(self):

        return {
            "blink_rate": round(self.blink_rate, 1),
            "stare_duration_sec": round(self.stare_duration, 1),
            "screen_time_min": round(self.screen_time_min, 1),
        }