#!/bin/bash

echo "============================================================"
echo "AI Health Platform - Complete Setup and Training"
echo "============================================================"
echo ""

echo "Step 1: Installing dependencies..."
echo "------------------------------------------------------------"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error installing dependencies!"
    exit 1
fi
echo ""

echo "Step 2: Preparing datasets..."
echo "------------------------------------------------------------"
python prepare_data.py
if [ $? -ne 0 ]; then
    echo "Error preparing datasets!"
    exit 1
fi
echo ""

echo "Step 3: Training disease risk models..."
echo "------------------------------------------------------------"
python train_disease_model.py
if [ $? -ne 0 ]; then
    echo "Error training disease models!"
    exit 1
fi
echo ""

echo "Step 4: Training stress detection models..."
echo "------------------------------------------------------------"
python train_stress_model.py
if [ $? -ne 0 ]; then
    echo "Error training stress models!"
    exit 1
fi
echo ""

echo "============================================================"
echo "SUCCESS! All models trained successfully!"
echo "============================================================"
echo ""
echo "To start the API server, run:"
echo "  python main.py"
echo ""
echo "Then visit: http://localhost:8000/api/docs"
echo ""
