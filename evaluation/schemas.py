"""Pydantic schemas for the evaluation benchmark framework."""

from pydantic import BaseModel, Field


class GoldenQuery(BaseModel):
    """Schema for a verified benchmark test query entry."""

    id: int | str = Field(..., description="Unique identifier for the benchmark query")
    query_text: str = Field(..., description="The benchmark question or prompt")
    expected_status: str = Field(
        ..., description="Expected pipeline status ('answered' or 'abstained')"
    )
    expected_category: str = Field(
        ..., description="Expected product/query category classification"
    )
    mandatory_citations: list[str] = Field(
        default_factory=list,
        description="Statutes, sections, or authorities that must be cited in the response",
    )
    expected_abs_flag: bool = Field(
        default=False,
        description="Whether the query must trigger an Access and Benefit Sharing (ABS) flag",
    )
    description: str | None = Field(
        default=None,
        description="Contextual legal or technical rationale for this test case",
    )


class JudgeScore(BaseModel):
    """Schema for LLM-as-a-judge evaluation scoring."""

    faithfulness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Faithfulness score (0-1): statements supported by citations",
    )
    answer_relevance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Answer relevance score (0-1): answers user question directly",
    )
    abstention_precision: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Abstention precision (0-1): correctly abstained when required",
    )
    hallucinated_citations: list[str] = Field(
        default_factory=list,
        description="Citations or sections fabricated by the model",
    )
    reasoning: str = Field(
        default="", description="Evaluator rationale for the assigned scores"
    )
    passed: bool = Field(
        default=True,
        description="Whether the query passed quality and anti-hallucination thresholds",
    )


class EvaluationResult(BaseModel):
    """Execution result for a single benchmark query."""

    id: int | str
    query_text: str
    expected_status: str
    actual_status: str
    expected_category: str
    actual_category: str
    expected_abs_flag: bool
    actual_abs_flag: bool
    mandatory_citations: list[str] = Field(default_factory=list)
    actual_citations: list[str] = Field(default_factory=list)
    citations_found: list[str] = Field(default_factory=list)
    status_match: bool
    category_match: bool
    abs_match: bool
    mandatory_citations_present: bool = True
    confidence_score: float = 0.0
    grounding_score: float = 1.0
    latency_ms: float = 0.0
    passed: bool
    error: str | None = None
    judge_score: JudgeScore | None = None


class MetricSummary(BaseModel):
    """Statistical summary of an evaluation run."""

    total_queries: int
    passed_queries: int
    failed_queries: int
    overall_pass_rate: float
    status_accuracy: float
    category_accuracy: float
    abs_accuracy: float
    mandatory_citation_recall: float
    avg_latency_ms: float
    p50_latency_ms: float
    p90_latency_ms: float
    p99_latency_ms: float
    category_distribution: dict[str, int]
    avg_faithfulness: float | None = None
    avg_answer_relevance: float | None = None
    avg_abstention_precision: float | None = None
    hallucination_violations_count: int = 0


class EvaluationReport(BaseModel):
    """Structured report of a complete evaluation run."""

    timestamp: str
    dataset_path: str
    summary: MetricSummary
    results: list[EvaluationResult]
