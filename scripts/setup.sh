#!/bin/bash
echo "Setting up local development environment for IP-SAKTI Sahayak..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 could not be found. Please install Python 3.11+"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip and install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup .env file
if [ ! -f ".env" ]; then
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "Please open .env and add your GEMINI_API_KEY."
fi

echo "Setup complete! You can now run the system using run_api.sh and run_frontend.sh"
