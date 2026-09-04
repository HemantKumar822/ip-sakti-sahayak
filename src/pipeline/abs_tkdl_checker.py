import logging
import time
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


class TKDLSimulatorAPI:
    """Simulates a secure, federated API call to the Traditional Knowledge Digital Library (TKDL).

    In a real production environment, the TKDL is a highly restricted government database.
    This adapter pattern proves the architecture is ready for enterprise API integration
    by encapsulating the logic and introducing simulated network latency.
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def _is_abs_document(self, metadata: dict[str, Any], chunk_text: str = "") -> bool:
        doc_id = str(metadata.get("doc_id", "")).lower()
        doc_type = str(
            metadata.get("doc_type") or metadata.get("document_type") or ""
        ).lower()
        title = str(metadata.get("title", "")).lower()
        source_url = str(metadata.get("source_url", "")).lower()

        combined_meta = f"{doc_id} {doc_type} {title} {source_url}"
        if any(marker in combined_meta for marker in ABS_IDENTIFIERS):
            return True

        section = str(metadata.get("section_heading", "")).lower()
        return (
            "biological diversity" in section or "nba" in section or "tkdl" in section
        )

    def fetch_prior_art(
        self, query: str, top_k: int, threshold: float
    ) -> ABSCheckerOutput:
        """Simulates an external HTTP request to the TKDL database."""
        logger.info(
            "[TKDL-SIMULATOR] Initiating secure federated API call to TKDL endpoints..."
        )

        # Simulate network latency of hitting an external secure government database
        time.sleep(0.35)

        try:
            if self.vector_store.count() == 0:
                logger.debug("[TKDL-SIMULATOR] Vector store is empty.")
                return ABSCheckerOutput()

            raw_results = self.vector_store.search(
                query=query.strip(),
                n_results=top_k,
            )
        except Exception as e:  # noqa: BLE001
            logger.error(
                "[TKDL-SIMULATOR] API/Vector store search failed for query '%s': %s",
                query,
                e,
            )
            return ABSCheckerOutput()

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

            if self._is_abs_document(meta, chunk_text):
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

        matching_abs_citations.sort(key=lambda x: x["similarity_score"], reverse=True)

        logger.info(
            "[TKDL-SIMULATOR] API response received successfully (Latency: 350ms)"
        )

        if highest_abs_score >= threshold and matching_abs_citations:
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
                threshold,
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
            threshold,
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
        """Initializes the ABS/TKDL Checker with a VectorStore and similarity threshold."""
        self.vector_store = vector_store or ChromaStore()
        self.threshold: float = (
            threshold if threshold is not None else config.ABS_THRESHOLD
        )
        self.top_k: int = top_k if top_k is not None else config.RETRIEVAL_TOP_K

        # Instantiate the simulated federated API adapter
        self.tkdl_api = TKDLSimulatorAPI(self.vector_store)

    def is_abs_document(self, metadata: dict[str, Any], chunk_text: str = "") -> bool:
        """Proxies to TKDLSimulatorAPI for backward compatibility."""
        return self.tkdl_api._is_abs_document(metadata, chunk_text)

    def check(self, query: str, top_k: int | None = None) -> ABSCheckerOutput:
        """Runs the ABS / TKDL check by invoking the federated API simulator.

        Args:
            query: The user query string.
            top_k: Optional override for number of search results to inspect.

        Returns:
            ABSCheckerOutput containing abs_flag, abs_detail, citations, and similarity_score.
        """
        if not query or not query.strip():
            logger.debug("ABSTKDLChecker called with empty query.")
            return ABSCheckerOutput()

        limit = top_k if top_k is not None else self.top_k
        if limit <= 0:
            return ABSCheckerOutput()

        # Delegate entirely to the simulated API
        return self.tkdl_api.fetch_prior_art(
            query=query, top_k=limit, threshold=self.threshold
        )


# Alias for concise import
ABSChecker = ABSTKDLChecker
