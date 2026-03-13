@echo off
REM Professional Avatar System - Setup Script
REM ==========================================

echo.
echo ========================================
echo   Professional Avatar Lip Sync Setup
echo ========================================
echo.

REM Step 1: Install Python dependencies
echo [1/3] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)
echo ✅ Python dependencies installed
echo.

REM Step 2: Create directories
echo [2/3] Creating directories...
if not exist "audio_cache" mkdir audio_cache
if not exist "tools" mkdir tools
echo ✅ Directories created
echo.

REM Step 3: Check for Rhubarb
echo [3/3] Checking for Rhubarb Lip Sync...
if exist "tools\rhubarb.exe" (
    echo ✅ Rhubarb found at tools\rhubarb.exe
    tools\rhubarb.exe --version
) else (
    echo.
    echo ⚠️  Rhubarb Lip Sync NOT FOUND
    echo.
    echo Please download Rhubarb from:
    echo https://github.com/DanielSWolf/rhubarb-lip-sync/releases
    echo.
    echo Extract and place rhubarb.exe in:
    echo %CD%\tools\rhubarb.exe
    echo.
    echo The system will work without Rhubarb but with reduced quality.
    echo.
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. If Rhubarb is missing, download it from the link above
echo 2. Run START_AVATAR.bat to start the system
echo 3. Open http://localhost:5173 in your browser
echo.
echo Check LIPSYNC_SETUP.md for detailed documentation.
echo.
pause
