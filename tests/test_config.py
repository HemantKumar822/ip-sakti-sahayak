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
    assert config.GEMINI_MODEL == "gemini-1.5-flash"
    assert config.GEMINI_TEMPERATURE == 0.1
    assert config.GEMINI_MAX_OUTPUT_TOKENS == 2048
    assert config.PII_STRIP_ENABLED is True
    assert "general awareness" in config.DISCLAIMER_TEXT
    assert "IP professional" in config.ABSTENTION_MESSAGE
