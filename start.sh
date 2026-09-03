#!/usr/bin/env bash
# ==============================================================================
# IP-SAKTI Sahayak: One-Click Startup Script (Git Bash / Linux / macOS)
# Starts both FastAPI Backend & React Legal Workbench concurrently
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

if [ -f ".venv/Scripts/python.exe" ]; then
    .venv/Scripts/python.exe run.py "$@"
elif [ -f ".venv/bin/python" ]; then
    .venv/bin/python run.py "$@"
elif command -v python &>/dev/null; then
    python run.py "$@"
else
    python3 run.py "$@"
fi
