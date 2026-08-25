#!/bin/bash

# LightShare V1.0 - macOS / Linux Launcher
# Launches dedicated Desktop GUI Window or Headless Local Server

GREEN='\033[1;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

clear
echo ""
echo -e "${CYAN}========================================================================${NC}"
echo -e "${GREEN}    [APP] LIGHTSHARE V1.0 - DESKTOP AND SERVER LAUNCHER${NC}"
echo -e "${CYAN}========================================================================${NC}"
echo ""

# Ensure we are in the script's directory
cd "$(dirname "$0")" || exit 1

# Check Python 3
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}ERROR: Python 3 not found.${NC}"
        echo "Please install Python 3 from https://www.python.org/downloads"
        read -r -p "Press Enter to close..."
        exit 1
    fi
fi

echo "[1] Checking Python installation..."
$PYTHON_CMD --version

echo "[2] Checking Virtual Environment..."
if [ ! -d "venv" ]; then
    echo "[*] Creating fresh virtual environment..."
    $PYTHON_CMD -m venv venv 2>/dev/null || true
fi

if [ -f "venv/bin/activate" ]; then
    # shellcheck source=/dev/null
    source venv/bin/activate
    PYTHON_CMD="python"
fi

echo "[3] Installing dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt >/dev/null 2>&1 || true

# Free port 53317 if occupied (supports fuser and lsof)
fuser -k 53317/tcp 2>/dev/null || (command -v lsof &>/dev/null && lsof -i :53317 -t | xargs kill -9 2>/dev/null) || true

echo ""
echo "[*] Launching LightShare Dedicated Desktop GUI Window..."
echo ""

# Run desktop GUI launcher with fallback to server mode
$PYTHON_CMD desktop_app.py || $PYTHON_CMD -m app.main

echo ""
read -r -p "Press Enter to close..."