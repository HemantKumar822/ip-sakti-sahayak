import os
from typing import ClassVar

from dotenv import load_dotenv

load_dotenv()


class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
    GEMINI_MAX_OUTPUT_TOKENS: int = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "2048"))
    GEMINI_REQUEST_TIMEOUT: float = float(os.getenv("GEMINI_REQUEST_TIMEOUT", "30.0"))

    # LLM Provider configuration ('gemini', 'openrouter', or 'omniroute')
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

    # OpenRouter configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv(
        "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct"
    )
    OPENROUTER_BASE_URL: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )

    # OmniRoute configuration (used when LLM_PROVIDER=omniroute)
    OMNIROUTE_API_KEY: str = os.getenv("OMNIROUTE_API_KEY", "omniroute-local")
    OMNIROUTE_MODEL: str = os.getenv("OMNIROUTE_MODEL", "auto")
    OMNIROUTE_BASE_URL: str = os.getenv(
        "OMNIROUTE_BASE_URL", "http://localhost:11434/v1"
    )

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
        os.getenv("VECTOR_DB_COLLECTION_NAME", ""),
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

    # Session & Persistence configuration
    SESSION_DB_PATH: str = os.getenv("SESSION_DB_PATH", "./corpus/sessions.db")
    MAX_SESSION_TURNS: int = int(os.getenv("MAX_SESSION_TURNS", "6"))

    # Server configuration (supports API_PORT/APP_PORT and API_HOST/APP_HOST)
    API_PORT: int = int(os.getenv("API_PORT", os.getenv("APP_PORT", "8000")))
    API_HOST: str = os.getenv("API_HOST", os.getenv("APP_HOST", "0.0.0.0"))
    APP_PORT: int = API_PORT
    APP_HOST: str = API_HOST
    CORS_ORIGINS: ClassVar[list[str]] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]

    # API Authentication & Security
    API_KEYS: ClassVar[list[str]] = [
        k.strip() for k in os.getenv("VALID_API_KEYS", "").split(",") if k.strip()
    ]
    ADMIN_API_KEYS: ClassVar[list[str]] = [
        k.strip() for k in os.getenv("VALID_ADMIN_API_KEYS", "").split(",") if k.strip()
    ]

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

    @classmethod
    def validate(cls) -> None:
        """Validates that required configuration is present."""
        if cls.LLM_PROVIDER == "gemini" and not cls.GEMINI_MODEL:
            raise RuntimeError(
                "GEMINI_MODEL is required when LLM_PROVIDER is 'gemini' but not set in configuration or environment variables."
            )
        if cls.LLM_PROVIDER == "openrouter" and not cls.OPENROUTER_MODEL:
            raise RuntimeError(
                "OPENROUTER_MODEL is required when LLM_PROVIDER is 'openrouter' but not set in configuration or environment variables."
            )
        if cls.LLM_PROVIDER == "omniroute" and not cls.OMNIROUTE_BASE_URL:
            raise RuntimeError(
                "OMNIROUTE_BASE_URL is required when LLM_PROVIDER is 'omniroute' but not set in configuration or environment variables."
            )
        if not cls.CHROMA_COLLECTION_NAME:
            raise RuntimeError(
                "CHROMA_COLLECTION_NAME is required but not set in configuration or environment variables."
            )


config = Config()
