import json
from unittest.mock import MagicMock

import requests

from ingestion.fetchers.base_fetcher import BaseFetcher
from ingestion.fetchers.india_code import (
    IndiaCodeFetcher,
    clean_html_to_text,
)
from src.config import config


class DummyFetcher(BaseFetcher):
    def fetch_all(self):
        return []


def test_clean_html_to_text():
    html_content = """
    <html>
        <head>
            <style>body { color: red; }</style>
            <script>alert("test");</script>
        </head>
        <body>
            <h1>The Patents Act, 1970</h1>
            <p>Section 3(p) relates to <strong>traditional knowledge</strong>.</p>
            <br/>
            <div>Subsection &amp; details &quot;quoted&quot;.</div>
        </body>
    </html>
    """
    cleaned = clean_html_to_text(html_content)
    assert "body { color: red; }" not in cleaned
    assert "alert(" not in cleaned
    assert "The Patents Act, 1970" in cleaned
    assert "Section 3(p) relates to traditional knowledge." in cleaned
    assert 'Subsection & details "quoted".' in cleaned


def test_base_fetcher_save_and_manifest(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(config, "CORPUS_RAW_DIR", str(raw_dir))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_path))

    fetcher = DummyFetcher()
    saved_path = fetcher.save_raw_text("test-doc", "Sample statute content.")
    assert (raw_dir / "test-doc.txt").exists()
    assert (raw_dir / "test-doc.txt").read_text(
        encoding="utf-8"
    ) == "Sample statute content."
    assert saved_path == str(raw_dir / "test-doc.txt")

    meta = {
        "doc_id": "test-doc",
        "source_url": "https://example.com/test",
        "document_type": "statute",
        "date_retrieved": "2026-08-31",
        "version_or_amendment_date": "2024-01-01",
    }
    fetcher.update_manifest(meta)

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest_data) == 1
    assert manifest_data[0]["doc_id"] == "test-doc"

    # Test updating existing entry in manifest
    meta["version_or_amendment_date"] = "2025-01-01"
    fetcher.update_manifest(meta)
    updated_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(updated_manifest) == 1
    assert updated_manifest[0]["version_or_amendment_date"] == "2025-01-01"


def test_india_code_fetcher_success(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(config, "CORPUS_RAW_DIR", str(raw_dir))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_path))

    statute_sample = {
        "doc_id": "patents-act-1970",
        "title": "The Patents Act, 1970",
        "source_url": "https://indiacode.nic.in/handle/123456789/1392",
        "document_type": "statute",
        "version_or_amendment_date": "2024-03-15",
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = (
        "<html><body><h1>Patents Act 1970</h1><p>Section 3(p)</p></body></html>"
    )
    mock_resp.raise_for_status.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    fetcher = IndiaCodeFetcher(statutes=[statute_sample], session=mock_session)
    results = fetcher.fetch_all()

    assert len(results) == 1
    assert results[0]["doc_id"] == "patents-act-1970"
    assert results[0]["document_type"] == "statute"
    assert results[0]["source_url"] == "https://indiacode.nic.in/handle/123456789/1392"
    assert "date_retrieved" in results[0]

    # Verify raw file saved
    saved_file = raw_dir / "patents-act-1970.txt"
    assert saved_file.exists()
    assert "Patents Act 1970" in saved_file.read_text(encoding="utf-8")


def test_india_code_fetcher_network_error_resilience(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(config, "CORPUS_RAW_DIR", str(raw_dir))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_path))

    statutes = [
        {
            "doc_id": "failing-act",
            "title": "Failing Act",
            "source_url": "https://indiacode.nic.in/failing",
            "document_type": "statute",
            "version_or_amendment_date": "2024-01-01",
        },
        {
            "doc_id": "succeeding-act",
            "title": "Succeeding Act",
            "source_url": "https://indiacode.nic.in/succeeding",
            "document_type": "statute",
            "version_or_amendment_date": "2024-01-01",
        },
    ]

    mock_session = MagicMock()

    def get_side_effect(url, **kwargs):
        if "failing" in url:
            raise requests.exceptions.HTTPError("404 Not Found")
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<html><body>Succeeding Act content</body></html>"
        resp.raise_for_status.return_value = None
        return resp

    mock_session.get.side_effect = get_side_effect

    fetcher = IndiaCodeFetcher(statutes=statutes, session=mock_session)
    results = fetcher.fetch_all()

    # The failing statute should be skipped without crashing, and the succeeding one should be ingested
    assert len(results) == 1
    assert results[0]["doc_id"] == "succeeding-act"
    assert (raw_dir / "succeeding-act.txt").exists()
    assert not (raw_dir / "failing-act.txt").exists()


def test_india_code_fetcher_empty_content(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(config, "CORPUS_RAW_DIR", str(raw_dir))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_path))

    statute_sample = {
        "doc_id": "empty-act",
        "title": "Empty Act",
        "source_url": "https://indiacode.nic.in/empty",
        "document_type": "statute",
        "version_or_amendment_date": "2024-01-01",
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = (
        "<html><head><script>alert(1);</script></head><body>   </body></html>"
    )
    mock_resp.raise_for_status.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    fetcher = IndiaCodeFetcher(statutes=[statute_sample], session=mock_session)
    results = fetcher.fetch_all()

    # Should log error and skip empty extraction
    assert len(results) == 0
