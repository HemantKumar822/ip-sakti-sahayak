import json
import logging

from src.utils.logger import BeautifulConsoleFormatter, JSONLogFormatter, setup_logging


def test_beautiful_console_formatter_levels_and_components():
    formatter = BeautifulConsoleFormatter(use_color=False)
    record = logging.LogRecord(
        name="ip_sakti.pipeline.orchestrator",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Processing query %s",
        args=("Triphala",),
        exc_info=None,
    )
    output = formatter.format(record)
    assert "INFO" in output
    assert "[ORCHESTRATOR" in output
    assert "Processing query Triphala" in output


def test_beautiful_console_formatter_warning_and_error():
    formatter = BeautifulConsoleFormatter(use_color=True)
    rec_warn = logging.LogRecord(
        name="ip_sakti.pipeline.classifier",
        level=logging.WARNING,
        pathname=__file__,
        lineno=20,
        msg="Fallback heuristic",
        args=(),
        exc_info=None,
    )
    rec_err = logging.LogRecord(
        name="ip_sakti.privacy.query_logger",
        level=logging.ERROR,
        pathname=__file__,
        lineno=30,
        msg="Audit failed",
        args=(),
        exc_info=None,
    )
    out_warn = formatter.format(rec_warn)
    out_err = formatter.format(rec_err)

    assert "WARN" in out_warn
    assert "CLASSIFIER" in out_warn
    assert "FAIL" in out_err
    assert "PII-GUARD" in out_err


def test_json_log_formatter():
    formatter = JSONLogFormatter()
    record = logging.LogRecord(
        name="ip_sakti.api",
        level=logging.INFO,
        pathname=__file__,
        lineno=45,
        msg="Server started on port %d",
        args=(8000,),
        exc_info=None,
    )
    out = formatter.format(record)
    data = json.loads(out)

    assert data["level"] == "INFO"
    assert data["logger"] == "ip_sakti.api"
    assert data["message"] == "Server started on port 8000"
    assert "timestamp" in data


def test_setup_logging_console_and_json():
    setup_logging(level="DEBUG", log_format="console")
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert isinstance(root.handlers[0].formatter, BeautifulConsoleFormatter)

    setup_logging(level=logging.INFO, log_format="json")
    assert root.level == logging.INFO
    assert isinstance(root.handlers[0].formatter, JSONLogFormatter)

    # Reset back to console info for subsequent tests
    setup_logging(level="INFO", log_format="console")
