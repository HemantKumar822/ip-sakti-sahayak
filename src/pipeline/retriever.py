import logging
from typing import Any

from src.config import config
from src.vector_store.base import VectorStore
from src.vector_store.chroma_store import ChromaStore

logger = logging.getLogger("ip_sakti.pipeline.retriever")


class Retriever:
    """Retriever pipeline module that retrieves top-K legal text chunks from a VectorStore."""

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        top_k: int | None = None,
    ) -> None:
        """Initializes the Retriever with a VectorStore instance and default top_k.

        Args:
            vector_store: VectorStore protocol implementation (defaults to ChromaStore).
            top_k: Optional default number of chunks to retrieve (defaults to config.RETRIEVAL_TOP_K).
        """
        self.vector_store: VectorStore = (
            vector_store if vector_store is not None else ChromaStore()
        )
        self.top_k: int = (
            top_k if top_k is not None else getattr(config, "RETRIEVAL_TOP_K", 5)
        )

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieves the most similar legal corpus chunks for a given query string.

        Args:
            query: The user query string.
            top_k: Optional override for the number of results to retrieve.
            where: Optional metadata filter dictionary to pass to the vector store.

        Returns:
            List of formatted chunk dictionaries sorted by similarity score descending.
            Returns an empty list if the query is empty or the vector store has 0 documents.
        """
        if not query or not query.strip():
            logger.debug("Retriever.retrieve() called with empty query.")
            return []

        limit = top_k if top_k is not None else self.top_k
        if limit <= 0:
            return []

        try:
            if self.vector_store.count() == 0:
                logger.debug("Retriever.retrieve(): vector store is empty.")
                return []
        except Exception as e:  # noqa: BLE001
            logger.warning("Error checking vector store count: %s", e)
            return []

        try:
            raw_results = self.vector_store.search(
                query=query.strip(),
                n_results=limit,
                where=where,
            )
        except TypeError:
            # Fallback if custom VectorStore implementation doesn't support 'where'
            raw_results = self.vector_store.search(
                query=query.strip(),
                n_results=limit,
            )
        except Exception as e:  # noqa: BLE001
            logger.error("Vector store search failed for query '%s': %s", query, e)
            return []

        formatted_chunks: list[dict[str, Any]] = []
        for item in raw_results:
            meta = item.get("metadata") or {}
            chunk_text = (
                item.get("chunk_text")
                or item.get("snippet")
                or item.get("document")
                or item.get("text")
                or ""
            )
            score = item.get("similarity_score")
            if score is None:
                score = item.get("score")
            if score is None:
                score = item.get("relevance_score")
            if score is None:
                score = 1.0

            doc_id = str(
                meta.get("doc_id") or item.get("doc_id") or item.get("id") or "unknown"
            )
            raw_chunk_id = meta.get("chunk_id", item.get("chunk_id", 0))
            try:
                chunk_id = int(raw_chunk_id)
            except (ValueError, TypeError):
                chunk_id = 0

            doc_type = str(
                meta.get("doc_type")
                or meta.get("document_type")
                or item.get("doc_type")
                or item.get("document_type")
                or "statute"
            )

            formatted_chunks.append(
                {
                    "chunk_text": chunk_text,
                    "similarity_score": float(score),
                    "source_url": str(
                        meta.get("source_url") or item.get("source_url") or ""
                    ),
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "doc_type": doc_type,
                    "document_type": doc_type,
                    "date_retrieved": str(
                        meta.get("date_retrieved") or item.get("date_retrieved") or ""
                    ),
                    "version_or_amendment_date": str(
                        meta.get("version_or_amendment_date")
                        or item.get("version_or_amendment_date")
                        or ""
                    ),
                    "section_heading": str(
                        meta.get("section_heading") or item.get("section_heading") or ""
                    ),
                    "title": str(meta.get("title") or item.get("title") or doc_id),
                    "snippet": chunk_text,
                    "text": chunk_text,
                    "score": float(score),
                    "relevance_score": float(score),
                    "id": str(item.get("id") or f"{doc_id}#chunk_{chunk_id}"),
                    "metadata": meta,
                }
            )

        # Sort results by similarity_score descending
        formatted_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)

        logger.info(
            "Retriever retrieved %d chunks for query '%s'",
            len(formatted_chunks),
            query[:50],
        )
        return formatted_chunks
