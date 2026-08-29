#!/bin/bash
source .venv/bin/activate
export $(cat .env | xargs)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
