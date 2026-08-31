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
