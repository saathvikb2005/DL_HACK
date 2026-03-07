"""
run_background.pyw
══════════════════
Launches posture detection in the background — no terminal, no camera window.
A system-tray icon shows current posture status (green / orange / red).
Right-click the tray icon to Stop.

Run by double-clicking this file, or:
    pythonw run_background.pyw

Requires:
    pip install pystray Pillow
"""

import sys
import os
import threading

# ── Make sure posture_detection is importable from the same folder ────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Check dependencies ────────────────────────────────────────────────────────
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk(); root.withdraw()
    messagebox.showerror(
        "Missing packages",
        "pystray and Pillow are required for background mode.\n\n"
        "Run:  pip install pystray Pillow\n\nthen try again."
    )
    sys.exit(1)

import posture_detection as _pd

# ── Tray icon helpers ─────────────────────────────────────────────────────────
_COLORS = {
    "good":     (34,  197,  94),   # green
    "moderate": (251, 146,  60),   # orange
    "bad":      (239,  68,  68),   # red
    "idle":     (100, 100, 100),   # grey
}

def _make_icon(rgb=(100, 100, 100)):
    """64×64 circle on dark background."""
    img  = Image.new("RGBA", (64, 64), (30, 30, 30, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([6, 6, 58, 58], fill=rgb)
    return img


def _score_to_rgb(score: int):
    if score >= 70:
        return _COLORS["good"]
    if score >= 50:
        return _COLORS["moderate"]
    return _COLORS["bad"]


# ── Detection thread ──────────────────────────────────────────────────────────
_tray_icon   = None
_last_status = "Starting…"
_last_score  = 0


def _patch_hud():
    """
    Monkey-patch draw_hud so the tray icon colour updates live
    without touching the main posture_detection source.
    """
    _orig_log = _pd.log_row

    def _hooked_log(neck_a, sh_d, sp_a, sh_z, n_s, s_s, sp_s, r_s, total, status):
        global _last_status, _last_score
        _last_score  = total
        _last_status = status
        if _tray_icon is not None:
            try:
                _tray_icon.icon  = _make_icon(_score_to_rgb(total))
                _tray_icon.title = f"Posture  {total}% — {status}"
            except Exception:
                pass
        _orig_log(neck_a, sh_d, sp_a, sh_z, n_s, s_s, sp_s, r_s, total, status)

    _pd.log_row = _hooked_log


def _run_detection():
    _patch_hud()
    _pd.main(headless=True)


# ── Tray menu actions ─────────────────────────────────────────────────────────
def _on_stop(icon, _item):
    _pd._stop_event.set()
    icon.stop()


def _on_status(icon, _item):
    pass  # label only – no action


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    global _tray_icon

    # Start detection in a daemon thread
    t = threading.Thread(target=_run_detection, daemon=True, name="PostureDetection")
    t.start()

    menu = pystray.Menu(
        pystray.MenuItem(lambda _: f"Score: {_last_score}% — {_last_status}",
                         _on_status, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Stop", _on_stop),
    )

    _tray_icon = pystray.Icon(
        name    = "PostureMonitor",
        icon    = _make_icon(_COLORS["idle"]),
        title   = "Posture Monitor — starting…",
        menu    = menu,
    )
    _tray_icon.run()   # blocks until icon.stop() is called


if __name__ == "__main__":
    main()
