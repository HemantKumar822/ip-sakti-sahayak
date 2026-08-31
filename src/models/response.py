from pydantic import BaseModel, Field


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
        description="Indicates if Access and Benefit Sharing (ABS) applies",
    )
    abs_detail: str | None = Field(
        default=None, description="Detailed explanation of ABS requirement if flagged"
    )
    confidence_score: float | None = Field(
        default=None, description="Overall pipeline confidence score"
    )
    abstention_message: str | None = Field(
        default=None,
        description="Explanation provided when system abstains from answering",
    )
    disclaimer: str = Field(
        default="This is for awareness only. Not legal advice.",
        description="Standard legal disclaimer",
    )
    response_time_ms: int = Field(
        default=0, description="Total request processing time in milliseconds"
    )
