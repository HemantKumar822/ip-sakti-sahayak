from abc import ABC, abstractmethod
from typing import Any

class VectorStore(ABC):
    @abstractmethod
    def add(self, documents: list[str], metadatas: list[dict[str, Any]], ids: list[str]) -> None:
        """Add documents to the vector store."""


    @abstractmethod
    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search for similar documents in the vector store."""


    @abstractmethod
    def count(self) -> int:
        """Return the number of documents in the vector store."""
