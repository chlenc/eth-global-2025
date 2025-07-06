#!/bin/bash

# Exit immediately on error
set -e

echo "🔄 Removing old virtual environments..."
rm -rf .venv venv

echo "🐍 Creating new virtual environment in .venv..."
python3 -m venv .venv

echo "✅ Activating virtual environment..."
source .venv/bin/activate

echo "📦 Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup complete. Virtual environment is ready!"
