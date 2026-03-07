"""
Unified Launcher — Start the entire Wellness Companion system.

Usage:
    python launcher.py              # Start orchestrator + avatar
    python launcher.py --all        # Start everything including monitors
    python launcher.py --no-avatar  # Start orchestrator only (monitors push events)

Architecture:
    1. Orchestrator (port 8765)  — Central hub, WebSocket server
    2. Avatar (port 5173)        — Vite dev server, 3D avatar frontend
    3. Eye Care                  — Webcam blink/stare detection
    4. Posture Detection         — Webcam posture scoring
    5. Work Pattern (port 8001)  — Keyboard/mouse fatigue monitoring
    6. Air Quality (port 8002)   — AQI prediction with weather-aware advice
"""

import subprocess
import sys
import os
import time
import signal
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AVATAR_DIR = os.path.join(BASE_DIR, "avatar_system")
EYECARE_DIR = os.path.join(BASE_DIR, "Eye_care")
POSTURE_DIR = os.path.join(BASE_DIR, "posture_detection")
WORKPATTERN_DIR = os.path.join(BASE_DIR, "workpattern")
AIRQUALITY_DIR = os.path.join(BASE_DIR, "Air_quality_risk_pred")

processes = []


def start_process(name, cmd, cwd, shell=False):
    """Start a subprocess and track it."""
    print(f"  Starting {name}...")
    try:
        # Set process group isolation for proper cleanup
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            start_new_session = False
        else:
            creationflags = 0
            start_new_session = True
        
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            shell=shell,
            stdout=subprocess.DEVNULL,  # Avoid blocking on PIPE
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            start_new_session=start_new_session,
        )
        processes.append((name, proc))
        print(f"  {name} started (PID {proc.pid})")
        return proc
    except FileNotFoundError as e:
        print(f"  {name} FAILED: {e}")
        return None


def stop_all():
    """Gracefully stop all subprocesses."""
    print("\nShutting down...")
    for name, proc in processes:
        if proc.poll() is None:
            print(f"  Stopping {name} (PID {proc.pid})...")
            try:
                if os.name == "nt":
                    proc.terminate()
                else:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                proc.kill()
    print("All services stopped.")


def main():
    parser = argparse.ArgumentParser(description="Wellness Companion Launcher")
    parser.add_argument("--all", action="store_true", help="Start all modules including monitors")
    parser.add_argument("--no-avatar", action="store_true", help="Start orchestrator only")
    parser.add_argument("--no-monitors", action="store_true", help="Skip monitoring modules")
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("  AI Wellness Companion — Unified Launcher")
    print("=" * 60)
    print()

    python = sys.executable

    # 1. Orchestrator (always starts)
    start_process(
        "Orchestrator",
        [python, "orchestrator.py"],
        cwd=AVATAR_DIR,
    )
    time.sleep(2)

    # 2. Avatar frontend (unless --no-avatar)
    if not args.no_avatar:
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        start_process(
            "Avatar (Vite)",
            [npm_cmd, "run", "dev"],
            cwd=AVATAR_DIR,
        )
        time.sleep(2)

    # 3. Monitoring modules (with --all or not --no-monitors)
    if args.all or not args.no_monitors:
        # Eye Care (headless mode)
        if os.path.exists(os.path.join(EYECARE_DIR, "main.py")):
            start_process(
                "Eye Care",
                [python, "main.py", "--headless"],
                cwd=EYECARE_DIR,
            )

        # Posture Detection
        if os.path.exists(os.path.join(POSTURE_DIR, "posture_detection.py")):
            start_process(
                "Posture Detection",
                [python, "posture_detection.py"],
                cwd=POSTURE_DIR,
            )

        # Work Pattern Monitor + API
        if os.path.exists(os.path.join(WORKPATTERN_DIR, "main.py")):
            start_process(
                "Work Pattern",
                [python, "main.py"],
                cwd=WORKPATTERN_DIR,
            )

        # Air Quality Module
        if os.path.exists(os.path.join(AIRQUALITY_DIR, "app", "main.py")):
            start_process(
                "Air Quality",
                [python, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"],
                cwd=AIRQUALITY_DIR,
            )

    print()
    print("=" * 60)
    print("  System Running")
    print("=" * 60)
    print()
    print("  Orchestrator:  http://localhost:8765")
    if not args.no_avatar:
        print("  Avatar:        http://localhost:5173")
    if args.all or not args.no_monitors:
        print("  Air Quality:   http://localhost:8002")
    print()
    print("  Press Ctrl+C to stop all services")
    print("=" * 60)
    print()

    # Keep running until interrupted
    reported_exits = set()  # Track which processes we've already reported
    try:
        while True:
            # Check if any critical process died
            for name, proc in processes:
                pid = proc.pid
                if proc.poll() is not None and pid not in reported_exits:
                    print(f"  [!] {name} exited with code {proc.returncode}")
                    reported_exits.add(pid)  # Mark as reported
            time.sleep(5)
    except KeyboardInterrupt:
        stop_all()


if __name__ == "__main__":
    main()
