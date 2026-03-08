@echo off
REM ============================================================
REM AI Wellness Companion - Automated Setup Script (Windows)
REM ============================================================
echo.
echo ============================================================
echo    AI Wellness Companion - Automated Setup
echo ============================================================
echo.

REM ── Check Python Installation ──
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
python --version
echo [OK] Python found
echo.

REM ── Create Virtual Environment ──
echo [2/6] Creating virtual environment...
if exist .venv (
    echo [SKIP] Virtual environment already exists
) else (
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)
echo.

REM ── Activate Virtual Environment ──
echo [3/6] Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM ── Install Python Dependencies ──
echo [4/6] Installing Python dependencies...
echo This may take 3-5 minutes...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed
echo.

REM ── Setup Environment Variables ──
echo [5/6] Setting up environment variables...
if exist .env (
    echo [SKIP] .env file already exists
    echo [INFO] Make sure your API keys are configured
) else (
    if exist .env.example (
        copy .env.example .env
        echo [OK] Created .env from template
        echo.
        echo !!! IMPORTANT !!!
        echo Edit .env file and add your API keys:
        echo   - AQI_WAQI_TOKEN (from https://aqicn.org/data-platform/token/)
        echo   - AQI_OWM_API_KEY (from https://openweathermap.org/api)
        echo.
    ) else (
        echo [WARNING] .env.example not found, skipping .env creation
    )
)
echo.

REM ── Install Avatar Frontend Dependencies ──
echo [6/6] Installing Avatar frontend dependencies...
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Node.js/npm not found, skipping avatar frontend setup
    echo Install Node.js from https://nodejs.org to use the avatar UI
) else (
    echo [INFO] Node.js found, installing avatar dependencies...
    cd avatar_system
    if exist package.json (
        call npm install
        if %errorlevel% neq 0 (
            echo [WARNING] Failed to install avatar dependencies
        ) else (
            echo [OK] Avatar dependencies installed
        )
    ) else (
        echo [WARNING] package.json not found in avatar_system
    )
    cd ..
)
echo.

REM ── Setup Complete ──
echo ============================================================
echo    Setup Complete!
echo ============================================================
echo.
echo Important: Edit .env file and add your API keys
echo   - AQI_WAQI_TOKEN (from https://aqicn.org/data-platform/token/)
echo   - AQI_OWM_API_KEY (from https://openweathermap.org/api)
echo.
echo To start the system:
echo   python MASTER_LAUNCHER.py --all
echo.
echo For help and options:
echo   python MASTER_LAUNCHER.py --help
echo.
echo ============================================================
pause
