#!/bin/bash
source .venv/bin/activate
export $(cat .env | xargs)
pytest --cov=src tests/
