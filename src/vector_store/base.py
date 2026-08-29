from abc import ABC, abstractmethod
from typing import List, Any

class VectorStore(ABC):
    @abstractmethod
    def add(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]) -> None:
        """Add documents to the vector store."""
        pass

    @abstractmethod
    def search(self, query: str, n_results: int = 5) -> List[dict[str, Any]]:
        """Search for similar documents in the vector store."""


    @abstractmethod
    def count(self) -> int:
        """Return the number of documents in the vector store."""
