#!/bin/bash
if [ -f .venv/Scripts/activate ]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi
if [ -f .env ]; then
    set -a
    source .env 2>/dev/null || true
    set +a
fi
streamlit run src/frontend/app.py --server.port 8501 --server.address 0.0.0.0
