@echo off
REM ==============================================================================
REM IP-SAKTI Sahayak: One-Click Startup Script (Windows)
REM Starts both FastAPI Backend & React Legal Workbench concurrently
REM ==============================================================================

cd /d "%~dp0"

IF EXIST ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py %*
) ELSE (
    python run.py %*
)
