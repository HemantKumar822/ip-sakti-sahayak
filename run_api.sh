#!/bin/bash
source .venv/bin/activate
if [ -f .env ]; then
    set -a
    source .env 2>/dev/null || true
    set +a
fi
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
