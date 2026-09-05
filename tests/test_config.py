from pathlib import Path

import pytest

from src.config import Config, config


def test_config_instance():
    assert isinstance(config, Config)
    assert config.APP_HOST in ("0.0.0.0", "127.0.0.1")
    assert config.API_HOST in ("0.0.0.0", "127.0.0.1")
    assert config.APP_PORT == 8000
    assert config.API_PORT == 8000
    assert config.CHROMA_COLLECTION_NAME in ("ip_sakti_corpus", "ip_sakti_docs")
    assert config.VECTOR_DB_COLLECTION_NAME in ("ip_sakti_corpus", "ip_sakti_docs")
    assert config.EMBEDDING_MODEL == "BAAI/bge-small-en-v1.5"
    assert config.CONFIDENCE_THRESHOLD == 0.65
    assert config.RETRIEVAL_TOP_K == 5
    assert config.CORPUS_RAW_DIR == "./corpus/raw"
    assert config.CORPUS_MANIFEST_PATH == "./corpus/manifest.json"
    assert config.DEFAULT_JURISDICTION == "India"
    assert config.ABS_THRESHOLD == 0.55
    assert config.GEMINI_MODEL in (
        "gemini-1.5-flash",
        "gemini-2.5-flash",
        "gemini-3.5-flash",
    )
    assert config.GEMINI_TEMPERATURE == 0.1
    assert config.GEMINI_MAX_OUTPUT_TOKENS == 2048
    assert config.PII_STRIP_ENABLED is True
    assert "general awareness" in config.DISCLAIMER_TEXT
    assert "IP professional" in config.ABSTENTION_MESSAGE


def test_omniroute_defaults_point_at_local_gateway():
    assert config.OMNIROUTE_BASE_URL.startswith("http://localhost")
    assert config.OMNIROUTE_MODEL == "auto"


def test_validate_rejects_omniroute_without_base_url(monkeypatch):
    monkeypatch.setattr(Config, "LLM_PROVIDER", "omniroute")
    monkeypatch.setattr(Config, "OMNIROUTE_BASE_URL", "")
    with pytest.raises(RuntimeError, match="OMNIROUTE_BASE_URL"):
        Config.validate()


def test_validate_accepts_configured_omniroute(monkeypatch):
    monkeypatch.setattr(Config, "LLM_PROVIDER", "omniroute")
    monkeypatch.setattr(Config, "OMNIROUTE_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setattr(Config, "CHROMA_COLLECTION_NAME", "ip_sakti_corpus")
    Config.validate()


def test_env_example_documents_admin_keys():
    text = Path(".env.example").read_text(encoding="utf-8")
    assert "VALID_API_KEYS=" in text
    assert "VALID_ADMIN_API_KEYS=" in text


def test_frontend_env_example_documents_admin_key():
    text = Path("src/web/.env.example").read_text(encoding="utf-8")
    assert "VITE_API_KEY=" in text
    assert "VALID_ADMIN_API_KEYS" in text


def test_runner_covers_env_parity_and_provider_check():
    text = Path("run.py").read_text(encoding="utf-8")
    assert "ensure_frontend_env" in text
    assert "check_key_parity" in text
    assert "--provider-check" in text
