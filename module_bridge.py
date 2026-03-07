"""
Module Bridge — Pushes monitoring events to the Wellness Orchestrator.

Usage from any monitoring module:
    from module_bridge import push_event
    push_event("LOW_BLINK_RATE", "eye_care", {"blink_rate": 5.2})
"""

import threading
import logging
import urllib.request
import json

logger = logging.getLogger(__name__)

ORCHESTRATOR_URL = "http://localhost:8765/api/event"


def push_event(event_type: str, source: str, context: dict = None):
    """
    Non-blocking push of a health event to the orchestrator.
    Silently fails if orchestrator is not running.
    """
    def _send():
        payload = {
            "event_type": event_type,
            "source": source,
        }
        if context:
            payload["context"] = context

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            ORCHESTRATOR_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                result = json.loads(resp.read().decode())
                logger.debug("Event pushed: %s → %s", event_type, result.get("status"))
        except Exception as e:
            logger.debug("Orchestrator not reachable: %s", e)

    # Fire and forget — don't block the monitoring loop
    threading.Thread(target=_send, daemon=True).start()
