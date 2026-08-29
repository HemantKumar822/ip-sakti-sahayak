@echo off
call .venv\Scripts\activate
for /f "tokens=*" %%a in (.env) do set %%a
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
