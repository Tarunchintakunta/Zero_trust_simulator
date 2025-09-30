#!/bin/bash

# Run ZTA experiment with default config
# Usage: ./run_experiment.sh [config_file]

set -e  # Exit on error

# Default config file
CONFIG_FILE=${1:-configs/sample_experiment.json}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if ! pip show zta-sim &>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    pip install -e .
fi

# Run experiment
echo "Running experiment with config: $CONFIG_FILE"
python -m src.sim.experiment --config "$CONFIG_FILE"

# Generate analysis if available
if [ -f "analysis/scripts/analyze_results.py" ]; then
    echo "Generating analysis..."
    python -m analysis.scripts.analyze_results
fi

echo "Experiment completed!"
