@echo off
call .venv\Scripts\activate
if exist .env (
    for /f "usebackq eol=# tokens=*" %%a in (".env") do set "%%a"
)
streamlit run src\frontend\app.py
