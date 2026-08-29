@echo off
call .venv\Scripts\activate
for /f "tokens=*" %%a in (.env) do set %%a
streamlit run src\frontend\app.py
