import logging
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.config import config

logger = logging.getLogger("ip_sakti.pipeline.confidence_gate")


class ConfidenceGateOutput(BaseModel):
    """Structured output schema for the Confidence Gate decision."""

    decision: Literal["generate", "abstain"] = Field(
        ...,
        description="Gate decision: 'generate' if retrieval confidence is sufficient, 'abstain' otherwise.",
    )
    max_score: float = Field(
        default=0.0,
        description="Highest similarity score among the retrieved legal corpus chunks.",
    )
    chunks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Retrieved chunks passed through if decision is 'generate', or empty list if 'abstain'.",
    )


class ConfidenceGate:
    """Deterministic anti-hallucination confidence gate.

    Evaluates retrieved legal corpus chunks to determine whether retrieval confidence
    is high enough to safely generate a grounded answer without hallucination.
    """

    def __init__(self, threshold: float | None = None) -> None:
        """Initializes the Confidence Gate with a configurable threshold.

        Args:
            threshold: Minimum similarity score required to generate (defaults to config.CONFIDENCE_THRESHOLD).
        """
        self.threshold: float = (
            threshold
            if threshold is not None
            else getattr(config, "CONFIDENCE_THRESHOLD", 0.65)
        )

    def evaluate(self, chunks: list[dict[str, Any]] | None) -> ConfidenceGateOutput:
        """Evaluates retrieved chunks against the confidence threshold.

        Args:
            chunks: List of retrieved chunk dictionaries from Retriever.

        Returns:
            ConfidenceGateOutput containing decision ('generate' or 'abstain'),
            the highest similarity score observed, and the filtered chunks list.
        """
        if not chunks:
            logger.info(
                "Confidence gate: No chunks provided -> decision='abstain', max_score=0.0"
            )
            return ConfidenceGateOutput(
                decision="abstain",
                max_score=0.0,
                chunks=[],
            )

        max_score = 0.0
        for chunk in chunks:
            score_val = (
                chunk.get("similarity_score")
                if chunk.get("similarity_score") is not None
                else (
                    chunk.get("score")
                    if chunk.get("score") is not None
                    else chunk.get("relevance_score")
                )
            )
            if score_val is not None:
                try:
                    score_float = float(score_val)
                    max_score = max(max_score, score_float)
                except (ValueError, TypeError):
                    continue

        if max_score >= self.threshold:
            logger.info(
                "Confidence gate: max_score=%.4f >= threshold=%.4f -> decision='generate'",
                max_score,
                self.threshold,
            )
            return ConfidenceGateOutput(
                decision="generate",
                max_score=max_score,
                chunks=chunks,
            )

        logger.info(
            "Confidence gate: max_score=%.4f < threshold=%.4f -> decision='abstain'",
            max_score,
            self.threshold,
        )
        return ConfidenceGateOutput(
            decision="abstain",
            max_score=max_score,
            chunks=[],
        )


def evaluate_confidence(
    chunks: list[dict[str, Any]] | None, threshold: float | None = None
) -> ConfidenceGateOutput:
    """Pure functional helper to evaluate confidence of retrieved chunks."""
    gate = ConfidenceGate(threshold=threshold)
    return gate.evaluate(chunks)
