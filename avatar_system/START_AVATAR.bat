@echo off
REM Wellness Avatar System - Windows Startup Script
REM ================================================

echo.
echo ========================================
echo   Wellness Avatar System
echo   Starting Backend + Frontend
echo ========================================
echo.

REM Start Orchestrator Backend
echo [1/2] Starting Orchestrator (Port 8765)...
start "Wellness Orchestrator" cmd /k "cd /d %~dp0 && python orchestrator.py"
timeout /t 3 /nobreak >nul

REM Start Vite Frontend
echo [2/2] Starting Avatar Frontend (Port 5173)...
start "Avatar Frontend" cmd /k "cd /d %~dp0 && npm run dev"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Servers Started!
echo ========================================
echo.
echo Backend:  http://localhost:8765
echo Frontend: http://localhost:5173
echo.
echo Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo Press any key to close this window...
pause >nul
