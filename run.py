#!/usr/bin/env python3
"""IP-SAKTI Sahayak: Unified Application Orchestrator & Launcher.

Single command to manage local development, testing, ingestion, and production runs:
    python run.py            -> Start both FastAPI Backend & React Workbench
    python run.py --api      -> Start FastAPI Backend only (port 8000)
    python run.py --ui       -> Start React Workbench only (port 5173)
    python run.py --test     -> Run pytest regression test suite
    python run.py --bench    -> Run 20-query Golden Set evaluation benchmark
    python run.py --ingest   -> Run statutory corpus ingestion into ChromaDB
    python run.py --provider-check -> Smoke-check the configured LLM provider
"""

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# ANSI Terminal Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

BANNER = f"""{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════════════╗
║                     🏛️  IP-SAKTI SAHAYAK v2.0                        ║
║     Citation-Grounded AI Legal Workbench for Ayurveda & ABS Laws    ║
╚══════════════════════════════════════════════════════════════════════╝{RESET}
"""


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks whether a local TCP port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def _parse_env_file(path: Path) -> dict:
    """Parses KEY=VALUE lines from a dotenv file, ignoring comments."""
    values = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            values[key.strip()] = value.strip().strip("\"'")
    except OSError:
        pass
    return values


def ensure_environment() -> None:
    """Checks for backend and frontend .env files, creating them from examples if missing."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    if not env_file.exists() and env_example.exists():
        print(
            f"{YELLOW}[!] .env file not found. Initializing from .env.example...{RESET}"
        )
        shutil.copy(env_example, env_file)
        print(
            f"{GREEN}[✓] Created .env file. Please add your GEMINI_API_KEY if needed.{RESET}"
        )
    ensure_frontend_env()
    check_key_parity()


def ensure_frontend_env() -> None:
    """Creates src/web/.env from src/web/.env.example when missing (Vite API key wiring)."""
    web_env = Path("src/web/.env")
    web_example = Path("src/web/.env.example")
    if not web_env.exists() and web_example.exists():
        print(
            f"{YELLOW}[!] src/web/.env not found. Initializing from .env.example...{RESET}"
        )
        shutil.copy(web_example, web_env)
        print(f"{GREEN}[OK] Created src/web/.env with dev API key.{RESET}")


def check_key_parity() -> None:
    """Warns when frontend and backend dev keys disagree (the #1 admin-access failure)."""
    backend_keys = _parse_env_file(Path(".env")).get("VALID_API_KEYS", "")
    backend_admins = _parse_env_file(Path(".env")).get("VALID_ADMIN_API_KEYS", "")
    frontend_key = _parse_env_file(Path("src/web/.env")).get("VITE_API_KEY", "")
    if not frontend_key:
        print(
            f"{YELLOW}[!] src/web/.env has no VITE_API_KEY — queries and admin will return 401.{RESET}"
        )
        return
    if backend_keys and frontend_key not in [
        k.strip() for k in backend_keys.split(",")
    ]:
        print(
            f"{YELLOW}[!] VITE_API_KEY does not match backend VALID_API_KEYS — expect 401s.{RESET}"
        )
    elif backend_admins and frontend_key not in [
        k.strip() for k in backend_admins.split(",")
    ]:
        print(
            f"{YELLOW}[!] VITE_API_KEY lacks admin rights (not in VALID_ADMIN_API_KEYS) — corpus console will be restricted.{RESET}"
        )
    else:
        print(f"{GREEN}[OK] API key parity OK (query + admin).{RESET}")


def run_provider_check() -> int:
    """Smoke-checks the configured LLM provider with a minimal generation call."""
    print(f"\n{CYAN}{BOLD}[*] Checking LLM provider wiring...{RESET}\n")
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    script = (
        "from src.config import config;"
        "from src.pipeline.providers import get_llm_client;"
        "client = get_llm_client();"
        "print('provider:', type(client).__name__);"
        "print('model:', getattr(client, 'model_name', '?'));"
        "print('base_url:', getattr(client, 'base_url', '(sdk default)'));"
        "out = client.generate_text('Reply with exactly: provider-ok');"
        "print('response:', out[:200]);"
        "assert out.strip(), 'empty response from provider';"
        "print('PROVIDER-OK')"
    )
    cmd = [sys.executable, "-c", script]
    return subprocess.call(cmd, env=env)


def run_tests() -> int:
    """Runs pytest regression suite."""
    print(f"\n{CYAN}{BOLD}[*] Executing IP-SAKTI Test Suite with Coverage...{RESET}\n")
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
    return subprocess.call(cmd)


def run_benchmark() -> int:
    """Runs 20-query Golden Set evaluation."""
    print(
        f"\n{CYAN}{BOLD}[*] Executing Golden Set Benchmark (20 standardized queries)...{RESET}\n"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    cmd = [sys.executable, "scripts/evaluate_golden_set.py"]
    return subprocess.call(cmd, env=env)


def run_ingest() -> int:
    """Runs vector corpus ingestion into ChromaDB."""
    print(
        f"\n{CYAN}{BOLD}[*] Ingesting Authentic Statutory Corpus into ChromaDB...{RESET}\n"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    cmd = [sys.executable, "scripts/ingest_corpus.py"]
    return subprocess.call(cmd, env=env)


def start_backend() -> subprocess.Popen:
    """Spawns the FastAPI backend server process."""
    if is_port_in_use(8000):
        print(
            f"{YELLOW}[!] Port 8000 is already in use. Assuming backend is already running.{RESET}"
        )
        return None

    print(f"{CYAN}[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...{RESET}")
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--log-level",
        "warning",
    ]
    proc = subprocess.Popen(cmd, env=env)
    return proc


def wait_for_backend(timeout: float = 12.0) -> bool:
    """Polls the backend /health endpoint until it responds with HTTP 200."""
    import urllib.error
    import urllib.request

    start_time = time.time()
    url = "http://127.0.0.1:8000/health"
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.getcode() == 200:
                    print(f"{GREEN}[✓] FastAPI Backend is ONLINE & Healthy.{RESET}")
                    return True
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            time.sleep(0.4)
    print(
        f"{YELLOW}[!] Backend did not respond within {timeout}s (will proceed anyway).{RESET}"
    )
    return False


def start_frontend() -> subprocess.Popen:
    """Spawns the React (Vite) workbench frontend process."""
    print(f"{CYAN}[2/2] Launching React Web App on http://localhost:5173 ...{RESET}")
    env = os.environ.copy()
    npm_bin = shutil.which("npm") or ("npm.cmd" if sys.platform == "win32" else "npm")
    cmd = [npm_bin, "run", "dev"]
    proc = subprocess.Popen(
        cmd, env=env, cwd="src/web", shell=(sys.platform == "win32")
    )
    return proc


def start_full_stack() -> None:
    """Starts both FastAPI backend and React UI with unified process lifecycle management."""
    print(BANNER)
    ensure_environment()

    backend_proc = start_backend()
    if backend_proc is not None:
        wait_for_backend()

    frontend_proc = start_frontend()

    print(f"\n{GREEN}{BOLD}{'═' * 70}{RESET}")
    print(f"{GREEN}{BOLD}  🚀 IP-SAKTI Sahayak Legal Workbench is Running!{RESET}")
    print(f"{DIM}  • Interactive Workbench UI:  {BOLD}http://localhost:5173{RESET}")
    print(f"{DIM}  • Backend REST API:         {BOLD}http://localhost:8000{RESET}")
    print(
        f"{DIM}  • Interactive Swagger Docs:  {BOLD}http://localhost:8000/docs{RESET}"
    )
    print(f"{GREEN}{BOLD}{'═' * 70}{RESET}")
    print(f"{YELLOW}Press Ctrl+C at any time to gracefully stop all services.{RESET}\n")

    time.sleep(2.5)
    try:
        webbrowser.open("http://localhost:5173")
    except Exception:
        pass

    # Monitor and handle Ctrl+C termination cleanly
    def cleanup_signal(sig, frame):
        print(f"\n{YELLOW}[*] Shutting down IP-SAKTI services cleanly...{RESET}")
        if frontend_proc and frontend_proc.poll() is None:
            frontend_proc.terminate()
        if backend_proc and backend_proc.poll() is None:
            backend_proc.terminate()
        print(f"{GREEN}[✓] Shutdown complete. Goodbye!{RESET}")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, cleanup_signal)

    try:
        while True:
            time.sleep(1)
            # If both processes exited, terminate runner
            if (backend_proc and backend_proc.poll() is not None) and (
                frontend_proc and frontend_proc.poll() is not None
            ):
                break
    except KeyboardInterrupt:
        cleanup_signal(None, None)


def main() -> None:
    """Main entrypoint routing command line arguments."""
    parser = argparse.ArgumentParser(
        description="IP-SAKTI Sahayak Unified Runner",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--api", action="store_true", help="Start only the FastAPI backend (port 8000)"
    )
    parser.add_argument(
        "--ui", action="store_true", help="Start only the React workbench (port 5173)"
    )
    parser.add_argument(
        "--test", action="store_true", help="Run pytest regression test suite"
    )
    parser.add_argument(
        "--bench",
        action="store_true",
        help="Run 20-query Golden Set evaluation benchmark",
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Run statutory corpus ingestion into ChromaDB",
    )
    parser.add_argument(
        "--provider-check",
        action="store_true",
        help="Smoke-check the configured LLM provider (LLM_PROVIDER) end to end",
    )

    args = parser.parse_args()

    if args.test:
        sys.exit(run_tests())
    elif args.provider_check:
        ensure_environment()
        sys.exit(run_provider_check())
    elif args.bench:
        sys.exit(run_benchmark())
    elif args.ingest:
        sys.exit(run_ingest())
    elif args.api:
        ensure_environment()
        p = start_backend()
        if p:
            try:
                p.wait()
            except KeyboardInterrupt:
                p.terminate()
    elif args.ui:
        ensure_environment()
        p = start_frontend()
        try:
            p.wait()
        except KeyboardInterrupt:
            p.terminate()
    else:
        start_full_stack()


if __name__ == "__main__":
    main()
