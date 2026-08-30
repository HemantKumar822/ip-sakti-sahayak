from typing import Any

import pytest

from src.vector_store.base import VectorStore


class DummyVectorStore(VectorStore):
    def __init__(self):
        self.docs: list[str] = []

    def add(
        self, documents: list[str], metadatas: list[dict[str, Any]], ids: list[str]
    ) -> None:
        self.docs.extend(documents)

    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        return [{"doc": d} for d in self.docs[:n_results]]

    def count(self) -> int:
        return len(self.docs)


def test_vector_store_implementation():
    store = DummyVectorStore()
    assert store.count() == 0

    store.add(
        documents=["Patents Act 1970 Section 3(p)"],
        metadatas=[{"source": "indiacode"}],
        ids=["id-1"],
    )
    assert store.count() == 1

    results = store.search("Patents Act")
    assert len(results) == 1
    assert results[0]["doc"] == "Patents Act 1970 Section 3(p)"


def test_vector_store_abstract_instantiation_error():
    with pytest.raises(TypeError):
        VectorStore()  # type: ignore[abstract]
