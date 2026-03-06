@echo off
echo ============================================================
echo AI Health Platform - Complete Setup and Training
echo ============================================================
echo.

echo Step 1: Installing dependencies...
echo ------------------------------------------------------------
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies!
    pause
    exit /b 1
)
echo.

echo Step 2: Preparing datasets...
echo ------------------------------------------------------------
python prepare_data.py
if %errorlevel% neq 0 (
    echo Error preparing datasets!
    pause
    exit /b 1
)
echo.

echo Step 3: Training disease risk models...
echo ------------------------------------------------------------
python train_disease_model.py
if %errorlevel% neq 0 (
    echo Error training disease models!
    pause
    exit /b 1
)
echo.

echo Step 4: Training stress detection models...
echo ------------------------------------------------------------
python train_stress_model.py
if %errorlevel% neq 0 (
    echo Error training stress models!
    pause
    exit /b 1
)
echo.

echo ============================================================
echo SUCCESS! All models trained successfully!
echo ============================================================
echo.
echo To start the API server, run:
echo   python main.py
echo.
echo Then visit: http://localhost:8000/api/docs
echo.
pause
