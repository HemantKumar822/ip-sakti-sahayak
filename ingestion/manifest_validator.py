import json
import os

from src.config import config


class ManifestValidationError(Exception):
    pass


REQUIRED_FIELDS = [
    "doc_id",
    "source_url",
    "document_type",
    "date_retrieved",
    "version_or_amendment_date",
]


def validate(doc: dict) -> bool:
    """
    Validates that a document contains all required metadata fields
    and that its doc_id is unique across the corpus manifest.
    """
    missing_fields = []

    # Check for required fields and non-empty values
    for field in REQUIRED_FIELDS:
        if field not in doc or not doc[field]:
            missing_fields.append(field)

    errors = []
    if missing_fields:
        errors.append(f"Missing or empty fields: {', '.join(missing_fields)}")

    # Check for duplicate doc_id
    doc_id = doc.get("doc_id")
    if doc_id:
        manifest_path = config.CORPUS_MANIFEST_PATH
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)

                if isinstance(manifest_data, list):
                    existing_ids = {
                        item.get("doc_id")
                        for item in manifest_data
                        if isinstance(item, dict)
                    }
                    if doc_id in existing_ids:
                        errors.append(
                            f"Duplicate doc_id: '{doc_id}' already exists in manifest"
                        )
            except (OSError, json.JSONDecodeError):
                # If manifest is empty or invalid, we assume it's a fresh start.
                pass

    if errors:
        raise ManifestValidationError("; ".join(errors))

    return True
