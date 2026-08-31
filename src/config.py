import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
    GEMINI_MAX_OUTPUT_TOKENS: int = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "2048"))

    # Embedding configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

    # Vector store configuration (supports both CHROMA_PERSIST_DIR and legacy CHROMA_PERSIST_DIRECTORY)
    CHROMA_PERSIST_DIR: str = os.getenv(
        "CHROMA_PERSIST_DIR",
        os.getenv("CHROMA_PERSIST_DIRECTORY", "./corpus/embeddings"),
    )
    CHROMA_PERSIST_DIRECTORY: str = CHROMA_PERSIST_DIR

    # Chroma collection name (supports both CHROMA_COLLECTION_NAME and legacy VECTOR_DB_COLLECTION_NAME)
    CHROMA_COLLECTION_NAME: str = os.getenv(
        "CHROMA_COLLECTION_NAME",
        os.getenv("VECTOR_DB_COLLECTION_NAME", "ip_sakti_corpus"),
    )
    VECTOR_DB_COLLECTION_NAME: str = CHROMA_COLLECTION_NAME

    # Corpus configuration
    CORPUS_MANIFEST_PATH: str = os.getenv(
        "CORPUS_MANIFEST_PATH", "./corpus/manifest.json"
    )
    CORPUS_RAW_DIR: str = os.getenv("CORPUS_RAW_DIR", "./corpus/raw")

    # Pipeline thresholds
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    ABS_THRESHOLD: float = float(os.getenv("ABS_THRESHOLD", "0.55"))

    # Privacy configuration
    PII_STRIP_ENABLED: bool = os.getenv("PII_STRIP_ENABLED", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    # Server configuration (supports API_PORT/APP_PORT and API_HOST/APP_HOST)
    API_PORT: int = int(os.getenv("API_PORT", os.getenv("APP_PORT", "8000")))
    API_HOST: str = os.getenv("API_HOST", os.getenv("APP_HOST", "0.0.0.0"))
    APP_PORT: int = API_PORT
    APP_HOST: str = API_HOST

    # Jurisdiction routing configuration
    DEFAULT_JURISDICTION: str = os.getenv("DEFAULT_JURISDICTION", "India")

    # Standard Advisory Messages and Disclaimers
    DISCLAIMER_TEXT: str = os.getenv(
        "DISCLAIMER_TEXT",
        "This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation.",
    )
    ABSTENTION_MESSAGE: str = os.getenv(
        "ABSTENTION_MESSAGE",
        "The system cannot provide a confident advisory based on available legal corpus. Please consult an IP professional.",
    )


config = Config()
