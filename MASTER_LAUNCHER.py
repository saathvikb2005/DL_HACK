"""
AI WELLNESS COMPANION - MASTER CONTROL LAUNCHER
================================================

Complete health monitoring system with 7 integrated modules:
  1. Orchestrator (Port 8765) - Central event hub, WebSocket server
  2. Avatar UI (Port 5173) - 3D avatar with dynamic health feedback
  3. Eye Care - Blink rate, stare detection, screen time monitoring
  4. Posture Detection - Real-time posture scoring with MediaPipe
  5. Workpattern (Port 8001) - Fatigue detection via typing behavior
  6. Air Quality (Port 8002) - AQI prediction with weather awareness
  7. Vijitha (Port 8000) - Disease risk & mental health assessment

Usage:
    python MASTER_LAUNCHER.py --all                    # All modules, normal mode
    python MASTER_LAUNCHER.py --all --debug            # All modules, debug mode
    python MASTER_LAUNCHER.py --orchestrator-only      # Just orchestrator
    python MASTER_LAUNCHER.py --no-avatar              # No UI, just backend
    python MASTER_LAUNCHER.py --select eye,posture     # Specific modules only
    python MASTER_LAUNCHER.py --help                   # Show all options

Debug Mode:
    --debug         Shows all console output from modules
    (no debug)      Suppresses output, clean terminal

Module Names for --select:
    eye, posture, workpattern, airquality, vijitha
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from datetime import datetime

# =====================================================================
# CONFIGURATION
# =====================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODULES = {
    "orchestrator": {
        "name": "Orchestrator",
        "cmd": [sys.executable, "orchestrator.py"],
        "cwd": os.path.join(BASE_DIR, "avatar_system"),
        "port": 8765,
        "required": True,
        "wait": 2,
    },
    "avatar": {
        "name": "Avatar UI",
        "cmd": ["npm.cmd" if os.name == "nt" else "npm", "run", "dev"],
        "cwd": os.path.join(BASE_DIR, "avatar_system"),
        "port": 5173,
        "required": False,
        "wait": 3,
    },
    "eye": {
        "name": "Eye Care",
        "cmd": [sys.executable, "main.py", "--headless"],
        "cwd": os.path.join(BASE_DIR, "Eye_care"),
        "port": None,
        "required": False,
        "wait": 1,
    },
    "posture": {
        "name": "Posture Detection",
        "cmd": [sys.executable, "posture_detection.py"],
        "cwd": os.path.join(BASE_DIR, "posture_detection"),
        "port": None,
        "required": False,
        "wait": 1,
    },
    "workpattern": {
        "name": "Workpattern Monitor",
        "cmd": [sys.executable, "integrated_monitor.py"],
        "cwd": os.path.join(BASE_DIR, "workpattern"),
        "port": 8001,
        "required": False,
        "wait": 1,
    },
    "airquality": {
        "name": "Air Quality",
        "cmd": [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8002"],
        "cwd": os.path.join(BASE_DIR, "Air_quality_risk_pred"),
        "port": 8002,
        "required": False,
        "wait": 2,
    },
    "vijitha": {
        "name": "Vijitha Health AI",
        "cmd": [sys.executable, "main.py"],
        "cwd": os.path.join(BASE_DIR, "vijitha"),
        "port": 8000,
        "required": False,
        "wait": 2,
    },
}

processes = []

# =====================================================================
# PROCESS MANAGEMENT
# =====================================================================

def start_process(module_id, config, debug_mode=False):
    """Start a subprocess and track it."""
    name = config["name"]
    
    # Check if module exists
    main_file = config["cmd"][1] if len(config["cmd"]) > 1 else config["cmd"][0]
    if not os.path.exists(os.path.join(config["cwd"], main_file.split()[0])):
        if module_id == "avatar":
            # For avatar, check if frontend directory exists
            if not os.path.exists(config["cwd"]):
                print(f"  ⚠️  {name}: Directory not found, skipping")
                return None
        else:
            print(f"  ⚠️  {name}: Not found, skipping")
            return None
    
    print(f"  🚀 Starting {name}...", end=" ")
    
    try:
        # Configure output handling based on debug mode
        if debug_mode:
            stdout = None  # Show output in terminal
            stderr = None
        else:
            stdout = subprocess.DEVNULL  # Suppress output
            stderr = subprocess.DEVNULL
        
        # Set process group isolation for proper cleanup
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            start_new_session = False
        else:
            creationflags = 0
            start_new_session = True
        
        proc = subprocess.Popen(
            config["cmd"],
            cwd=config["cwd"],
            shell=False,
            stdout=stdout,
            stderr=stderr,
            creationflags=creationflags,
            start_new_session=start_new_session,
        )
        
        processes.append((module_id, name, proc))
        
        port_info = f"on port {config['port']}" if config['port'] else ""
        print(f"✅ (PID {proc.pid}) {port_info}")
        
        return proc
        
    except FileNotFoundError as e:
        print(f"❌ Failed - {e}")
        return None
    except Exception as e:
        print(f"❌ Error - {e}")
        return None


def stop_all():
    """Gracefully stop all subprocesses."""
    if not processes:
        return
    
    print("\n" + "=" * 60)
    print("  🛑 Shutting Down All Services")
    print("=" * 60)
    
    for module_id, name, proc in processes:
        if proc.poll() is None:
            print(f"  Stopping {name} (PID {proc.pid})...", end=" ")
            try:
                if os.name == "nt":
                    proc.terminate()
                    time.sleep(0.5)
                    if proc.poll() is None:
                        proc.kill()
                else:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    time.sleep(0.5)
                    if proc.poll() is None:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                print("✅")
            except Exception as e:
                print(f"⚠️ {e}")
        else:
            print(f"  {name} already stopped")
    
    print("\n  All services stopped.\n")


def check_running_processes():
    """Check if any processes have died unexpectedly."""
    global processes
    to_report = []
    
    for module_id, name, proc in processes:
        if proc.poll() is not None:
            # Process has exited - add to report list
            return_code = proc.returncode
            to_report.append((module_id, name, return_code))
    
    # Log and remove reported processes
    if to_report:
        for module_id, name, return_code in to_report:
            if return_code != 0:
                print(f"  ⚠️  {name} exited with code {return_code}")
            else:
                print(f"  ℹ️  {name} stopped")
        
        # Remove dead processes from list to avoid repeated logging
        processes = [(mid, n, p) for mid, n, p in processes if p.poll() is None]


# =====================================================================
# MAIN LAUNCHER
# =====================================================================

def print_banner(debug_mode=False):
    """Print startup banner."""
    print("\n" + "=" * 60)
    print("  🏥 AI WELLNESS COMPANION - MASTER CONTROL")
    print("=" * 60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Mode: {'DEBUG (verbose)' if debug_mode else 'NORMAL (quiet)'}")
    print("=" * 60 + "\n")


def print_summary(selected_modules, debug_mode=False):
    """Print running services summary."""
    print("\n" + "=" * 60)
    print("  ✅ SYSTEM RUNNING")
    print("=" * 60)
    
    active_ports = []
    
    if "orchestrator" in selected_modules:
        active_ports.append(("Orchestrator API", "http://localhost:8765"))
    
    if "avatar" in selected_modules:
        active_ports.append(("Avatar UI", "http://localhost:5173"))
    
    if "airquality" in selected_modules:
        active_ports.append(("Air Quality API", "http://localhost:8002/api/docs"))
    
    if "workpattern" in selected_modules:
        active_ports.append(("Workpattern API", "http://localhost:8001/api/docs"))
    
    if "vijitha" in selected_modules:
        active_ports.append(("Vijitha Health API", "http://localhost:8000/api/docs"))
    
    if active_ports:
        print("\n  🌐 Active Services:")
        for service, url in active_ports:
            print(f"    • {service:20s} {url}")
    
    print("\n  📊 Running Modules:")
    for module_id, name, proc in processes:
        status = "✅ Running" if proc.poll() is None else "❌ Stopped"
        print(f"    • {name:20s} (PID {proc.pid:6d}) {status}")
    
    print("\n  💡 Controls:")
    print("    • Press Ctrl+C to stop all services")
    if not debug_mode:
        print("    • Use --debug flag to see module output")
    
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="AI Wellness Companion - Master Control Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python MASTER_LAUNCHER.py --all                     # Start all modules
  python MASTER_LAUNCHER.py --all --debug             # Start all with debug output
  python MASTER_LAUNCHER.py --select eye,posture      # Start specific modules only
  python MASTER_LAUNCHER.py --no-avatar               # Backend only (no UI)
  python MASTER_LAUNCHER.py --orchestrator-only       # Just orchestrator

Module Names:
  eye, posture, workpattern, airquality, vijitha
        """)
    
    parser.add_argument("--all", action="store_true", 
                       help="Start all modules (orchestrator, avatar, and all health monitors)")
    parser.add_argument("--orchestrator-only", action="store_true",
                       help="Start only the orchestrator (no UI, no monitors)")
    parser.add_argument("--no-avatar", action="store_true",
                       help="Start all modules except avatar UI")
    parser.add_argument("--select", type=str,
                       help="Select specific modules (comma-separated): eye,posture,workpattern,airquality,vijitha")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug mode (show all module output in console)")
    
    args = parser.parse_args()
    
    # Determine which modules to start
    selected_modules = set()
    
    if args.orchestrator_only:
        selected_modules = {"orchestrator"}
    elif args.select:
        selected_modules = {"orchestrator"}  # Always include orchestrator
        module_names = [m.strip().lower() for m in args.select.split(",")]
        for name in module_names:
            if name in MODULES:
                selected_modules.add(name)
            else:
                print(f"⚠️  Unknown module: {name}")
                print(f"Available modules: {', '.join([k for k in MODULES.keys() if k not in ['orchestrator', 'avatar']])}")
                return 1
    elif args.no_avatar:
        selected_modules = set(MODULES.keys()) - {"avatar"}
    elif args.all:
        selected_modules = set(MODULES.keys())
    else:
        # Default: orchestrator + avatar only
        selected_modules = {"orchestrator", "avatar"}
    
    # Print startup banner
    print_banner(debug_mode=args.debug)
    
    # Start modules in order
    start_order = ["orchestrator", "avatar", "airquality", "vijitha", "workpattern", "eye", "posture"]
    
    for module_id in start_order:
        if module_id in selected_modules:
            config = MODULES[module_id]
            proc = start_process(module_id, config, debug_mode=args.debug)
            if proc:
                time.sleep(config["wait"])
            elif config["required"]:
                print(f"\n❌ Critical module {config['name']} failed to start. Aborting.")
                stop_all()
                return 1
    
    # Print summary
    print_summary(selected_modules, debug_mode=args.debug)
    
    # Monitor processes
    try:
        check_interval = 5
        while True:
            time.sleep(check_interval)
            check_running_processes()
            
    except KeyboardInterrupt:
        stop_all()
        return 0


if __name__ == "__main__":
    try:
        exit(main())
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        stop_all()
        exit(1)
