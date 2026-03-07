@echo off
echo ============================================
echo Starting INTEGRATED Work Pattern System
echo ============================================
echo.
echo Starting monitor in background...
cd /d "%~dp0"
start "Work Pattern Monitor" cmd /k "python integrated_monitor.py"
timeout /t 3
echo.
echo Starting API server...
python main.py
