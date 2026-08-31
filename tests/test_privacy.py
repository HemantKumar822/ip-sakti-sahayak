import json

from src.config import config
from src.privacy.pii_strip import log_query, strip_pii


def test_strip_pii_email():
    text = "Please contact me at test.user+ayurveda@example.com for further questions."
    cleaned = strip_pii(text)
    assert "[REDACTED_EMAIL]" in cleaned
    assert "test.user+ayurveda@example.com" not in cleaned


def test_strip_pii_phone_indian_standard():
    text = "You can call me on 9876543210 regarding the formulation."
    cleaned = strip_pii(text)
    assert "[REDACTED_PHONE]" in cleaned
    assert "9876543210" not in cleaned


def test_strip_pii_phone_with_country_code():
    variants = [
        "Call +91 9876543210 for info",
        "Call +91-9876543210 for info",
        "Call 09876543210 for info",
        "Call 919876543210 for info",
    ]
    for variant in variants:
        cleaned = strip_pii(variant)
        assert "[REDACTED_PHONE]" in cleaned
        assert "9876543210" not in cleaned


def test_strip_pii_aadhaar():
    text_spaced = "My Aadhaar number is 1234 5678 9012."
    cleaned_spaced = strip_pii(text_spaced)
    assert "[REDACTED_AADHAAR]" in cleaned_spaced
    assert "1234 5678 9012" not in cleaned_spaced

    text_continuous = "Aadhaar: 123456789012"
    cleaned_continuous = strip_pii(text_continuous)
    assert "[REDACTED_AADHAAR]" in cleaned_continuous
    assert "123456789012" not in cleaned_continuous


def test_strip_pii_name_intro():
    text = "My name is Rajesh Sharma and I want to patent my herbal tea formulation."
    cleaned = strip_pii(text)
    assert "My name is [REDACTED_NAME]" in cleaned
    assert "Rajesh Sharma" not in cleaned

    text2 = "I am Suresh Patel, asking about Section 3(p)."
    cleaned2 = strip_pii(text2)
    assert "I am [REDACTED_NAME]" in cleaned2
    assert "Suresh Patel" not in cleaned2


def test_strip_pii_salutation_name():
    text = "Dr. Ramesh Sharma developed this new composition."
    cleaned = strip_pii(text)
    assert "[REDACTED_NAME]" in cleaned
    assert "Ramesh Sharma" not in cleaned


def test_strip_pii_empty_or_clean_text():
    assert strip_pii("") == ""
    clean = "Can I patent a classical Triphala formulation in India?"
    assert strip_pii(clean) == clean


def test_log_query_structure_and_stdout(capsys):
    raw_query = "My name is John Doe, email me at john@example.com or call 9876543210 about turmeric."
    log_entry = log_query(
        session_id="custom-session-uuid-1",
        query_text=raw_query,
        category="Classical Ayurveda",
        retrieved_doc_ids=["patents-act-1970", "tkdl-neem-turmeric-prior-art"],
        confidence_score=0.88,
        decision="generate",
        timestamp="2026-09-01T00:00:00Z",
    )

    # Validate returned structure
    assert log_entry["session_id"] == "custom-session-uuid-1"
    assert log_entry["category"] == "Classical Ayurveda"
    assert log_entry["retrieved_doc_ids"] == [
        "patents-act-1970",
        "tkdl-neem-turmeric-prior-art",
    ]
    assert log_entry["confidence_score"] == 0.88
    assert log_entry["decision"] == "generate"
    assert log_entry["timestamp"] == "2026-09-01T00:00:00Z"
    assert "[REDACTED_NAME]" in log_entry["query_text"]
    assert "[REDACTED_EMAIL]" in log_entry["query_text"]
    assert "[REDACTED_PHONE]" in log_entry["query_text"]
    assert "john@example.com" not in log_entry["query_text"]
    assert "9876543210" not in log_entry["query_text"]

    # Validate stdout capture
    captured = capsys.readouterr()
    assert "john@example.com" not in captured.out
    assert "9876543210" not in captured.out
    parsed_json = json.loads(captured.out.strip().split("\n")[-1])
    assert parsed_json["session_id"] == "custom-session-uuid-1"
    assert parsed_json["decision"] == "generate"


def test_log_query_default_session_and_timestamp(capsys):
    log_entry = log_query(
        session_id=None,
        query_text="What is Section 3(p)?",
        category=None,
        retrieved_doc_ids=None,
        confidence_score=None,
        decision="abstain",
        timestamp=None,
    )

    assert log_entry["session_id"].startswith("anon-")
    assert "T" in log_entry["timestamp"]  # Valid ISO timestamp
    assert log_entry["retrieved_doc_ids"] == []
    assert log_entry["decision"] == "abstain"

    captured = capsys.readouterr()
    parsed_json = json.loads(captured.out.strip().split("\n")[-1])
    assert parsed_json["session_id"] == log_entry["session_id"]


def test_log_query_pii_disabled(monkeypatch):
    monkeypatch.setattr(config, "PII_STRIP_ENABLED", False)
    raw_query = "Contact test@example.com"
    log_entry = log_query(
        session_id="anon-123",
        query_text=raw_query,
        category=None,
        retrieved_doc_ids=[],
        confidence_score=0.5,
        decision="abstain",
    )
    assert log_entry["query_text"] == raw_query
