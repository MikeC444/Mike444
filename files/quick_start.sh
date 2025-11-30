#!/bin/bash

# GVI Tracker Quick Start Script
# ================================

echo "================================================"
echo "GVI Stock Decile Movement Tracker - Quick Start"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

echo "✓ pip3 found"
echo ""

# Install requirements
echo "📦 Installing required packages..."
pip3 install -r requirements.txt --quiet

if [ $? -eq 0 ]; then
    echo "✓ All packages installed successfully"
else
    echo "❌ Failed to install packages. Please check requirements.txt"
    exit 1
fi

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "You can now:"
echo ""
echo "1. Launch the interactive dashboard:"
echo "   streamlit run gvi_dashboard.py"
echo ""
echo "2. Use the command-line interface:"
echo "   python gvi_cli.py --help"
echo ""
echo "3. Upload your first data files:"
echo "   python gvi_cli.py upload --file your_file.xlsx --date 2025-03-11"
echo ""
echo "See README.md for complete documentation."
echo ""
