import logging
from typing import Any

from pydantic import BaseModel, Field

from src.config import config
from src.vector_store.base import VectorStore
from src.vector_store.chroma_store import ChromaStore

logger = logging.getLogger("ip_sakti.pipeline.abs_tkdl_checker")

# Recognizable identifiers, types, or title markers for ABS / TKDL legal corpus documents
ABS_IDENTIFIERS = [
    "bda",
    "abs",
    "tkdl",
    "biological",
    "biodiversity",
    "nba",
    "traditional",
    "s3p",
    "section 3(p)",
    "section 3p",
]


class ABSCheckerOutput(BaseModel):
    """Structured output schema for the ABS / TKDL Prior Art Checker stage."""

    abs_flag: bool = Field(
        default=False,
        description="Indicates whether Access and Benefit Sharing (ABS) or TKDL prior art compliance applies.",
    )
    abs_detail: str | None = Field(
        default=None,
        description="Statutory explanation and retrieved citation for the ABS requirement if flagged.",
    )
    tkdl_flag: bool = Field(
        default=False,
        description="Indicates whether Traditional Knowledge Digital Library (TKDL) or Section 3(p) prior art applies.",
    )
    tkdl_detail: str | None = Field(
        default=None,
        description="Statutory explanation for TKDL prior art / Section 3(p) patent exclusion if flagged.",
    )
    citations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of relevant ABS/TKDL citations retrieved from the legal corpus.",
    )
    similarity_score: float = Field(
        default=0.0,
        description="Highest cosine similarity score among matching ABS/TKDL corpus chunks.",
    )


class ABSTKDLChecker:
    """Checks whether a user query touches biological resources or traditional knowledge

    requiring ABS compliance under the Biological Diversity Act, 2002 or TKDL prior art bars.
    """

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        threshold: float | None = None,
        top_k: int | None = None,
    ) -> None:
        """Initializes the ABS/TKDL Checker with a VectorStore and similarity threshold.

        Args:
            vector_store: VectorStore instance (defaults to persistent ChromaStore).
            threshold: Cosine similarity threshold for flagging ABS/TKDL relevance.
                       Defaults to config.ABS_THRESHOLD (0.55).
            top_k: Number of candidate chunks to retrieve and evaluate.
                   Defaults to config.RETRIEVAL_TOP_K (5).
        """
        self.vector_store = vector_store or ChromaStore()
        self.threshold: float = (
            threshold if threshold is not None else config.ABS_THRESHOLD
        )
        self.top_k: int = top_k if top_k is not None else config.RETRIEVAL_TOP_K

    def is_abs_document(self, metadata: dict[str, Any], chunk_text: str = "") -> bool:
        """Determines if a document or chunk belongs to the ABS / TKDL statutory regime.

        Inspects metadata fields (doc_id, doc_type, title, source_url, section_heading).

        Args:
            metadata: Metadata dictionary associated with a chunk.
            chunk_text: Text content of the chunk.

        Returns:
            True if the chunk is from an ABS or TKDL legal source, False otherwise.
        """
        doc_id = str(metadata.get("doc_id", "")).lower()
        doc_type = str(
            metadata.get("doc_type") or metadata.get("document_type") or ""
        ).lower()
        title = str(metadata.get("title", "")).lower()
        source_url = str(metadata.get("source_url", "")).lower()

        combined_meta = f"{doc_id} {doc_type} {title} {source_url}"
        if any(marker in combined_meta for marker in ABS_IDENTIFIERS):
            return True

        # Check section heading or chunk content for explicit statutory references
        section = str(metadata.get("section_heading", "")).lower()
        return (
            "biological diversity" in section or "nba" in section or "tkdl" in section
        )

    def check(self, query: str, top_k: int | None = None) -> ABSCheckerOutput:
        """Runs the ABS / TKDL check on the query via vector retrieval.

        Args:
            query: The user query string.
            top_k: Optional override for number of search results to inspect.

        Returns:
            ABSCheckerOutput containing abs_flag, abs_detail, citations, and similarity_score.
        """
        if not query or not query.strip():
            logger.debug("ABSTKDLChecker called with empty query.")
            return ABSCheckerOutput(
                abs_flag=False,
                abs_detail=None,
                citations=[],
                similarity_score=0.0,
            )

        limit = top_k if top_k is not None else self.top_k
        if limit <= 0:
            return ABSCheckerOutput(
                abs_flag=False,
                abs_detail=None,
                citations=[],
                similarity_score=0.0,
            )

        try:
            if self.vector_store.count() == 0:
                logger.debug("ABSTKDLChecker: vector store is empty.")
                return ABSCheckerOutput(
                    abs_flag=False,
                    abs_detail=None,
                    citations=[],
                    similarity_score=0.0,
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("Error checking vector store count in ABSTKDLChecker: %s", e)
            return ABSCheckerOutput(
                abs_flag=False,
                abs_detail=None,
                citations=[],
                similarity_score=0.0,
            )

        try:
            # Query vector store for candidates
            raw_results = self.vector_store.search(
                query=query.strip(),
                n_results=limit,
            )
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Vector store search failed during ABS check for query '%s': %s",
                query,
                e,
            )
            return ABSCheckerOutput(
                abs_flag=False,
                abs_detail=None,
                citations=[],
                similarity_score=0.0,
            )

        matching_abs_citations: list[dict[str, Any]] = []
        highest_abs_score = 0.0

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

            numeric_score = float(score)

            if self.is_abs_document(meta, chunk_text):
                doc_id = str(
                    meta.get("doc_id")
                    or item.get("doc_id")
                    or item.get("id")
                    or "bda-2002"
                )
                source_url = str(meta.get("source_url") or item.get("source_url") or "")
                section = str(
                    meta.get("section_heading")
                    or meta.get("section")
                    or "Section 3 / Section 6"
                )
                doc_type = str(
                    meta.get("doc_type") or meta.get("document_type") or "statute"
                )
                title = str(meta.get("title") or "Biological Diversity Act, 2002")

                citation_entry = {
                    "doc_id": doc_id,
                    "title": title,
                    "section": section,
                    "source_url": source_url,
                    "doc_type": doc_type,
                    "snippet": chunk_text,
                    "similarity_score": numeric_score,
                }
                matching_abs_citations.append(citation_entry)

                highest_abs_score = max(highest_abs_score, numeric_score)

        # Sort matching ABS citations by similarity score descending
        matching_abs_citations.sort(key=lambda x: x["similarity_score"], reverse=True)

        if highest_abs_score >= self.threshold and matching_abs_citations:
            top_match = matching_abs_citations[0]
            doc_id = top_match["doc_id"]
            section = top_match["section"]
            source_url = top_match["source_url"]
            title = top_match["title"]

            url_suffix = f" [Source: {source_url}]" if source_url else ""
            section_info = f" ({section})" if section else ""
            abs_detail = (
                f"This query involves a biological resource or traditional knowledge element. "
                f"Access and Benefit Sharing (ABS) clearance under {title}{section_info} "
                f"and National Biodiversity Authority (NBA) approval may be required prior to patenting or commercialization.{url_suffix}"
            )

            tkdl_match = any(
                "tkdl" in c.get("doc_id", "").lower()
                or "traditional" in c.get("doc_id", "").lower()
                or "traditional" in c.get("title", "").lower()
                or "s3p" in c.get("doc_id", "").lower()
                or "3(p)" in str(c.get("section", ""))
                for c in matching_abs_citations
            )
            tkdl_detail = (
                "Traditional Knowledge Prior Art Notice: Inventions based on traditional knowledge "
                "or aggregation of known properties are non-patentable under Section 3(p) of the Patents Act, 1970 "
                "and subject to prior art screening against the Traditional Knowledge Digital Library (TKDL)."
                if tkdl_match
                else None
            )

            logger.info(
                "ABS flag TRIGGERED (score=%.4f >= %.4f) for query: %s (tkdl_flag=%s)",
                highest_abs_score,
                self.threshold,
                query[:60],
                tkdl_match,
            )
            return ABSCheckerOutput(
                abs_flag=True,
                abs_detail=abs_detail,
                tkdl_flag=tkdl_match,
                tkdl_detail=tkdl_detail,
                citations=matching_abs_citations,
                similarity_score=highest_abs_score,
            )

        logger.debug(
            "ABS flag NOT triggered (max_abs_score=%.4f < %.4f) for query: %s",
            highest_abs_score,
            self.threshold,
            query[:60],
        )
        return ABSCheckerOutput(
            abs_flag=False,
            abs_detail=None,
            tkdl_flag=False,
            tkdl_detail=None,
            citations=matching_abs_citations,
            similarity_score=highest_abs_score,
        )


# Alias for concise import
ABSChecker = ABSTKDLChecker
