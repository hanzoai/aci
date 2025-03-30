#!/bin/bash

# Run ACI Tests
# This script runs all tests for the Hanzo ACI package

set -e  # Exit on error

echo "=== Running Hanzo ACI Tests ==="
echo

# Make sure pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest not found. Installing..."
    pip install pytest pytest-asyncio
fi

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Run the tests
echo "Running tests..."
pytest -xvs tests/

# Check test results
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed!"
    exit 1
fi

echo
echo "=== Test Run Complete ==="
