import json
from unittest.mock import MagicMock

import requests

from ingestion.fetchers.base_fetcher import BaseFetcher
from ingestion.fetchers.ip_india import TARGET_DOCUMENTS, IpIndiaFetcher
from src.config import config


class DummyFetcher(BaseFetcher):
    def fetch_all(self):
        return []


def test_base_fetcher_save_raw_binary(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(config, "CORPUS_RAW_DIR", str(raw_dir))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_path))

    fetcher = DummyFetcher()
    dummy_bytes = b"%PDF-1.4 dummy pdf binary stream"
    saved_path = fetcher.save_raw_binary(
        "test-guideline", dummy_bytes, extension=".pdf"
    )

    assert (raw_dir / "test-guideline.pdf").exists()
    assert (raw_dir / "test-guideline.pdf").read_bytes() == dummy_bytes
    assert saved_path == str(raw_dir / "test-guideline.pdf")


def test_ip_india_fetcher_target_documents_structure():
    assert len(TARGET_DOCUMENTS) == 3
    for doc in TARGET_DOCUMENTS:
        assert doc["document_type"] == "guideline"
        assert doc["source_url"].startswith("https://ipindia.gov.in")
        assert doc["doc_id"].startswith("ipindia-")
        assert "title" in doc
        assert "version_or_amendment_date" in doc


def test_ip_india_fetcher_success(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(config, "CORPUS_RAW_DIR", str(raw_dir))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_path))

    doc_sample = {
        "doc_id": "ipindia-guidelines-biotechnology",
        "title": "Guidelines for Examination of Biotechnology Applications for Patent",
        "source_url": "https://ipindia.gov.in/writereaddata/Portal/IPOGuidelines/1_38_1_biotechnology-guidelines-25march2013.pdf",
        "document_type": "guideline",
        "version_or_amendment_date": "2013-03-25",
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"%PDF-1.4 sample patent guideline content"
    mock_resp.raise_for_status.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    fetcher = IpIndiaFetcher(documents=[doc_sample], session=mock_session)
    results = fetcher.fetch_all()

    assert len(results) == 1
    assert results[0]["doc_id"] == "ipindia-guidelines-biotechnology"
    assert results[0]["document_type"] == "guideline"
    assert "source_url" in results[0]
    assert "date_retrieved" in results[0]
    assert results[0]["version_or_amendment_date"] == "2013-03-25"

    # Verify PDF file saved
    saved_file = raw_dir / "ipindia-guidelines-biotechnology.pdf"
    assert saved_file.exists()
    assert saved_file.read_bytes() == b"%PDF-1.4 sample patent guideline content"

    # Verify manifest updated
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest_data) == 1
    assert manifest_data[0]["doc_id"] == "ipindia-guidelines-biotechnology"
    assert manifest_data[0]["document_type"] == "guideline"


def test_ip_india_fetcher_network_error_resilience(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(config, "CORPUS_RAW_DIR", str(raw_dir))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_path))

    docs = [
        {
            "doc_id": "failing-guideline",
            "title": "Failing Guideline",
            "source_url": "https://ipindia.gov.in/failing.pdf",
            "document_type": "guideline",
            "version_or_amendment_date": "2024-01-01",
        },
        {
            "doc_id": "succeeding-guideline",
            "title": "Succeeding Guideline",
            "source_url": "https://ipindia.gov.in/succeeding.pdf",
            "document_type": "guideline",
            "version_or_amendment_date": "2024-01-01",
        },
    ]

    mock_session = MagicMock()

    def get_side_effect(url, **kwargs):
        if "failing" in url:
            raise requests.exceptions.HTTPError("500 Server Error")
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"%PDF-1.4 succeeding doc content"
        resp.raise_for_status.return_value = None
        return resp

    mock_session.get.side_effect = get_side_effect

    fetcher = IpIndiaFetcher(documents=docs, session=mock_session)
    results = fetcher.fetch_all()

    # The failing document should be skipped without crashing, and the succeeding one should be ingested
    assert len(results) == 1
    assert results[0]["doc_id"] == "succeeding-guideline"
    assert (raw_dir / "succeeding-guideline.pdf").exists()
    assert not (raw_dir / "failing-guideline.pdf").exists()


def test_ip_india_fetcher_empty_content(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(config, "CORPUS_RAW_DIR", str(raw_dir))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_path))

    doc_sample = {
        "doc_id": "empty-guideline",
        "title": "Empty Guideline",
        "source_url": "https://ipindia.gov.in/empty.pdf",
        "document_type": "guideline",
        "version_or_amendment_date": "2024-01-01",
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b""
    mock_resp.raise_for_status.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    fetcher = IpIndiaFetcher(documents=[doc_sample], session=mock_session)
    results = fetcher.fetch_all()

    # Should log error and skip empty extraction
    assert len(results) == 0
    assert not (raw_dir / "empty-guideline.pdf").exists()
