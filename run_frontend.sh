#!/bin/bash
source .venv/bin/activate
if [ -f .env ]; then
    set -a
    source .env 2>/dev/null || true
    set +a
fi
streamlit run src/frontend/app.py
