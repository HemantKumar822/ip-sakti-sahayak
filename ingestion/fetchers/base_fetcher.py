import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ingestion.manifest_validator import validate
from src.config import config

logger = logging.getLogger("ip_sakti.ingestion.fetchers")


class BaseFetcher(ABC):
    """Abstract base class for all corpus document fetchers."""

    def __init__(self) -> None:
        self.raw_dir = Path(config.CORPUS_RAW_DIR)
        self.manifest_path = Path(config.CORPUS_MANIFEST_PATH)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        if not self.manifest_path.parent.exists():
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    def save_raw_text(self, doc_id: str, content: str) -> str:
        """Saves raw text content to corpus/raw/<doc_id>.txt."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.raw_dir / f"{doc_id}.txt"
        file_path.write_text(content, encoding="utf-8")
        logger.info("Saved raw text for '%s' to %s", doc_id, file_path)
        return str(file_path)

    def update_manifest(self, metadata: dict[str, Any]) -> None:
        """
        Validates metadata and updates corpus/manifest.json.
        If doc_id already exists in the manifest, updates the entry.
        Otherwise, validates uniqueness and appends it.
        """
        manifest_data: list[dict[str, Any]] = []
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        loaded = json.loads(content)
                        if isinstance(loaded, list):
                            manifest_data = loaded
            except (OSError, json.JSONDecodeError) as err:
                logger.warning(
                    "Could not parse existing manifest file (%s). Initializing fresh list.",
                    err,
                )

        doc_id = metadata.get("doc_id")
        existing_index = next(
            (i for i, item in enumerate(manifest_data) if item.get("doc_id") == doc_id),
            None,
        )

        if existing_index is not None:
            # Updating existing document entry in place
            manifest_data[existing_index] = metadata
        else:
            # Validating before appending new document entry
            validate(metadata)
            manifest_data.append(metadata)

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        logger.info("Updated manifest with document '%s'", doc_id)

    def log_error(self, doc_id: str, error: Exception | str) -> None:
        """Standardized error logger for fetch failures."""
        logger.error("Failed to fetch document '%s': %s", doc_id, error)

    @abstractmethod
    def fetch_all(self) -> list[dict[str, Any]]:
        """Fetch all target documents. Must be implemented by subclasses."""
