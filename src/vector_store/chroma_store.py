import contextlib
import json
import logging
from pathlib import Path
from typing import Any, cast

import chromadb
from chromadb.api import ClientAPI
from chromadb.utils import embedding_functions

from src.config import config
from src.vector_store.base import VectorStore

logger = logging.getLogger("ip_sakti.vector_store.chroma")


class ChromaStore(VectorStore):
    """ChromaDB-backed implementation of the VectorStore abstract interface."""

    def __init__(
        self,
        persist_dir: str | Path | None = None,
        collection_name: str | None = None,
        embedding_model: str | None = None,
        embedding_function: Any | None = None,
        client: ClientAPI | None = None,
    ) -> None:
        self.persist_dir = Path(persist_dir or config.CHROMA_PERSIST_DIR)
        self.collection_name = collection_name or config.CHROMA_COLLECTION_NAME
        self.embedding_model_name = embedding_model or config.EMBEDDING_MODEL

        # Configure or initialize embedding function (cached once per store instance)
        if embedding_function is not None:
            self.embedding_function: Any = embedding_function
        else:
            try:
                self.embedding_function = (
                    embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=self.embedding_model_name
                    )
                )
            except (ImportError, ValueError, RuntimeError, OSError) as e:
                logger.warning(
                    "Could not load SentenceTransformerEmbeddingFunction (%s). Falling back to DefaultEmbeddingFunction.",
                    e,
                )
                self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # Configure ChromaDB client
        if client is not None:
            self.client = client
        elif persist_dir is not None or config.CHROMA_PERSIST_DIR:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        else:
            self.client = chromadb.EphemeralClient()

        # Initialize or get collection with cosine space
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=cast(Any, self.embedding_function),
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Initialized ChromaStore collection '%s' at %s",
            self.collection_name,
            self.persist_dir if client is None else "[custom client]",
        )

    def add(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
        batch_size: int = 500,
    ) -> None:
        """Add documents and corresponding metadata to the ChromaDB collection.

        Args:
            documents: List of document text strings.
            metadatas: List of metadata dictionaries.
            ids: List of unique document or chunk IDs.
            batch_size: Batch size for chunked insertion.

        Raises:
            ValueError: If input lists do not have matching lengths.
        """
        if not documents:
            logger.debug("ChromaStore.add() called with empty document list.")
            return

        if len(documents) != len(ids) or len(documents) != len(metadatas):
            raise ValueError(
                f"Length mismatch in ChromaStore.add(): {len(documents)} documents, "
                f"{len(metadatas)} metadatas, {len(ids)} ids"
            )

        # Sanitize metadata values: ChromaDB requires primitive types (str, int, float, bool)
        sanitized_metadatas: list[dict[str, Any]] = []
        for meta in metadatas:
            clean_meta: dict[str, Any] = {}
            for k, v in meta.items():
                if v is None:
                    clean_meta[k] = ""
                elif isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)
            sanitized_metadatas.append(clean_meta)

        total_chunks = len(documents)
        for start_idx in range(0, total_chunks, batch_size):
            end_idx = min(start_idx + batch_size, total_chunks)
            batch_docs = documents[start_idx:end_idx]
            batch_metas = sanitized_metadatas[start_idx:end_idx]
            batch_ids = ids[start_idx:end_idx]

            self.collection.upsert(
                documents=batch_docs,
                metadatas=cast(Any, batch_metas),
                ids=batch_ids,
            )
            logger.debug(
                "Upserted batch %d-%d of %d chunks into '%s'",
                start_idx,
                end_idx,
                total_chunks,
                self.collection_name,
            )

        logger.info(
            "Successfully stored %d chunks into ChromaStore collection '%s'",
            total_chunks,
            self.collection_name,
        )

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar documents matching the query string.

        Args:
            query: The search query text.
            n_results: Maximum number of results to return.
            where: Optional metadata filter dictionary.

        Returns:
            List of matching result dictionaries containing doc_id, snippet text,
            metadata, and similarity score.
        """
        current_count = self.count()
        if current_count == 0 or not query.strip():
            return []

        limit = min(max(1, n_results), current_count)
        query_kwargs: dict[str, Any] = {
            "query_texts": [query],
            "n_results": limit,
        }
        if where:
            query_kwargs["where"] = where

        raw_results = self.collection.query(**query_kwargs)

        raw_ids = raw_results.get("ids")
        ids = raw_ids[0] if raw_ids and len(raw_ids) > 0 else []

        raw_docs = raw_results.get("documents")
        docs = raw_docs[0] if raw_docs and len(raw_docs) > 0 else []

        raw_metas = raw_results.get("metadatas")
        metas = raw_metas[0] if raw_metas and len(raw_metas) > 0 else []

        raw_distances = raw_results.get("distances")
        distances = raw_distances[0] if raw_distances and len(raw_distances) > 0 else []

        formatted_results: list[dict[str, Any]] = []
        for idx, item_id in enumerate(ids):
            meta = metas[idx] if idx < len(metas) and metas[idx] else {}
            doc_text = docs[idx] if idx < len(docs) else ""
            dist = distances[idx] if idx < len(distances) else None

            # With cosine distance (0.0 to 2.0), similarity score = max(0.0, 1.0 - distance)
            if dist is not None:
                score = round(max(0.0, min(1.0, 1.0 - dist)), 4)
            else:
                score = 1.0

            formatted_results.append(
                {
                    "id": item_id,
                    "doc_id": meta.get("doc_id", item_id),
                    "document": doc_text,
                    "text": doc_text,
                    "snippet": doc_text,
                    "metadata": meta,
                    "distance": dist,
                    "score": score,
                    "relevance_score": score,
                }
            )

        return formatted_results

    def count(self) -> int:
        """Return the number of documents in the vector store."""
        return self.collection.count()

    def get_collection_stats(self) -> dict[str, Any]:
        """Return diagnostic statistics and health status of the ChromaDB collection.

        Returns:
            Dictionary containing collection status, name, total chunk count,
            unique document count, and sorted list of document IDs and breakdowns.
        """
        total_chunks = self.count()
        documents: list[str] = []
        document_breakdown: list[dict[str, Any]] = []

        manifest_by_id: dict[str, dict[str, Any]] = {}
        manifest_path = Path(config.CORPUS_MANIFEST_PATH)
        if manifest_path.exists():
            with (
                contextlib.suppress(Exception),
                open(manifest_path, encoding="utf-8") as f,
            ):
                manifest_data = json.load(f)
                if isinstance(manifest_data, list):
                    for item in manifest_data:
                        if isinstance(item, dict) and item.get("doc_id"):
                            manifest_by_id[item["doc_id"]] = item

        chunk_counts: dict[str, int] = {}
        doc_metas: dict[str, dict[str, Any]] = {}

        if total_chunks > 0:
            data = self.collection.get(include=["metadatas"])
            metadatas = data.get("metadatas") or []
            for meta in metadatas:
                if meta and meta.get("doc_id"):
                    d_id = str(meta["doc_id"])
                    chunk_counts[d_id] = chunk_counts.get(d_id, 0) + 1
                    if d_id not in doc_metas:
                        doc_metas[d_id] = meta
            documents = sorted(chunk_counts.keys())

            for d_id in documents:
                live_meta = doc_metas.get(d_id, {})
                man_meta = manifest_by_id.get(d_id, {})
                document_breakdown.append(
                    {
                        "doc_id": d_id,
                        "title": man_meta.get("title")
                        or live_meta.get("title")
                        or d_id,
                        "document_type": man_meta.get("document_type")
                        or live_meta.get("document_type")
                        or "statute",
                        "chunk_count": chunk_counts.get(d_id, 0),
                        "source_url": man_meta.get("source_url")
                        or live_meta.get("source_url")
                        or "",
                        "date_retrieved": man_meta.get("date_retrieved")
                        or live_meta.get("date_retrieved")
                        or "",
                        "version_or_amendment_date": man_meta.get(
                            "version_or_amendment_date"
                        )
                        or live_meta.get("version_or_amendment_date")
                        or "",
                    }
                )

        return {
            "status": "healthy",
            "collection_name": self.collection_name,
            "total_chunks": total_chunks,
            "document_count": len(documents),
            "documents": sorted(documents),
            "document_breakdown": document_breakdown,
        }

    def reset(self) -> None:
        """Clears and reinitializes the collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
        except (ValueError, KeyError, OSError, RuntimeError) as e:
            logger.debug(
                "Collection '%s' did not exist during reset (%s)",
                self.collection_name,
                e,
            )

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=cast(Any, self.embedding_function),
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Reset collection '%s' in ChromaStore", self.collection_name)
