"""
Simple Launcher — Wrapper for MASTER_LAUNCHER.py with sensible defaults

Usage:
    python launcher.py              # Start orchestrator + avatar UI
    python launcher.py --all        # Start all modules

For advanced options, use MASTER_LAUNCHER.py directly
"""

import subprocess
import sys
import os

def main():
    # Simple argument parsing
    if "--all" in sys.argv:
        # Start everything
        args = ["--all"]
    else:
        # Default: just orchestrator + avatar
        args = []
    
    # Call MASTER_LAUNCHER.py
    master_launcher = os.path.join(os.path.dirname(__file__), "MASTER_LAUNCHER.py")
    cmd = [sys.executable, master_launcher] + args
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
