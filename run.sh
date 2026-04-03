#!/bin/bash
set -e

cd "$(dirname "$0")"

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --quiet fiftyone twelvelabs python-dotenv

# Verify Twelve Labs connection
echo "Testing Twelve Labs API..."
python test_twelvelabs.py

# Register the plugin with FiftyOne
echo "Registering PitLane AI plugin..."
fiftyone plugins dev .

# Load dataset and launch app
echo "Loading dataset and launching FiftyOne..."
python dataset.py
