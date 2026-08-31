import json
import logging
from pathlib import Path
from typing import Any

from ingestion.parsers.pdf_parser import ParseError, parse_document
from src.config import config
from src.vector_store.base import VectorStore
from src.vector_store.chroma_store import ChromaStore

logger = logging.getLogger("ip_sakti.ingestion.ingest")


def run_ingest(
    manifest_path: Path | str | None = None,
    raw_dir: Path | str | None = None,
    vector_store: VectorStore | None = None,
) -> dict[str, Any]:
    """Ingests documents listed in corpus/manifest.json into the vector database.

    1. Loads manifest.json and rejects unmanifested loose files in raw directory.
    2. Parses and chunks each manifested document.
    3. Computes vector embeddings and stores chunks in ChromaDB.
    4. Updates manifest.json with the chunk_count for each document.

    Args:
        manifest_path: Path to manifest.json file.
        raw_dir: Path to raw documents folder.
        vector_store: Optional VectorStore instance (initializes ChromaStore by default).

    Returns:
        Summary dict containing ingestion statistics.
    """
    manifest_file = Path(manifest_path or config.CORPUS_MANIFEST_PATH)
    raw_folder = Path(raw_dir or config.CORPUS_RAW_DIR)

    # 1. Load manifest data
    manifest_data: list[dict[str, Any]] = []
    if manifest_file.exists():
        try:
            content = manifest_file.read_text(encoding="utf-8").strip()
            if content:
                loaded = json.loads(content)
                if isinstance(loaded, list):
                    manifest_data = loaded
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Failed to read manifest file %s: %s", manifest_file, e)
            raise

    manifest_docs_by_id: dict[str, dict[str, Any]] = {
        doc["doc_id"]: doc
        for doc in manifest_data
        if isinstance(doc, dict) and "doc_id" in doc
    }

    # 2. Reject unmanifested loose files in raw_dir with a log warning
    if raw_folder.exists():
        for file in raw_folder.iterdir():
            if file.is_file() and not file.name.startswith("."):
                file_stem = file.stem
                if (
                    file_stem not in manifest_docs_by_id
                    and file.name not in manifest_docs_by_id
                ):
                    logger.warning(
                        "Rejecting unmanifested file '%s' (not present in %s)",
                        file.name,
                        manifest_file.name,
                    )

    # 3. Initialize VectorStore (loads embedding model ONCE per ingestion run)
    if vector_store is None:
        logger.info("Initializing ChromaStore for ingestion...")
        store: VectorStore = ChromaStore()
    else:
        store = vector_store

    total_chunks_ingested = 0
    documents_processed = 0

    # 4. Ingest each manifested document
    for doc in manifest_data:
        if not isinstance(doc, dict) or "doc_id" not in doc:
            continue

        doc_id = doc["doc_id"]

        # Locate raw file for this document
        target_file = None
        for ext in [".txt", ".pdf", ""]:
            candidate = raw_folder / f"{doc_id}{ext}"
            if candidate.exists() and candidate.is_file():
                target_file = candidate
                break

        if target_file is None:
            logger.warning(
                "Document '%s' listed in manifest was not found in raw directory '%s'",
                doc_id,
                raw_folder,
            )
            doc["chunk_count"] = 0
            continue

        try:
            chunks = parse_document(target_file, doc)
        except ParseError as pe:
            logger.warning("Could not parse document '%s': %s", doc_id, pe)
            doc["chunk_count"] = 0
            continue
        except (ValueError, TypeError, OSError, RuntimeError) as e:
            logger.error("Unexpected error parsing '%s': %s", doc_id, e)
            doc["chunk_count"] = 0
            continue

        docs_list: list[str] = []
        metas_list: list[dict[str, Any]] = []
        ids_list: list[str] = []

        for chunk in chunks:
            c_id = chunk.get("chunk_id", 0)
            text = chunk.get("chunk_text", "").strip()
            if not text:
                continue

            metadata = {
                "doc_id": doc_id,
                "chunk_id": int(c_id),
                "source_url": str(
                    chunk.get("source_url") or doc.get("source_url") or ""
                ),
                "doc_type": str(
                    chunk.get("document_type") or doc.get("document_type") or "statute"
                ),
                "document_type": str(
                    chunk.get("document_type") or doc.get("document_type") or "statute"
                ),
                "date_retrieved": str(
                    chunk.get("date_retrieved") or doc.get("date_retrieved") or ""
                ),
                "version_or_amendment_date": str(
                    chunk.get("version_or_amendment_date")
                    or doc.get("version_or_amendment_date")
                    or ""
                ),
                "section_heading": str(chunk.get("section_heading") or ""),
                "title": str(chunk.get("title") or doc.get("title") or doc_id),
            }

            unique_id = f"{doc_id}#chunk_{c_id}"
            docs_list.append(text)
            metas_list.append(metadata)
            ids_list.append(unique_id)

        if docs_list:
            store.add(documents=docs_list, metadatas=metas_list, ids=ids_list)
            doc["chunk_count"] = len(docs_list)
            total_chunks_ingested += len(docs_list)
            documents_processed += 1
            logger.info(
                "Successfully ingested %d chunks for '%s'", len(docs_list), doc_id
            )
        else:
            doc["chunk_count"] = 0
            logger.warning("Document '%s' produced 0 chunks after parsing", doc_id)

    # 5. Atomically update manifest.json with chunk_count
    if manifest_file.parent.exists():
        temp_file = manifest_file.with_suffix(".tmp")
        temp_file.write_text(
            json.dumps(manifest_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temp_file.replace(manifest_file)
        logger.info("Updated manifest %s with chunk counts", manifest_file)

    summary = {
        "documents_processed": documents_processed,
        "total_documents": len(manifest_data),
        "total_chunks": total_chunks_ingested,
        "vector_store_count": store.count(),
    }
    logger.info("Ingestion complete: %s", summary)
    return summary


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_ingest()
