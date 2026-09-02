import logging
from typing import Any

from src.pipeline.bm25_retriever import BM25Retriever
from src.vector_store.base import VectorStore
from src.vector_store.chroma_store import ChromaStore

logger = logging.getLogger("ip_sakti.pipeline.hybrid_retriever")


class HybridRetriever:
    """Fuses dense vector retrieval (BAAI/bge-small-en-v1.5) with sparse lexical retrieval (BM25)

    using Reciprocal Rank Fusion (RRF) for statutory and botanical legal queries.
    """

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        bm25_retriever: BM25Retriever | None = None,
        rrf_k: int = 60,
    ) -> None:
        """Initializes HybridRetriever with a vector store and BM25 engine.

        Args:
            vector_store: Underlying dense vector store (defaults to ChromaStore).
            bm25_retriever: BM25 lexical retriever instance.
            rrf_k: Reciprocal Rank Fusion constant parameter (default: 60).
        """
        self.vector_store = vector_store or ChromaStore()
        self.bm25 = bm25_retriever or BM25Retriever()
        self.rrf_k = rrf_k
        self._is_bm25_indexed = False

    def _ensure_bm25_index(self) -> None:
        """Lazily extracts all documents from the vector store to populate the BM25 index."""
        if self._is_bm25_indexed:
            return

        try:
            collection = getattr(self.vector_store, "collection", None)
            if collection is not None:
                data = collection.get()
                docs = data.get("documents") or []
                metas = data.get("metadatas") or []
                ids = data.get("ids") or []

                corpus_items = []
                for i, doc_text in enumerate(docs):
                    meta = metas[i] if i < len(metas) else {}
                    cid = ids[i] if i < len(ids) else f"chunk_{i}"
                    corpus_items.append(
                        {
                            "id": cid,
                            "chunk_text": doc_text,
                            "section_heading": meta.get("section_heading", ""),
                            "metadata": meta,
                            "source_url": meta.get("source_url", ""),
                            "doc_id": meta.get("doc_id", ""),
                            "doc_type": meta.get("doc_type", "statute"),
                            "title": meta.get("title", ""),
                            "date_retrieved": meta.get("date_retrieved", ""),
                        }
                    )
                self.bm25.index(corpus_items)
                self._is_bm25_indexed = True
                logger.info(
                    "HybridRetriever indexed %d documents into BM25.",
                    len(corpus_items),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Could not automatically populate BM25 index from vector store: %s",
                e,
            )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Executes hybrid retrieval combining dense vector search and BM25 with RRF ranking.

        Args:
            query: User's legal question or search phrase.
            top_k: Number of final fused chunks to return.
            where: Optional metadata filter for vector search.

        Returns:
            Ranked list of top_k chunk dictionaries with calibrated similarity scores.
        """
        if not query or not query.strip():
            return []

        self._ensure_bm25_index()

        # 1. Fetch dense vector results (candidate pool = top_k * 3)
        candidate_count = max(top_k * 3, 10)
        try:
            dense_results = self.vector_store.search(
                query=query.strip(),
                n_results=candidate_count,
                where=where,
            )
        except TypeError:
            dense_results = self.vector_store.search(
                query=query.strip(),
                n_results=candidate_count,
            )
        except Exception as e:  # noqa: BLE001
            logger.error("Dense vector search failed: %s", e)
            dense_results = []

        # 2. Fetch BM25 sparse results
        sparse_results = self.bm25.search(query=query.strip(), top_k=candidate_count)

        # If sparse has no results (e.g. not indexed or mock store), return dense
        if not sparse_results:
            return dense_results[:top_k]
        if not dense_results:
            return sparse_results[:top_k]

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF_Score(d) = 1 / (rrf_k + rank_dense) + 1 / (rrf_k + rank_bm25)
        rrf_scores: dict[str, float] = {}
        chunk_map: dict[str, dict[str, Any]] = {}

        for rank, item in enumerate(dense_results, start=1):
            doc_id = str(item.get("id") or item.get("doc_id") or f"dense_{rank}")
            chunk_map[doc_id] = item
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (
                1.0 / (self.rrf_k + rank)
            )

        for rank, item in enumerate(sparse_results, start=1):
            doc_id = str(item.get("id") or item.get("doc_id") or f"sparse_{rank}")
            if doc_id not in chunk_map:
                chunk_map[doc_id] = item
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (
                1.0 / (self.rrf_k + rank)
            )

        # 4. Sort by RRF score descending
        sorted_doc_ids = sorted(
            rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True
        )

        # 5. Format and calibrate scores so Confidence Gate works seamlessly
        fused_chunks: list[dict[str, Any]] = []
        for doc_id in sorted_doc_ids[:top_k]:
            item = dict(chunk_map[doc_id])
            base_dense_score = float(
                item.get("similarity_score") or item.get("score") or 0.70
            )

            # If document appeared in both dense and sparse, apply an agreement boost (+0.05)
            in_dense = any(
                str(d.get("id") or d.get("doc_id")) == doc_id for d in dense_results
            )
            in_sparse = any(
                str(s.get("id") or s.get("doc_id")) == doc_id for s in sparse_results
            )

            boost = 0.05 if (in_dense and in_sparse) else 0.0
            calibrated_score = min(base_dense_score + boost, 0.98)

            item["similarity_score"] = calibrated_score
            item["score"] = calibrated_score
            item["relevance_score"] = calibrated_score
            item["rrf_score"] = rrf_scores[doc_id]
            fused_chunks.append(item)

        return fused_chunks
