#!/bin/bash
# ============================================================
# AI Wellness Companion - Automated Setup Script (Linux/Mac)
# ============================================================

set -e  # Exit on error

echo ""
echo "============================================================"
echo "   AI Wellness Companion - Automated Setup"
echo "============================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ── Check Python Installation ──
echo "[1/6] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 is not installed"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi
python3 --version
echo -e "${GREEN}[OK]${NC} Python found"
echo ""

# ── Create Virtual Environment ──
echo "[2/6] Creating virtual environment..."
if [ -d ".venv" ]; then
    echo -e "${YELLOW}[SKIP]${NC} Virtual environment already exists"
else
    python3 -m venv .venv
    echo -e "${GREEN}[OK]${NC} Virtual environment created"
fi
echo ""

# ── Activate Virtual Environment ──
echo "[3/6] Activating virtual environment..."
source .venv/bin/activate
echo -e "${GREEN}[OK]${NC} Virtual environment activated"
echo ""

# ── Install Python Dependencies ──
echo "[4/6] Installing Python dependencies..."
echo "This may take 3-5 minutes..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}[OK]${NC} Python dependencies installed"
echo ""

# ── Setup Environment Variables ──
echo "[5/6] Setting up environment variables..."
if [ -f ".env" ]; then
    echo -e "${YELLOW}[SKIP]${NC} .env file already exists"
    echo -e "${YELLOW}[INFO]${NC} Make sure your API keys are configured"
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}[OK]${NC} Created .env from template"
        echo ""
        echo "!!! IMPORTANT !!!"
        echo "Edit .env file and add your API keys:"
        echo "  - AQI_WAQI_TOKEN (from https://aqicn.org/data-platform/token/)"
        echo "  - AQI_OWM_API_KEY (from https://openweathermap.org/api)"
        echo ""
    else
        echo -e "${YELLOW}[WARNING]${NC} .env.example not found, skipping .env creation"
    fi
fi
echo ""

# ── Install Avatar Frontend Dependencies ──
echo "[6/6] Installing Avatar frontend dependencies..."
if ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Node.js/npm not found, skipping avatar frontend setup"
    echo "Install Node.js from https://nodejs.org to use the avatar UI"
else
    echo -e "${GREEN}[INFO]${NC} Node.js found, installing avatar dependencies..."
    cd avatar_system
    if [ -f "package.json" ]; then
        npm install
        echo -e "${GREEN}[OK]${NC} Avatar dependencies installed"
    else
        echo -e "${YELLOW}[WARNING]${NC} package.json not found in avatar_system"
    fi
    cd ..
fi
echo ""

# ── Setup Complete ──
echo "============================================================"
echo "   Setup Complete!"
echo "============================================================"
echo ""
echo "Important: Edit .env file and add your API keys"
echo "  - AQI_WAQI_TOKEN (from https://aqicn.org/data-platform/token/)"
echo "  - AQI_OWM_API_KEY (from https://openweathermap.org/api)"
echo ""
echo "To start the system:"
echo "  python3 MASTER_LAUNCHER.py --all"
echo ""
echo "For help and options:"
echo "  python3 MASTER_LAUNCHER.py --help"
echo ""
echo "To activate virtual environment in future sessions:"
echo "  source .venv/bin/activate"
echo ""
echo "============================================================"

