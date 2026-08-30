from src.config import Config, config


def test_config_instance():
    assert isinstance(config, Config)
    assert config.APP_HOST == "0.0.0.0"
    assert config.APP_PORT == 8000
    assert config.VECTOR_DB_COLLECTION_NAME == "ip_sakti_docs"
