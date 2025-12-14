#!/bin/bash
# Test entry point script
# Runs backend tests with coverage

set -e

echo "Running backend tests..."
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "backend/.venv" ]; then
    source backend/.venv/bin/activate
fi

# Run pytest with coverage
python3 -m pytest backend/tests/ -v --cov=backend/src --cov-report=term-missing

echo ""
echo "Tests completed successfully!"

