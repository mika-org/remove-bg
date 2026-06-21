#!/bin/bash

# Exit on error
set -e

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo "Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Pre-download the model
echo "Checking/pre-downloading the U-2-Net model..."
python download_model.py

# Start FastAPI using Uvicorn with production configuration (2 workers)
echo "Starting FastAPI server on port 8000..."
exec uvicorn api.index:app --host 0.0.0.0 --port 8000 --workers 2
