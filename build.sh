#!/bin/bash
# build.sh - Build swb binary with PyInstaller

set -e

echo "Building swb CLI..."

# Clean previous builds
rm -rf build/ dist/

# Create virtual environment if needed
if [ ! -d "venv" ] || [ ! -f "venv/bin/pip" ]; then
    echo "Creating virtual environment..."
    rm -rf venv
    python3 -m venv venv

    if [ ! -f "venv/bin/pip" ]; then
        echo "Error: Failed to create virtual environment"
        echo "Please ensure python3-venv is installed: sudo apt install python3-venv"
        exit 1
    fi
fi

# Install dependencies
echo "Installing dependencies..."
./venv/bin/pip install -q -r requirements.txt
./venv/bin/pip install -q -e .

# Run tests
echo "Running tests..."
./venv/bin/pytest tests/ -v

# Run PyInstaller
echo "Running PyInstaller..."
./venv/bin/pyinstaller swb.spec

echo ""
echo "Build complete!"
echo "Binary location: dist/swb"
echo ""
echo "Test with: ./dist/swb --help"
