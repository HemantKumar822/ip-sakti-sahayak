import json
from unittest.mock import patch

import pytest

from ingestion.ingest import run_ingest
from src.vector_store.base import VectorStore


class MockVectorStore(VectorStore):
    """In-memory vector store for unit testing ingest orchestration."""

    def __init__(self):
        self.documents: list[str] = []
        self.metadatas: list[dict] = []
        self.ids: list[str] = []

    def add(
        self,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
        batch_size: int = 500,
    ) -> None:
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)

    def search(self, query: str, n_results: int = 5, where=None):
        return [{"id": i, "document": d} for i, d in zip(self.ids, self.documents)]

    def count(self) -> int:
        return len(self.documents)


@pytest.fixture
def sample_corpus_env(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = tmp_path / "manifest.json"

    # Create 2 valid text files with multiple statutory sentences
    patents_content = (
        "CHAPTER II - INVENTIONS NOT PATENTABLE\n\n"
        "Section 3(p) provides that an invention which in effect is traditional knowledge "
        "or which is an aggregation or duplication of known properties of traditionally known "
        "component or components is not an invention.\n\n"
        "Section 3(j) provides that plants and animals in whole or any part thereof other than "
        "microorganisms but including seeds, varieties and species and essentially biological "
        "processes for production or propagation of plants and animals are not patentable.\n\n"
        "Section 3(d) excludes the mere discovery of a new form of a known substance which does "
        "not result in the enhancement of the known efficacy of that substance."
    )
    (raw_dir / "patents-act-1970.txt").write_text(patents_content, encoding="utf-8")

    bda_content = (
        "CHAPTER III - NATIONAL BIODIVERSITY AUTHORITY\n\n"
        "Section 3 of the Biological Diversity Act 2002 mandates that certain persons shall "
        "not obtain biological resources or associated knowledge for research or commercial "
        "utilization without prior approval of the National Biodiversity Authority.\n\n"
        "Section 6 provides that no person shall apply for any intellectual property right, "
        "by whatever name called, in or outside India for any invention based on any research "
        "or information on a biological resource obtained from India without previous approval."
    )
    (raw_dir / "biological-diversity-act-2002.txt").write_text(
        bda_content, encoding="utf-8"
    )

    manifest_data = [
        {
            "doc_id": "patents-act-1970",
            "source_url": "https://indiacode.nic.in/handle/123456789/1392",
            "document_type": "statute",
            "date_retrieved": "2026-08-31",
            "version_or_amendment_date": "2024-03-15",
            "title": "The Patents Act, 1970",
        },
        {
            "doc_id": "biological-diversity-act-2002",
            "source_url": "https://indiacode.nic.in/handle/123456789/2046",
            "document_type": "statute",
            "date_retrieved": "2026-08-31",
            "version_or_amendment_date": "2023-08-01",
            "title": "The Biological Diversity Act, 2002",
        },
    ]
    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    return {
        "raw_dir": raw_dir,
        "manifest_file": manifest_file,
        "manifest_data": manifest_data,
    }


def test_run_ingest_success(sample_corpus_env):
    raw_dir = sample_corpus_env["raw_dir"]
    manifest_file = sample_corpus_env["manifest_file"]
    store = MockVectorStore()

    summary = run_ingest(
        manifest_path=manifest_file,
        raw_dir=raw_dir,
        vector_store=store,
    )

    assert summary["documents_processed"] == 2
    assert summary["total_documents"] == 2
    assert summary["total_chunks"] > 0
    assert store.count() == summary["total_chunks"]

    # Verify manifest was updated with chunk_count
    updated_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert len(updated_manifest) == 2
    assert "chunk_count" in updated_manifest[0]
    assert updated_manifest[0]["chunk_count"] > 0
    assert "chunk_count" in updated_manifest[1]
    assert updated_manifest[1]["chunk_count"] > 0


def test_run_ingest_rejects_unmanifested_loose_file(sample_corpus_env, caplog):
    raw_dir = sample_corpus_env["raw_dir"]
    manifest_file = sample_corpus_env["manifest_file"]

    # Add an unmanifested rogue file
    (raw_dir / "unmanifested-secret-doc.txt").write_text(
        "Secret unverified legal text", encoding="utf-8"
    )

    store = MockVectorStore()
    with caplog.at_level("WARNING"):
        summary = run_ingest(
            manifest_path=manifest_file,
            raw_dir=raw_dir,
            vector_store=store,
        )

    assert "Rejecting unmanifested file" in caplog.text
    assert summary["documents_processed"] == 2
    # Ensure unmanifested doc was not added to store
    for meta in store.metadatas:
        assert meta["doc_id"] != "unmanifested-secret-doc"


def test_run_ingest_missing_raw_file(sample_corpus_env, caplog):
    raw_dir = sample_corpus_env["raw_dir"]
    manifest_file = sample_corpus_env["manifest_file"]

    # Add document to manifest that does not exist on disk
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest_data.append(
        {
            "doc_id": "non-existent-statute",
            "source_url": "https://example.com/missing",
            "document_type": "statute",
            "date_retrieved": "2026-08-31",
            "version_or_amendment_date": "2024-01-01",
        }
    )
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")

    store = MockVectorStore()
    with caplog.at_level("WARNING"):
        summary = run_ingest(
            manifest_path=manifest_file,
            raw_dir=raw_dir,
            vector_store=store,
        )

    assert "was not found in raw directory" in caplog.text
    assert summary["total_documents"] == 3
    updated_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    missing_entry = next(
        d for d in updated_manifest if d["doc_id"] == "non-existent-statute"
    )
    assert missing_entry["chunk_count"] == 0


def test_run_ingest_empty_raw_file_error_handled(sample_corpus_env, caplog):
    raw_dir = sample_corpus_env["raw_dir"]
    manifest_file = sample_corpus_env["manifest_file"]

    # Overwrite one file with 0 bytes
    (raw_dir / "patents-act-1970.txt").write_text("", encoding="utf-8")

    store = MockVectorStore()
    with caplog.at_level("WARNING"):
        summary = run_ingest(
            manifest_path=manifest_file,
            raw_dir=raw_dir,
            vector_store=store,
        )

    assert summary["documents_processed"] == 1
    updated_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    patents_entry = next(
        d for d in updated_manifest if d["doc_id"] == "patents-act-1970"
    )
    assert patents_entry["chunk_count"] == 0


def test_run_ingest_empty_manifest(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text("[]", encoding="utf-8")

    store = MockVectorStore()
    summary = run_ingest(
        manifest_path=manifest_file,
        raw_dir=raw_dir,
        vector_store=store,
    )
    assert summary["documents_processed"] == 0
    assert summary["total_chunks"] == 0


def test_run_ingest_corrupt_manifest_raises(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text("{corrupt json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        run_ingest(
            manifest_path=manifest_file,
            raw_dir=raw_dir,
        )


def test_run_ingest_generic_parse_exception_handled(sample_corpus_env, caplog):
    raw_dir = sample_corpus_env["raw_dir"]
    manifest_file = sample_corpus_env["manifest_file"]

    store = MockVectorStore()

    with (
        patch(
            "ingestion.ingest.parse_document",
            side_effect=RuntimeError("Unexpected boom"),
        ),
        caplog.at_level("ERROR"),
    ):
        summary = run_ingest(
            manifest_path=manifest_file,
            raw_dir=raw_dir,
            vector_store=store,
        )

    assert "Unexpected error parsing" in caplog.text
    assert summary["documents_processed"] == 0


def test_run_ingest_default_store_init(sample_corpus_env):
    raw_dir = sample_corpus_env["raw_dir"]
    manifest_file = sample_corpus_env["manifest_file"]

    mock_store = MockVectorStore()
    with patch("ingestion.ingest.ChromaStore", return_value=mock_store):
        summary = run_ingest(
            manifest_path=manifest_file,
            raw_dir=raw_dir,
            vector_store=None,
        )

    assert summary["documents_processed"] == 2
    assert summary["total_chunks"] > 0
