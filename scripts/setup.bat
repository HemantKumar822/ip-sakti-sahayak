@echo off
echo Setting up local development environment for IP-SAKTI Sahayak...

:: Check if python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python could not be found. Please install Python 3.11+ and add it to PATH.
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate virtual environment
call .venv\Scripts\activate

:: Upgrade pip and install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

:: Setup .env file
if not exist ".env" (
    echo Copying .env.example to .env...
    copy .env.example .env
    echo Please open .env and add your GEMINI_API_KEY.
)

echo Setup complete! You can now run the system using run_api.bat and run_frontend.bat
