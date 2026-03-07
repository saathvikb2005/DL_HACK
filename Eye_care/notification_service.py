import os
import sys
import time
import logging
from config import COOLDOWN_BLINK, COOLDOWN_STARE, COOLDOWN_SCREEN_TIME

# Add parent directory to path for module_bridge
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
try:
    from module_bridge import push_event
except ImportError:
    def push_event(*a, **k): pass

logger = logging.getLogger(__name__)

# ── Notification definitions ─────────────────────────────────────────────────
# Each entry: (title, message, tip, cooldown)
NOTIFICATIONS = {
    "low_blink": (
        "👁️  Blink Reminder",
        "Your blink rate is low — your eyes are drying out!",
        "💡 Tip: Slowly close your eyes for 3–4 seconds, repeat 5 times.",
        COOLDOWN_BLINK,
    ),
    "continuous_stare": (
        "🛑  Eye Strain Alert",
        "You haven't blinked in a while — take a micro-break now.",
        "💡 Tip: Close your eyes for 15 seconds and breathe deeply.",
        COOLDOWN_STARE,
    ),
    "long_screen_time": (
        "🖥  Screen Time Warning",
        "You've been staring at the screen too long!",
        "💡 Tip: Follow the 20-20-20 rule — look at something 20 ft away for 20 seconds.",
        COOLDOWN_SCREEN_TIME,
    ),
}

# Severity mapping for visual styling
_SEVERITY = {
    "low_blink": "warning",
    "continuous_stare": "urgent",
    "long_screen_time": "warning",
}


class NotificationService:

    def __init__(self):
        self._last_sent = {}
        self.backend = self._detect_backend()
        logger.info("Notification backend: %s", self.backend)

    @staticmethod
    def _detect_backend():
        """Pick the best available notification backend.
        Windows toasts/popups are disabled — avatar voice output is used instead.
        """
        return "console"

    # ── Sending ───────────────────────────────────────────────────────────────

    def _send(self, title, message, event_type=""):
        severity = _SEVERITY.get(event_type, "info")
        try:
            if self.backend == "winotify":
                self._send_winotify(title, message, severity)
            elif self.backend == "plyer":
                self._send_plyer(title, message)
            else:
                self._send_console(title, message, severity)
        except Exception as e:
            logger.warning("Notification backend '%s' failed (%s), using console", self.backend, e)
            self._send_console(title, message, severity)

    def _send_winotify(self, title, message, severity):
        from winotify import Notification, audio

        toast = Notification(
            app_id="EyeGuard",
            title=title,
            msg=message,
            duration="short" if severity == "info" else "long",
        )

        if severity == "urgent":
            toast.set_audio(audio.Reminder, loop=False)
        else:
            toast.set_audio(audio.Default, loop=False)

        toast.show()

    @staticmethod
    def _send_plyer(title, message):
        from plyer import notification

        notification.notify(
            title=title,
            message=message,
            timeout=10,
            app_name="EyeGuard",
        )

    @staticmethod
    def _send_console(title, message, severity="info"):
        """Rich console fallback with box-drawing characters."""
        colors = {
            "info":    "\033[96m",   # cyan
            "warning": "\033[93m",   # yellow
            "urgent":  "\033[91m",   # red
        }
        color = colors.get(severity, "\033[0m")
        reset = "\033[0m"
        bold = "\033[1m"

        lines = message.split("\n")
        width = max(len(title), *(len(l) for l in lines)) + 4

        print()
        print(f"{color}{'━' * (width + 2)}{reset}")
        print(f"{color}┃{reset} {bold}{title:<{width}}{reset}{color}┃{reset}")
        print(f"{color}┃{'─' * (width)}┃{reset}")
        for line in lines:
            print(f"{color}┃{reset} {line:<{width - 1}}{color}┃{reset}")
        print(f"{color}{'━' * (width + 2)}{reset}")
        print()

    # ── Public API ────────────────────────────────────────────────────────────

    def notify(self, event_type, extra_info=""):
        if event_type not in NOTIFICATIONS:
            return

        title, message, tip, cooldown = NOTIFICATIONS[event_type]

        now = time.time()
        if now - self._last_sent.get(event_type, 0) < cooldown:
            return

        full_message = message
        if extra_info:
            full_message += f"\n{extra_info}"
        full_message += f"\n{tip}"

        self._send(title, full_message, event_type)
        self._last_sent[event_type] = now

        # Push event to orchestrator → avatar
        event_map = {
            "low_blink": "LOW_BLINK_RATE",
            "continuous_stare": "CONTINUOUS_STARE",
            "long_screen_time": "LONG_SCREEN_TIME",
        }
        orch_event = event_map.get(event_type)
        if orch_event:
            push_event(orch_event, "eye_care", {"detail": extra_info} if extra_info else None)