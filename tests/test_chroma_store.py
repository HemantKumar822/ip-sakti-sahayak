import uuid
from typing import Any

import chromadb
import pytest
from chromadb import EmbeddingFunction
from chromadb.api.types import Documents, Embeddings

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
            embeddings.append([val, 1.0 - val, 0.5, 0.2])
        return embeddings

    def name(self) -> str:
        return "dummy_embedding_function"

    def get_config(self) -> dict[str, Any]:
        return {"name": "dummy_embedding_function"}


@pytest.fixture
def ephemeral_chroma_store():
    client = chromadb.EphemeralClient()
    ef = DummyEmbeddingFunction()
    col_name = f"test_col_{uuid.uuid4().hex}"
    return ChromaStore(
        collection_name=col_name,
        embedding_function=ef,
        client=client,
    )


def test_chroma_store_implements_interface(ephemeral_chroma_store):
    assert isinstance(ephemeral_chroma_store, VectorStore)
    assert ephemeral_chroma_store.count() == 0


def test_chroma_store_add_and_count(ephemeral_chroma_store):
    docs = [
        "Section 3(p) excludes traditional knowledge from patentability.",
        "Biological Diversity Act requires ABS approval for commercial utilization.",
    ]
    metas = [
        {"doc_id": "patents-act", "section": "3(p)", "type": "statute"},
        {"doc_id": "bda-2002", "section": "Section 3", "type": "statute"},
    ]
    ids = ["patents-act#chunk_1", "bda-2002#chunk_1"]

    ephemeral_chroma_store.add(documents=docs, metadatas=metas, ids=ids)
    assert ephemeral_chroma_store.count() == 2


def test_chroma_store_add_empty_list(ephemeral_chroma_store):
    # Should be a safe no-op
    ephemeral_chroma_store.add(documents=[], metadatas=[], ids=[])
    assert ephemeral_chroma_store.count() == 0


def test_chroma_store_length_mismatch_raises(ephemeral_chroma_store):
    with pytest.raises(ValueError) as exc:
        ephemeral_chroma_store.add(
            documents=["Doc 1", "Doc 2"],
            metadatas=[{"doc_id": "1"}],
            ids=["id-1", "id-2"],
        )
    assert "Length mismatch" in str(exc.value)


def test_chroma_store_search(ephemeral_chroma_store):
    docs = [
        "Section 3(p) excludes traditional knowledge from patentability.",
        "Biological Diversity Act requires ABS approval for commercial utilization.",
    ]
    metas = [
        {"doc_id": "patents-act", "section": "3(p)", "doc_type": "statute"},
        {"doc_id": "bda-2002", "section": "Section 3", "doc_type": "statute"},
    ]
    ids = ["patents-act#chunk_1", "bda-2002#chunk_1"]

    ephemeral_chroma_store.add(documents=docs, metadatas=metas, ids=ids)

    results = ephemeral_chroma_store.search("traditional knowledge patent", n_results=1)
    assert len(results) == 1
    assert "doc_id" in results[0]
    assert "document" in results[0]
    assert "snippet" in results[0]
    assert "score" in results[0]
    assert "metadata" in results[0]


def test_chroma_store_search_empty_store(ephemeral_chroma_store):
    results = ephemeral_chroma_store.search("any query", n_results=5)
    assert results == []


def test_chroma_store_search_empty_query(ephemeral_chroma_store):
    ephemeral_chroma_store.add(
        documents=["Sample text"],
        metadatas=[{"doc_id": "sample"}],
        ids=["sample#1"],
    )
    results = ephemeral_chroma_store.search("   ", n_results=5)
    assert results == []


def test_chroma_store_where_filter(ephemeral_chroma_store):
    docs = ["Doc Alpha", "Doc Beta"]
    metas = [{"doc_id": "alpha"}, {"doc_id": "beta"}]
    ids = ["id-alpha", "id-beta"]

    ephemeral_chroma_store.add(documents=docs, metadatas=metas, ids=ids)

    filtered_results = ephemeral_chroma_store.search(
        "Doc", n_results=5, where={"doc_id": "alpha"}
    )
    assert len(filtered_results) == 1
    assert filtered_results[0]["doc_id"] == "alpha"


def test_chroma_store_reset(ephemeral_chroma_store):
    ephemeral_chroma_store.add(
        documents=["Some text"],
        metadatas=[{"doc_id": "doc1"}],
        ids=["id-1"],
    )
    assert ephemeral_chroma_store.count() == 1

    ephemeral_chroma_store.reset()
    assert ephemeral_chroma_store.count() == 0


def test_chroma_store_persistent_path(tmp_path):
    persist_dir = tmp_path / "chroma_test"
    ef = DummyEmbeddingFunction()
    store = ChromaStore(
        persist_dir=str(persist_dir),
        collection_name=f"persist_test_{uuid.uuid4().hex}",
        embedding_function=ef,
    )
    store.add(
        documents=["Persistent document content"],
        metadatas=[{"doc_id": "persist-doc", "none_field": None}],
        ids=["p-1"],
    )
    assert store.count() == 1
    assert persist_dir.exists()


def test_chroma_store_batching(ephemeral_chroma_store):
    # Test batch size chunking
    docs = [f"Text chunk number {i}" for i in range(15)]
    metas = [{"doc_id": f"doc-{i}", "chunk_id": i} for i in range(15)]
    ids = [f"id-{i}" for i in range(15)]

    ephemeral_chroma_store.add(docs, metas, ids, batch_size=5)
    assert ephemeral_chroma_store.count() == 15


def test_chroma_store_default_embedding_init(monkeypatch):
    # Test initialization when embedding_function is None
    client = chromadb.EphemeralClient()
    mock_ef_instances = []

    def mock_st_ef(model_name):
        ef = DummyEmbeddingFunction()
        mock_ef_instances.append(model_name)
        return ef

    monkeypatch.setattr(
        "chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction",
        mock_st_ef,
    )

    store = ChromaStore(
        collection_name=f"default_ef_{uuid.uuid4().hex}",
        client=client,
    )
    assert store.count() == 0
    assert store.embedding_function is not None
    assert mock_ef_instances == ["BAAI/bge-small-en-v1.5"]


def test_chroma_store_embedding_function_fallback(monkeypatch):
    client = chromadb.EphemeralClient()

    # Force SentenceTransformerEmbeddingFunction to raise an exception
    def failing_st_ef(*args, **kwargs):
        raise RuntimeError("Model download blocked")

    monkeypatch.setattr(
        "chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction",
        failing_st_ef,
    )

    store = ChromaStore(
        collection_name=f"fallback_ef_{uuid.uuid4().hex}",
        client=client,
    )
    assert store.count() == 0
    assert store.embedding_function is not None
