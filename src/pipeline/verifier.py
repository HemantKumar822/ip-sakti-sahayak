"""Deterministic Citation and Grounding Verifier for IP-SAKTI Sahayak.

Validates the output of AnswerGenerator against the exact legal corpus chunks
retrieved for the session, enforcing mathematical provenance and anti-hallucination
guarantees prior to presenting the answer to the user.
"""

import logging
import re
from typing import Any

from pydantic import BaseModel, Field

from src.models.response import Citation

logger = logging.getLogger("ip_sakti.pipeline.verifier")


class VerificationResult(BaseModel):
    """Structured audit result for deterministic grounding verification."""

    is_verified: bool = Field(
        default=True,
        description="True if all claims and citations strictly map to retrieved evidence.",
    )
    grounding_score: float = Field(
        default=1.0,
        description="Grounding reliability ratio (1.0 = perfect provenance, 0.0 = rejected).",
    )
    status: str = Field(
        default="verified",
        description="Verification state: 'verified', 'unverified_citations', or 'ungrounded'.",
    )
    audit_trail: list[str] = Field(
        default_factory=list,
        description="Detailed verification steps and observations.",
    )


class GroundingVerifier:
    """Verifies that generated answers do not cite invented documents or hallucinated markers."""

    @staticmethod
    def extract_inline_citation_indices(text: str) -> list[int]:
        """Extracts all bracketed citation numbers like [1], [2, 3], [1-3], [1][2] from answer text."""
        indices: list[int] = []
        # Find all brackets containing only numbers, commas, hyphens, and spaces
        for match in re.finditer(r"\[([\d\s,\-]+)\]", text):
            content = match.group(1)
            # Split by commas
            parts = [p.strip() for p in content.split(",")]
            for part in parts:
                if not part:
                    continue
                if "-" in part:
                    # Handle range like 1-3
                    bounds = [b.strip() for b in part.split("-")]
                    if len(bounds) == 2 and bounds[0].isdigit() and bounds[1].isdigit():
                        start = int(bounds[0])
                        end = int(bounds[1])
                        if start <= end:
                            indices.extend(range(start, end + 1))
                elif part.isdigit():
                    indices.append(int(part))
        return sorted(set(indices))

    def verify(
        self,
        answer: str | None,
        citations: list[Citation] | list[dict[str, Any]],
        retrieved_chunks: list[dict[str, Any]] | None,
    ) -> VerificationResult:
        """Executes strict deterministic verification on generated answer and citations.

        Verification Rules:
        1. Non-empty answer text must be provided if answered.
        2. Every inline citation marker [N] must have a corresponding citation in `citations`.
        3. Every citation's `doc_id` must match a `doc_id` present in `retrieved_chunks`.
        4. If ungrounded citations or missing document IDs are detected, fail loudly and safely.

        Args:
            answer: Generated advisory text containing [N] citation markers.
            citations: List of Citation models or citation dictionaries.
            retrieved_chunks: Corpus chunks passed into the generator.

        Returns:
            VerificationResult with is_verified flag, grounding_score, and audit trail.
        """
        audit: list[str] = []

        if not answer or not answer.strip():
            audit.append("Empty answer text provided for verification.")
            return VerificationResult(
                is_verified=False,
                grounding_score=0.0,
                status="ungrounded",
                audit_trail=audit,
            )

        # Normalize retrieved document IDs
        allowed_doc_ids: set[str] = set()
        for c in retrieved_chunks or []:
            meta = c.get("metadata", {})
            doc_id = (
                str(c.get("doc_id") or meta.get("doc_id") or c.get("id") or "")
                .strip()
                .lower()
            )
            if doc_id:
                allowed_doc_ids.add(doc_id)

        audit.append(f"Retrieved candidate documents: {sorted(allowed_doc_ids)}")

        # Normalize citations list
        parsed_citations: list[dict[str, Any]] = []
        for cit in citations:
            if isinstance(cit, Citation):
                parsed_citations.append(cit.model_dump())
            elif isinstance(cit, dict):
                parsed_citations.append(cit)

        # Check 1: Inline marker indexing
        citation_indices = self.extract_inline_citation_indices(answer)
        audit.append(f"Extracted inline citation markers: {citation_indices}")

        unmatched_markers = [
            idx for idx in citation_indices if idx < 1 or idx > len(parsed_citations)
        ]
        if unmatched_markers:
            audit.append(
                f"FAILED: Inline markers {unmatched_markers} reference non-existent citation index (citations count={len(parsed_citations)})."
            )
            return VerificationResult(
                is_verified=False,
                grounding_score=0.0,
                status="unverified_citations",
                audit_trail=audit,
            )

        # Check 2: Document provenance check
        unproven_docs: list[str] = []
        for i, cit in enumerate(parsed_citations, start=1):
            doc_id = str(cit.get("doc_id", "")).strip().lower()
            if not allowed_doc_ids or doc_id not in allowed_doc_ids:
                unproven_docs.append(f"[{i}] {doc_id}")

        if unproven_docs:
            audit.append(
                f"FAILED: Citations reference unretrieved doc_ids: {unproven_docs}. Refusing hallucinated authority."
            )
            return VerificationResult(
                is_verified=False,
                grounding_score=0.0,
                status="ungrounded",
                audit_trail=audit,
            )

        # Check 3: Verified grounding confirmation
        audit.append(
            f"PASSED: All {len(parsed_citations)} citations strictly grounded in retrieved statutory chunks."
        )
        return VerificationResult(
            is_verified=True,
            grounding_score=1.0,
            status="verified",
            audit_trail=audit,
        )
