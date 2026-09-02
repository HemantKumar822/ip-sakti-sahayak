#!/usr/bin/env bash
# ==============================================================================
# IP-SAKTI Sahayak: One-Click Startup Script (Linux / macOS)
# Starts both FastAPI Backend & Streamlit Legal Workbench concurrently
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

if [ -f ".venv/bin/python" ]; then
    .venv/bin/python run.py "$@"
else
    python3 run.py "$@"
fi
