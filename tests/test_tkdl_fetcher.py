import json
from unittest.mock import MagicMock

import requests

from ingestion.fetchers.tkdl_public import (
    TARGET_TKDL_DOCUMENTS,
    TkdlPublicFetcher,
)
from src.config import config


def test_tkdl_target_documents_structure():
    assert len(TARGET_TKDL_DOCUMENTS) >= 3
    for doc in TARGET_TKDL_DOCUMENTS:
        assert doc["document_type"] == "policy"
        assert doc["doc_id"].startswith("tkdl-")
        assert "title" in doc
        assert "source_url" in doc
        assert "version_or_amendment_date" in doc
        assert len(doc["content"].strip()) > 0


def test_tkdl_fetcher_success_default_docs(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(config, "CORPUS_RAW_DIR", str(raw_dir))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_path))

    fetcher = TkdlPublicFetcher()
    results = fetcher.fetch_all()

    assert len(results) == len(TARGET_TKDL_DOCUMENTS)
    for res in results:
        assert res["document_type"] == "policy"
        assert (raw_dir / f"{res['doc_id']}.txt").exists()
        assert len((raw_dir / f"{res['doc_id']}.txt").read_text(encoding="utf-8")) > 0

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest_data) == len(TARGET_TKDL_DOCUMENTS)
    assert all(item["document_type"] == "policy" for item in manifest_data)


def test_tkdl_fetcher_network_fetch_when_content_absent(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(config, "CORPUS_RAW_DIR", str(raw_dir))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_path))

    doc_sample = {
        "doc_id": "tkdl-remote-policy",
        "title": "Remote TKDL Policy",
        "source_url": "https://www.tkdl.res.in/policy.html",
        "document_type": "policy",
        "version_or_amendment_date": "2023-01-01",
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "This is remote TKDL policy text about Ayurveda formulations."
    mock_resp.raise_for_status.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    fetcher = TkdlPublicFetcher(documents=[doc_sample], session=mock_session)
    results = fetcher.fetch_all()

    assert len(results) == 1
    assert results[0]["doc_id"] == "tkdl-remote-policy"
    assert (raw_dir / "tkdl-remote-policy.txt").exists()
    assert "remote TKDL policy" in (raw_dir / "tkdl-remote-policy.txt").read_text(
        encoding="utf-8"
    )


def test_tkdl_fetcher_error_handling(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(config, "CORPUS_RAW_DIR", str(raw_dir))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_path))

    docs = [
        {
            "doc_id": "tkdl-failing",
            "title": "Failing Doc",
            "source_url": "https://tkdl.res.in/failing.html",
            "document_type": "policy",
        },
        {
            "doc_id": "tkdl-empty",
            "title": "Empty Doc",
            "source_url": "https://tkdl.res.in/empty.html",
            "document_type": "policy",
            "content": "   ",
        },
        {
            "doc_id": "tkdl-succeeding",
            "title": "Succeeding Doc",
            "source_url": "https://tkdl.res.in/ok.html",
            "document_type": "policy",
            "content": "Valid traditional knowledge protection data.",
        },
    ]

    mock_session = MagicMock()
    mock_session.get.side_effect = requests.exceptions.RequestException(
        "Connection refused"
    )

    fetcher = TkdlPublicFetcher(documents=docs, session=mock_session)
    results = fetcher.fetch_all()

    # Failing and empty should be safely skipped, succeeding should be ingested
    assert len(results) == 1
    assert results[0]["doc_id"] == "tkdl-succeeding"
    assert (raw_dir / "tkdl-succeeding.txt").exists()
    assert not (raw_dir / "tkdl-failing.txt").exists()
    assert not (raw_dir / "tkdl-empty.txt").exists()
