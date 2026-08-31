import uuid
from typing import Any
from unittest.mock import MagicMock

import numpy as np

import chromadb
import pytest
from chromadb import EmbeddingFunction
from chromadb.api.types import Documents, Embeddings

from src.config import config
from src.pipeline import Retriever
from src.vector_store.base import VectorStore
from src.vector_store.chroma_store import ChromaStore


class DummyEmbeddingFunction(EmbeddingFunction[Documents]):
    """Mock embedding function for fast, deterministic testing without downloading models."""

    def __init__(self) -> None:
        pass

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: Embeddings = []
        for text in input:
            val = float(len(text) % 10) / 10.0
            embeddings.append(np.array([val, 1.0 - val, 0.5, 0.2], dtype=np.float32))
        return embeddings

    def name(self) -> str:
        return "dummy_embedding_function"

    def get_config(self) -> dict[str, Any]:
        return {"name": "dummy_embedding_function"}


class DummyVectorStore(VectorStore):
    """In-memory dummy vector store for testing retriever unit behavior."""

    def __init__(self, items: list[dict[str, Any]] | None = None) -> None:
        self.items = items or []

    def add(
        self, documents: list[str], metadatas: list[dict[str, Any]], ids: list[str]
    ) -> None:
        for idx, doc in enumerate(documents):
            meta = metadatas[idx] if idx < len(metadatas) else {}
            item_id = ids[idx] if idx < len(ids) else f"id_{idx}"
            self.items.append(
                {
                    "id": item_id,
                    "doc_id": meta.get("doc_id", item_id),
                    "document": doc,
                    "text": doc,
                    "snippet": doc,
                    "metadata": meta,
                    "similarity_score": meta.get("similarity_score", 0.85),
                    "score": meta.get("similarity_score", 0.85),
                    "relevance_score": meta.get("similarity_score", 0.85),
                }
            )

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        results = list(self.items)
        if where:
            filtered = []
            for item in results:
                meta = item.get("metadata", {})
                if all(meta.get(k) == v for k, v in where.items()):
                    filtered.append(item)
            results = filtered
        return results[:n_results]

    def count(self) -> int:
        return len(self.items)


class NoWhereVectorStore(VectorStore):
    """VectorStore implementation whose search() method does not accept a 'where' keyword argument."""

    def __init__(self, items: list[dict[str, Any]] | None = None) -> None:
        self.items = items or []

    def add(
        self, documents: list[str], metadatas: list[dict[str, Any]], ids: list[str]
    ) -> None:
        pass

    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        return self.items[:n_results]

    def count(self) -> int:
        return len(self.items)


def test_retriever_initialization_defaults() -> None:
    """Tests that Retriever initializes with default top_k and vector store."""
    dummy_store = DummyVectorStore()
    retriever = Retriever(vector_store=dummy_store)
    assert retriever.vector_store == dummy_store
    assert retriever.top_k == config.RETRIEVAL_TOP_K


def test_retriever_empty_query_returns_empty_list() -> None:
    """Tests that empty or whitespace query strings return an empty list."""
    dummy_store = DummyVectorStore(
        items=[
            {
                "id": "patents#chunk_0",
                "text": "Sample text",
                "similarity_score": 0.9,
                "metadata": {"doc_id": "patents-act-1970", "chunk_id": 0},
            }
        ]
    )
    retriever = Retriever(vector_store=dummy_store)

    assert retriever.retrieve("") == []
    assert retriever.retrieve("   ") == []
    assert retriever.retrieve(None) == []  # type: ignore[arg-type]


def test_retriever_empty_vector_store_returns_empty_list() -> None:
    """Tests that searching an empty vector store returns [] without raising an exception."""
    empty_store = DummyVectorStore(items=[])
    retriever = Retriever(vector_store=empty_store)

    results = retriever.retrieve("What is patentable in Ayurveda?")
    assert results == []


def test_retriever_basic_retrieval_and_fields() -> None:
    """Tests that retrieve() returns properly structured chunk dictionaries with all required fields."""
    sample_items = [
        {
            "id": "patents#chunk_5",
            "snippet": "Section 3(p) says traditional knowledge is not an invention...",
            "score": 0.88,
            "metadata": {
                "doc_id": "patents-act-1970",
                "chunk_id": 5,
                "source_url": "https://indiacode.nic.in/handle/123456789/1392",
                "document_type": "statute",
                "date_retrieved": "2026-08-28",
                "version_or_amendment_date": "2024-03-15",
                "title": "The Patents Act, 1970",
                "section_heading": "Section 3(p)",
            },
        }
    ]
    store = DummyVectorStore(items=sample_items)
    retriever = Retriever(vector_store=store)

    results = retriever.retrieve("traditional knowledge patentability")
    assert len(results) == 1
    chunk = results[0]

    assert (
        chunk["chunk_text"]
        == "Section 3(p) says traditional knowledge is not an invention..."
    )
    assert chunk["similarity_score"] == 0.88
    assert chunk["source_url"] == "https://indiacode.nic.in/handle/123456789/1392"
    assert chunk["doc_id"] == "patents-act-1970"
    assert chunk["chunk_id"] == 5
    assert chunk["doc_type"] == "statute"
    assert chunk["document_type"] == "statute"
    assert chunk["date_retrieved"] == "2026-08-28"
    assert chunk["version_or_amendment_date"] == "2024-03-15"
    assert chunk["section_heading"] == "Section 3(p)"
    assert chunk["title"] == "The Patents Act, 1970"


def test_retriever_sorting_order_descending() -> None:
    """Tests that returned chunks are strictly sorted by similarity_score in descending order."""
    sample_items = [
        {
            "id": "chunk_low",
            "text": "Lower match",
            "score": 0.65,
            "metadata": {"doc_id": "doc1", "chunk_id": 1},
        },
        {
            "id": "chunk_high",
            "text": "Highest match",
            "score": 0.95,
            "metadata": {"doc_id": "doc2", "chunk_id": 2},
        },
        {
            "id": "chunk_mid",
            "text": "Medium match",
            "score": 0.82,
            "metadata": {"doc_id": "doc3", "chunk_id": 3},
        },
    ]
    store = DummyVectorStore(items=sample_items)
    retriever = Retriever(vector_store=store)

    results = retriever.retrieve("Ayurveda formulation query")
    assert len(results) == 3
    assert results[0]["similarity_score"] == 0.95
    assert results[1]["similarity_score"] == 0.82
    assert results[2]["similarity_score"] == 0.65
    assert results[0]["id"] == "chunk_high"


def test_retriever_top_k_override_and_limits() -> None:
    """Tests top_k limit behavior from config, init argument, and method override."""
    sample_items = [
        {
            "id": f"chunk_{i}",
            "text": f"Text {i}",
            "score": 0.9 - (i * 0.1),
            "metadata": {"doc_id": f"doc_{i}", "chunk_id": i},
        }
        for i in range(10)
    ]
    store = DummyVectorStore(items=sample_items)

    # Initializer override
    retriever_k3 = Retriever(vector_store=store, top_k=3)
    res_k3 = retriever_k3.retrieve("test query")
    assert len(res_k3) == 3

    # Method call override
    res_k2 = retriever_k3.retrieve("test query", top_k=2)
    assert len(res_k2) == 2

    # Zero or negative top_k
    assert retriever_k3.retrieve("test query", top_k=0) == []
    assert retriever_k3.retrieve("test query", top_k=-1) == []


def test_retriever_where_filter_passed_to_store() -> None:
    """Tests that metadata filtering parameter 'where' is passed to the underlying store."""
    sample_items = [
        {
            "id": "doc_statute",
            "text": "Statute text",
            "score": 0.9,
            "metadata": {"doc_id": "doc1", "chunk_id": 1, "document_type": "statute"},
        },
        {
            "id": "doc_guideline",
            "text": "Guideline text",
            "score": 0.85,
            "metadata": {
                "doc_id": "doc2",
                "chunk_id": 1,
                "document_type": "guideline",
            },
        },
    ]
    store = DummyVectorStore(items=sample_items)
    retriever = Retriever(vector_store=store)

    statute_results = retriever.retrieve("query", where={"document_type": "statute"})
    assert len(statute_results) == 1
    assert statute_results[0]["doc_type"] == "statute"

    guideline_results = retriever.retrieve(
        "query", where={"document_type": "guideline"}
    )
    assert len(guideline_results) == 1
    assert guideline_results[0]["doc_type"] == "guideline"


def test_retriever_where_type_error_fallback() -> None:
    """Tests that VectorStore classes not supporting 'where' fallback to search without 'where'."""
    store = NoWhereVectorStore(
        items=[
            {
                "id": "item1",
                "text": "Basic chunk text",
                "metadata": {"doc_id": "doc1", "chunk_id": "non_int"},
            }
        ]
    )
    retriever = Retriever(vector_store=store)
    results = retriever.retrieve("test", where={"document_type": "statute"})
    assert len(results) == 1
    assert results[0]["similarity_score"] == 1.0
    assert results[0]["chunk_id"] == 0


def test_retriever_store_error_handling() -> None:
    """Tests that vector store search exceptions or count exceptions are handled gracefully."""
    mock_store = MagicMock(spec=VectorStore)
    mock_store.count.side_effect = RuntimeError("Chroma lock error")

    retriever = Retriever(vector_store=mock_store)
    assert retriever.retrieve("sample query") == []

    # Search raises error
    mock_store.count.side_effect = None
    mock_store.count.return_value = 5
    mock_store.search.side_effect = ValueError("Query execution failed")

    assert retriever.retrieve("sample query") == []


def test_retriever_default_chroma_store_initialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests that Retriever default constructor creates a ChromaStore instance."""
    # Mock ChromaStore so we don't load sentence-transformers in this unit test
    mock_chroma = MagicMock(spec=ChromaStore)
    monkeypatch.setattr("src.pipeline.retriever.ChromaStore", lambda: mock_chroma)

    retriever = Retriever()
    assert retriever.vector_store == mock_chroma


def test_retriever_integration_with_chroma() -> None:
    """Integration test verifying Retriever with an actual ChromaStore in ephemeral mode."""
    client = chromadb.EphemeralClient()
    ef = DummyEmbeddingFunction()
    col_name = f"test_retriever_{uuid.uuid4().hex}"

    chroma_store = ChromaStore(
        collection_name=col_name,
        embedding_function=ef,
        client=client,
    )

    chroma_store.add(
        documents=[
            "Section 3(p) Traditional knowledge is not an invention.",
            "Section 3(j) Plants and animals are not patentable subject matter.",
        ],
        metadatas=[
            {
                "doc_id": "patents-act-1970",
                "chunk_id": 1,
                "source_url": "https://indiacode.nic.in/handle/123456789/1392",
                "document_type": "statute",
                "date_retrieved": "2026-08-30",
            },
            {
                "doc_id": "patents-act-1970",
                "chunk_id": 2,
                "source_url": "https://indiacode.nic.in/handle/123456789/1392",
                "document_type": "statute",
                "date_retrieved": "2026-08-30",
            },
        ],
        ids=["patents-act-1970#chunk_1", "patents-act-1970#chunk_2"],
    )

    retriever = Retriever(vector_store=chroma_store, top_k=5)
    results = retriever.retrieve("What does Section 3(p) say?")

    assert len(results) == 2
    assert results[0]["doc_id"] == "patents-act-1970"
    assert "similarity_score" in results[0]
    assert isinstance(results[0]["similarity_score"], float)
    assert results[0]["chunk_id"] in [1, 2]
