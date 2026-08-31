import datetime
import json
import logging
import re
import sys
import uuid
from typing import Any

from src.config import config

logger = logging.getLogger("ip_sakti.privacy.query_logger")

# Regex patterns for Personally Identifiable Information (PII)
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Indian Phone Numbers: 10 digits starting with 6-9, with optional +91, 91, or 0 prefix
PHONE_PATTERN = re.compile(
    r"(?:(?:\+91|91|0)[-\s]?)?[6-9]\d{4}[-\s]?\d{5}\b|\b(?:(?:\+91|91|0)[-\s]?)?[6-9]\d{9}\b"
)

# Aadhaar: 12-digit Indian national identity number (formatted 4-4-4 with spaces/hyphens or 12 continuous digits)
AADHAAR_PATTERN = re.compile(r"\b(?:\d{4}[-\s]\d{4}[-\s]\d{4}|\d{12})\b")

# Name patterns: "My name is X", "I am X", "I'm X", "Name is X"
NAME_INTRO_PATTERN = re.compile(
    r"(?i)\b(my name is|i am|i\'m|name is|name:)\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,3})(?=\s+(?:and|or|who|which|from|want|need|have|is|can|could|would|seeking|asking|filing|\b)|[.,;!?]|$)"
)

# Salutation Name patterns: "Dr. Ramesh Sharma", "Shri Amit Kumar", etc.
NAME_SALUTATION_PATTERN = re.compile(
    r"\b(?:Dr\.|Mr\.|Mrs\.|Ms\.|Shri|Smt\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
)


def strip_pii(text: str) -> str:
    """Strips Personally Identifiable Information (PII) from query text.

    Complies with India's DPDP Act 2023 by redacting:
    - Email addresses -> [REDACTED_EMAIL]
    - Indian 10-digit phone numbers -> [REDACTED_PHONE]
    - Aadhaar numbers (12 digits) -> [REDACTED_AADHAAR]
    - Self-identified names ("My name is X", "I am X") -> [REDACTED_NAME]

    Args:
        text: Raw user query or text.

    Returns:
        Cleaned text with all detected PII redacted.
    """
    if not text:
        return text

    cleaned = text

    # 1. Redact Emails
    cleaned = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", cleaned)

    # 2. Redact Indian Phone Numbers (run before continuous Aadhaar so 91+10 digits is recognized as phone)
    cleaned = PHONE_PATTERN.sub("[REDACTED_PHONE]", cleaned)

    # 3. Redact Aadhaar numbers (12 digits)
    cleaned = AADHAAR_PATTERN.sub("[REDACTED_AADHAAR]", cleaned)

    # 4. Redact Introduced Names ("My name is John Doe" -> "My name is [REDACTED_NAME]")
    cleaned = NAME_INTRO_PATTERN.sub(r"\1 [REDACTED_NAME]", cleaned)

    # 5. Redact Salutation Names ("Dr. Ramesh" -> "[REDACTED_NAME]")
    cleaned = NAME_SALUTATION_PATTERN.sub("[REDACTED_NAME]", cleaned)

    return cleaned


def log_query(
    session_id: str | None,
    query_text: str,
    category: str | None = None,
    retrieved_doc_ids: list[str] | None = None,
    confidence_score: float | None = None,
    decision: str = "generate",
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Logs a query event to stdout as structured JSON after stripping PII.

    Args:
        session_id: Session identifier (anonymous UUID generated if None).
        query_text: User query string.
        category: Classified product category.
        retrieved_doc_ids: List of retrieved document IDs.
        confidence_score: Confidence gate or retrieval score.
        decision: Pipeline decision ('generate' or 'abstain').
        timestamp: ISO 8601 UTC timestamp (current time generated if None).

    Returns:
        Structured dictionary of the emitted log entry.
    """
    pii_enabled = getattr(config, "PII_STRIP_ENABLED", True)
    clean_query = strip_pii(query_text) if pii_enabled else query_text

    effective_session_id = session_id or f"anon-{uuid.uuid4()}"
    effective_timestamp = (
        timestamp
        if timestamp is not None
        else datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    log_entry: dict[str, Any] = {
        "session_id": effective_session_id,
        "query_text": clean_query,
        "category": category,
        "retrieved_doc_ids": retrieved_doc_ids or [],
        "confidence_score": confidence_score,
        "decision": decision,
        "timestamp": effective_timestamp,
    }

    # Format JSON and output to stdout for audit logging
    log_json = json.dumps(log_entry)
    sys.stdout.write(f"{log_json}\n")
    sys.stdout.flush()

    logger.info(
        "Query audit log recorded: session=%s decision=%s",
        effective_session_id,
        decision,
    )
    return log_entry
