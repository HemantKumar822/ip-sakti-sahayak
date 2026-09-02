"""IP-SAKTI Sahayak: Structured, Beautiful & Information-Rich Logging Engine.

Provides dual-mode formatting:
  1. Human-Centric ANSI Color Formatter for local development and live demonstrations.
  2. Structured JSON Formatter for cloud observability (Datadog, GCP, CloudWatch).
"""

import io
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

# Reconfigure stdout/stderr for UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation, ValueError):
        # Stream does not support reconfigure in restricted or non-standard environments
        pass

if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation, ValueError):
        pass

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Foreground Colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Mapping components to distinctive pill badges
COMPONENT_BADGES: dict[str, tuple[str, str]] = {
    "ip_sakti.pipeline.orchestrator": ("ORCHESTRATOR", CYAN),
    "ip_sakti.pipeline.classifier": ("CLASSIFIER", MAGENTA),
    "ip_sakti.pipeline.jurisdiction_router": ("ROUTER", YELLOW),
    "ip_sakti.pipeline.hybrid_retriever": ("HYBRID-RRF", GREEN),
    "ip_sakti.pipeline.retriever": ("RETRIEVER", GREEN),
    "ip_sakti.pipeline.bm25_retriever": ("BM25-SEARCH", GREEN),
    "ip_sakti.pipeline.confidence_gate": ("CONF-GATE", BLUE),
    "ip_sakti.pipeline.abs_tkdl_checker": ("COMPLIANCE", YELLOW),
    "ip_sakti.pipeline.answer_generator": ("GENERATOR", CYAN),
    "ip_sakti.privacy.query_logger": ("PII-GUARD", RED),
    "ip_sakti.api": ("API-GATEWAY", BLUE),
    "ip_sakti.api.routes": ("API-ROUTES", BLUE),
    "ip_sakti.vector_store.chroma": ("CHROMA-DB", MAGENTA),
}


class BeautifulConsoleFormatter(logging.Formatter):
    """Custom logging formatter rendering clean, information-rich terminal output."""

    def __init__(self, use_color: bool | None = None) -> None:
        super().__init__()
        if use_color is not None:
            self.use_color = use_color
        else:
            self.use_color = bool(
                (hasattr(sys.stdout, "isatty") and sys.stdout.isatty())
                or os.getenv("FORCE_COLOR", "0") in ("1", "true")
                or os.name == "nt"  # Modern Windows Terminal supports ANSI
            )

    def format(self, record: logging.LogRecord) -> str:
        # 1. Clean local timestamp (HH:MM:SS.mmm)
        ct = self.converter(record.created)
        t_str = time.strftime("%H:%M:%S", ct)
        msec = int(record.msecs)
        time_display = f"{t_str}.{msec:03d}"

        # 2. Level Badge
        lvl = record.levelname
        if self.use_color:
            if lvl == "INFO":
                level_badge = f"{GREEN}INFO {RESET}"
            elif lvl == "WARNING":
                level_badge = f"{YELLOW}{BOLD}WARN {RESET}"
            elif lvl in ("ERROR", "CRITICAL"):
                level_badge = f"{RED}{BOLD}FAIL {RESET}"
            else:
                level_badge = f"{DIM}DEBUG{RESET}"
        else:
            level_badge = f"{lvl:<5}"

        # 3. Component Badge
        badge_name = "SYSTEM"
        badge_color = CYAN
        for prefix, (name, color) in COMPONENT_BADGES.items():
            if record.name.startswith(prefix):
                badge_name = name
                badge_color = color
                break

        if self.use_color:
            comp_display = f"{badge_color}[{badge_name:<11}]{RESET}"
            time_formatted = f"{DIM}{time_display}{RESET}"
        else:
            comp_display = f"[{badge_name:<11}]"
            time_formatted = time_display

        # 4. Message Content
        try:
            msg = record.getMessage()
        except (TypeError, ValueError):
            msg = str(record.msg)

        # 5. Format stack trace if exception occurred
        exc_text = ""
        if record.exc_info:
            exc_text = "\n" + self.formatException(record.exc_info)

        return f"{time_formatted} {level_badge} {comp_display} {msg}{exc_text}"


class JSONLogFormatter(logging.Formatter):
    """Standard JSON line formatter for production and cloud log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "file": record.filename,
            "line": record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(
    level: str | int | None = None,
    log_format: str | None = None,
) -> None:
    """Configures project-wide structured logging.

    Args:
        level: Minimum log level (defaults to LOG_LEVEL env var or INFO).
        log_format: 'console' or 'json' (defaults to LOG_FORMAT env var or 'console').
    """
    if level is None:
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, level_str, logging.INFO)
    elif isinstance(level, str):
        log_level = getattr(logging, level.upper(), logging.INFO)
    else:
        log_level = level

    if log_format is None:
        log_format = os.getenv("LOG_FORMAT", "console").lower()

    # Determine Formatter
    if log_format == "json":
        formatter = JSONLogFormatter()
    else:
        formatter = BeautifulConsoleFormatter()

    # Configure root and ip_sakti loggers
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clean existing handlers to prevent duplicate lines
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Suppress verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
