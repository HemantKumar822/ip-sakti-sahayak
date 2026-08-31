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
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
