#!/bin/bash
# Activation script for LED strip light project

echo "🔧 Activating LED Strip Light Controller environment..."
source "$(dirname "$0")/../.venv/bin/activate"
echo "✅ Virtual environment activated"
echo "📁 Project: LED Strip Light Controller"
echo "🐍 Python: $(python --version)"
echo "📦 Pip packages: $(pip list --format=freeze | wc -l) installed"
echo ""
echo "Available commands:"
echo "  ./run.py breathing --color red"
echo "  pytest"
echo "  pytest --cov=led"
echo ""
