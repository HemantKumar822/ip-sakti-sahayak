@echo off
call .venv\Scripts\activate
if exist .env (
    for /f "usebackq eol=# tokens=*" %%a in (".env") do set "%%a"
)
pytest --cov=src tests\
