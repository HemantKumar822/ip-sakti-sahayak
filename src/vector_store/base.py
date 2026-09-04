from abc import ABC, abstractmethod
from typing import Any


class VectorStore(ABC):
    @abstractmethod
    def add(
        self, documents: list[str], metadatas: list[dict[str, Any]], ids: list[str]
    ) -> None:
        """Add documents to the vector store."""

    @abstractmethod
    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search for similar documents in the vector store."""

    @abstractmethod
    def count(self) -> int:
        """Return the number of documents in the vector store."""

    def get_collection_stats(self) -> dict[str, Any]:
        """Return diagnostic statistics and health status of the collection."""
        return {
            "status": "healthy",
            "collection_name": "default",
            "total_chunks": self.count(),
            "document_count": 0,
            "documents": [],
        }
