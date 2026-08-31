import json
import pytest

from ingestion.manifest_validator import validate, ManifestValidationError
from src.config import config


@pytest.fixture
def valid_doc():
    return {
        "doc_id": "patents-act-1970",
        "source_url": "https://example.com/patents-act",
        "document_type": "statute",
        "date_retrieved": "2026-08-28",
        "version_or_amendment_date": "2024-01-01"
    }


def test_validate_success(valid_doc, tmp_path, monkeypatch):
    # Set up a mock empty manifest
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text("[]")
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_file))
    
    assert validate(valid_doc) is True


def test_validate_missing_single_field(valid_doc, tmp_path, monkeypatch):
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text("[]")
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_file))

    del valid_doc["source_url"]
    
    with pytest.raises(ManifestValidationError) as exc:
        validate(valid_doc)
        
    assert "Missing or empty fields: source_url" in str(exc.value)


def test_validate_missing_multiple_fields(valid_doc, tmp_path, monkeypatch):
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text("[]")
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_file))

    del valid_doc["source_url"]
    valid_doc["date_retrieved"] = ""  # Test empty value
    
    with pytest.raises(ManifestValidationError) as exc:
        validate(valid_doc)
        
    assert "source_url" in str(exc.value)
    assert "date_retrieved" in str(exc.value)


def test_validate_duplicate_doc_id(valid_doc, tmp_path, monkeypatch):
    # Set up a mock manifest containing the doc_id
    manifest_file = tmp_path / "manifest.json"
    mock_data = [{"doc_id": "patents-act-1970"}]
    manifest_file.write_text(json.dumps(mock_data))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_file))
    
    with pytest.raises(ManifestValidationError) as exc:
        validate(valid_doc)
        
    assert "Duplicate doc_id: 'patents-act-1970' already exists" in str(exc.value)


def test_validate_no_manifest_file(valid_doc, tmp_path, monkeypatch):
    # If file doesn't exist, it should still pass
    manifest_file = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_file))
    
    assert validate(valid_doc) is True
