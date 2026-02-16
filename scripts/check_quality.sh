#!/bin/bash
set -e

# Change to project root
cd "$(dirname "$0")/.."

if [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Activating virtual environment..."
    source .venv/bin/activate
fi

python scripts/utils/check_quality.py

