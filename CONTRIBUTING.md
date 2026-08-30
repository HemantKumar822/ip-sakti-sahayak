# Contributing to IP-SAKTI Sahayak

Welcome to the team! This guide explains how to get the project running locally and how we collaborate.

## Local Development Setup (No Docker)

We use a standard Python virtual environment (`.venv`). Follow these steps to set up the project on your machine.

### 1. Prerequisites
- **Python 3.11 or higher** installed and added to your system `PATH`.
- Git installed.

### 2. Clone the Repository & Checkout `develop`
> [!IMPORTANT]
> Ensure your current directory is **completely empty** before running this command. If there are hidden files, Git will throw an error `fatal: destination path '.' already exists and is not an empty directory.`

```bash
git clone -b develop https://github.com/HemantKumar822/ip-sakti-sahayak.git .
```

### 3. Initialization (One-Time Setup)

#### Windows
Run the setup batch script from the root of the repository:
```cmd
scripts\setup.bat
```

#### Mac / Linux
Make the scripts executable and run the setup script:
```bash
chmod +x scripts/*.sh *.sh
./scripts/setup.sh
```

This script will automatically:
1. Create a Python virtual environment (`.venv`).
2. Install all required dependencies (from `requirements.txt` and `requirements-dev.txt`).
3. Copy `.env.example` to `.env`.

### 3. Add Your Secrets
Open the newly created `.env` file and add your `GEMINI_API_KEY`. (If you don't have one, get it free from Google AI Studio).

### 4. Running the System

You need to run the API and the Frontend in two separate terminal windows. You do not need to activate the virtual environment manually—the run scripts handle it for you.

**Terminal 1: Run the Backend API**
- **Windows:** `run_api.bat`
- **Mac/Linux:** `./run_api.sh`

*(The API will be available at `http://localhost:8000`)*

**Terminal 2: Run the Frontend**
- **Windows:** `run_frontend.bat`
- **Mac/Linux:** `./run_frontend.sh`

*(The Streamlit UI will open automatically at `http://localhost:8501`)*

### 5. Running Tests & Coverage
To run the automated test suite with coverage reporting:
- **Windows:** `run_tests.bat`
- **Mac/Linux:** `./run_tests.sh`

Or run directly with `pytest`:
```bash
# Run tests with terminal coverage summary (enforces >=70% threshold):
pytest tests/ --cov=src --cov-report=term-missing

# Generate detailed HTML coverage report (opens htmlcov/index.html):
pytest --cov=src --cov-report=html
```

### 6. Code Formatting & Linting
Our GitHub Actions CI checks strictly enforce `ruff` and `black` on every Pull Request.
Before committing and pushing your code, run:

```bash
# Auto-fix linting & import issues:
python -m ruff check --fix src/ tests/

# Auto-format all files to PEP 8 standards:
python -m black src/ tests/

# Verify that all checks pass:
python -m ruff check src/ tests/
python -m black --check src/ tests/
```

### 7. Pre-commit Hooks Setup
We use `pre-commit` to automatically run code formatters, linters, secret detection, and syntax checks before each commit.
```bash
# Install and register pre-commit hooks:
pip install pre-commit
pre-commit install

# Manually run all hooks across the codebase:
pre-commit run --all-files
```

---

## Common Errors & Fixes

### ❌ `uvicorn is not recognized as an internal or external command`
- **Cause:** The virtual environment is not activated, or dependencies failed to install.
- **Fix:** Run the `setup.bat` or `setup.sh` script again, and make sure there are no red error messages during `pip install`. Make sure you use the run scripts (e.g. `run_api.bat`) instead of typing `uvicorn` directly.

### ❌ `KeyError: 'GEMINI_API_KEY'`
- **Cause:** You forgot to add your API key, or the `.env` file doesn't exist.
- **Fix:** Ensure you have an `.env` file in the root folder, and that `GEMINI_API_KEY=your_key_here` is inside it.

### ❌ `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'chroma.sqlite3'`
- **Cause:** ChromaDB vector store is locked by another running process (FastAPI or a test runner).
- **Fix:** Close all terminal windows running the API, then start it again. If it persists, use Task Manager to kill lingering `python.exe` processes.

### ❌ `bash: ./run_api.sh: Permission denied`
- **Cause:** (Mac/Linux only) The script doesn't have execute permissions.
- **Fix:** Run `chmod +x *.sh scripts/*.sh`

### ❌ `Lint / lint (pull_request) failed on GitHub`
- **Cause:** Unsorted imports, missing blank lines (PEP 8), or deprecated typing annotations (`typing.List` vs `list`).
- **Fix:** Run `python -m ruff check --fix src/ tests/` and `python -m black src/ tests/` locally, commit, and push.

---

## Git Workflow

We use a feature-branch workflow.

1. **Never commit directly to `main` or `develop`.**
2. Always create a branch for your issue:
   `git checkout -b feature/<issue-number>-<short-description>`
3. Make your changes and write unit tests.
4. Run tests and linters locally:
   ```bash
   run_tests.bat # or ./run_tests.sh
   python -m ruff check src/ tests/
   python -m black --check src/ tests/
   ```
5. Commit and push your branch:
   `git push origin feature/<issue-number>-<short-description>`
6. Open a **Pull Request (PR)** on GitHub targeting the `develop` branch.
7. In your PR description, write `Closes #<issue-number>` so GitHub links and closes the issue when merged.
8. Wait for CI checks (Lint & Tests) to pass and at least **1 approving review** from a teammate before merging.
