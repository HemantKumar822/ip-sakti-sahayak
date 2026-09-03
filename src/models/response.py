from pydantic import BaseModel, Field

from src.config import config


class Citation(BaseModel):
    doc_id: str = Field(..., description="Unique identifier for the cited document")
    source_url: str | None = Field(
        default=None, description="Official source URL of the document"
    )
    doc_type: str | None = Field(
        default=None, description="Type of document (e.g. statute, gazette, guideline)"
    )
    section: str | None = Field(
        default=None, description="Specific section, rule, or provision cited"
    )
    date_retrieved: str | None = Field(
        default=None, description="Date the document was retrieved"
    )
    snippet: str | None = Field(
        default=None, description="Relevant excerpt supporting the answer"
    )
    relevance_score: float | None = Field(
        default=None, description="Relevance or similarity score"
    )


class QueryResponse(BaseModel):
    status: str = Field(
        default="answered",
        description="Response status: 'answered', 'abstained', or 'error'",
    )
    category: str | None = Field(
        default=None, description="Classified product category"
    )
    jurisdiction: str = Field(
        default="India (MVP)", description="Applicable legal jurisdiction"
    )
    answer: str | None = Field(
        default=None, description="Generated citation-grounded advisory text"
    )
    citations: list[Citation] = Field(
        default_factory=list, description="List of source citations backing the answer"
    )
    abs_flag: bool = Field(
        default=False,
        description="Indicates if Access and Benefit Sharing (ABS) applies under Biological Diversity Act",
    )
    abs_detail: str | None = Field(
        default=None, description="Detailed explanation of ABS requirement if flagged"
    )
    tkdl_flag: bool = Field(
        default=False,
        description="Indicates if Traditional Knowledge Digital Library (TKDL) or Section 3(p) prior art applies",
    )
    tkdl_detail: str | None = Field(
        default=None,
        description="Detailed explanation of TKDL / Section 3(p) patent exclusion if flagged",
    )
    confidence_score: float | None = Field(
        default=None, description="Overall pipeline confidence score"
    )
    grounding_score: float = Field(
        default=1.0,
        description="Deterministic citation grounding score (1.0 = verified provenance)",
    )
    verification_status: str = Field(
        default="verified",
        description="Verification state: 'verified', 'unverified_citations', or 'ungrounded'",
    )
    abstention_message: str | None = Field(
        default=None,
        description="Explanation provided when system abstains from answering",
    )
    disclaimer: str = Field(
        default=config.DISCLAIMER_TEXT,
        description="Standard legal disclaimer",
    )
    response_time_ms: int = Field(
        default=0, description="Total request processing time in milliseconds"
    )

    @property
    def requires_abs(self) -> bool:
        """Backward compatibility property for abs_flag."""
        return self.abs_flag

    @property
    def has_tkdl_prior_art(self) -> bool:
        """Convenience property for tkdl_flag."""
        return self.tkdl_flag
