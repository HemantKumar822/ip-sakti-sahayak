@echo off
call .venv\Scripts\activate
if exist .env (
    for /f "usebackq eol=# tokens=*" %%a in (".env") do set "%%a"
)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
