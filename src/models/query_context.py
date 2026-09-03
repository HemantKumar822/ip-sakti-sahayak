from dataclasses import dataclass


@dataclass
class QueryContext:
    """Structured context object for passing query state through the RAG pipeline."""
    raw_query: str
    english_keywords: str
    is_hindi: bool
