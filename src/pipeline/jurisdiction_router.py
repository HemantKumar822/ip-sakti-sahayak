import logging
import re
from typing import Any

from pydantic import BaseModel, Field

from src.config import config

logger = logging.getLogger(__name__)

# Regular expressions for explicit international IP treaties, offices, and frameworks
INTERNATIONAL_IP_PATTERNS = [
    re.compile(r"\bPCT\b", re.IGNORECASE),
    re.compile(r"\bPatent\s+Cooperation\s+Treaty\b", re.IGNORECASE),
    re.compile(r"\bTRIPS\b", re.IGNORECASE),
    re.compile(
        r"\bTrade[- ]Related\s+Aspects\s+of\s+Intellectual\s+Property\s+Rights\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bMadrid\s+(?:Protocol|System|Agreement)\b", re.IGNORECASE),
    re.compile(r"\bParis\s+Convention\b", re.IGNORECASE),
    re.compile(r"\bWIPO\b", re.IGNORECASE),
    re.compile(r"\bWorld\s+Intellectual\s+Property\s+Organization\b", re.IGNORECASE),
    re.compile(r"\bUSPTO\b", re.IGNORECASE),
    re.compile(r"\bEPO\b", re.IGNORECASE),
    re.compile(r"\bEuropean\s+Patent\s+Office\b", re.IGNORECASE),
]


class RouterOutput(BaseModel):
    """Structured output for the Jurisdiction Router pipeline stage."""

    jurisdiction: str = Field(
        ..., description="The routed legal jurisdiction (e.g., 'India')"
    )
    corpus_tag: str = Field(
        default="india",
        description="Corpus partition identifier for retrieval",
    )
    status: str = Field(
        default="routed",
        description="Routing status: 'routed' or 'out_of_scope_international'",
    )
    message: str | None = Field(
        default=None,
        description="Contextual note or out-of-scope explanation",
    )


class JurisdictionRouter:
    """Routes queries to appropriate jurisdiction corpus and flags international IP scopes."""

    def __init__(self, default_jurisdiction: str | None = None) -> None:
        """Initializes the router with the configured default jurisdiction.

        Args:
            default_jurisdiction: Optional override; defaults to config.DEFAULT_JURISDICTION.
        """
        self.default_jurisdiction = (
            default_jurisdiction
            if default_jurisdiction is not None
            else config.DEFAULT_JURISDICTION
        )

    def is_international(self, query: str) -> bool:
        """Checks whether the query explicitly references international IP frameworks."""
        if not query or not query.strip():
            return False
        return any(pattern.search(query) for pattern in INTERNATIONAL_IP_PATTERNS)

    def route(self, query: str, classifier_output: Any = None) -> RouterOutput:
        """Routes a query to its legal corpus jurisdiction.

        Args:
            query: The user's intellectual property question.
            classifier_output: Optional output from the upstream Classifier stage.

        Returns:
            RouterOutput: Structured routing result with jurisdiction and status tag.
        """
        if self.is_international(query):
            logger.info(
                "Query flagged as out-of-scope international IP reference: %s",
                query,
            )
            return RouterOutput(
                jurisdiction=self.default_jurisdiction,
                corpus_tag="india",
                status="out_of_scope_international",
                message=(
                    "Query references international IP frameworks (e.g., PCT, TRIPS). "
                    "The system currently scopes exclusively to Indian IP Law (MVP)."
                ),
            )

        return RouterOutput(
            jurisdiction=self.default_jurisdiction,
            corpus_tag="india",
            status="routed",
            message=None,
        )
