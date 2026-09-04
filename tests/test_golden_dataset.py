"""Unit tests for the 50+ query golden benchmark dataset and evaluation schemas."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from evaluation.schemas import (
    EvaluationReport,
    EvaluationResult,
    GoldenQuery,
    JudgeScore,
    MetricSummary,
)


def test_golden_expanded_dataset_schema_and_distribution():
    """Verify golden_expanded.json exists, adheres to GoldenQuery schema, and matches required distribution."""
    dataset_path = Path("evaluation/data/golden_expanded.json")
    assert dataset_path.exists(), f"Missing dataset file at {dataset_path}"

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 50, f"Expected exactly 50 benchmark queries, found {len(data)}"

    parsed_queries: list[GoldenQuery] = []
    for idx, item in enumerate(data):
        try:
            query = GoldenQuery.model_validate(item)
            parsed_queries.append(query)
        except ValidationError as e:
            pytest.fail(f"Item at index {idx} failed GoldenQuery validation: {e}")

    # Verify query IDs are unique
    ids = [q.id for q in parsed_queries]
    assert len(ids) == len(set(ids)), "Query IDs must be unique"

    # Verify distribution
    classical_queries = [
        q for q in parsed_queries if q.expected_category == "Classical Ayurveda"
    ]
    proprietary_queries = [
        q
        for q in parsed_queries
        if q.expected_category == "Proprietary Ayurveda" and not q.expected_abs_flag
    ]
    abs_queries = [
        q
        for q in parsed_queries
        if q.expected_category == "Proprietary Ayurveda" and q.expected_abs_flag
    ]
    out_of_scope_queries = [
        q for q in parsed_queries if q.expected_category == "Unclassifiable"
    ]

    assert (
        len(classical_queries) == 15
    ), f"Expected 15 Classical queries, got {len(classical_queries)}"
    assert (
        len(proprietary_queries) == 15
    ), f"Expected 15 Proprietary queries, got {len(proprietary_queries)}"
    assert len(abs_queries) == 10, f"Expected 10 ABS queries, got {len(abs_queries)}"
    assert (
        len(out_of_scope_queries) == 10
    ), f"Expected 10 Out-of-corpus queries, got {len(out_of_scope_queries)}"

    # Specific content checks
    for q in classical_queries:
        assert q.expected_status == "answered"
        assert any("3(p)" in cit or "TKDL" in cit for cit in q.mandatory_citations)
        assert q.expected_abs_flag is False

    for q in proprietary_queries:
        assert q.expected_status == "answered"
        assert any("3(d)" in cit for cit in q.mandatory_citations)
        assert q.expected_abs_flag is False

    for q in abs_queries:
        assert q.expected_status == "answered"
        assert any("Biological Diversity" in cit for cit in q.mandatory_citations)
        assert q.expected_abs_flag is True

    for q in out_of_scope_queries:
        assert q.expected_status == "abstained"
        assert q.expected_abs_flag is False


def test_evaluation_schemas_instantiation():
    """Verify instantiation and serialization of EvaluationResult and EvaluationReport."""
    judge = JudgeScore(
        faithfulness=0.95,
        answer_relevance=0.90,
        abstention_precision=1.0,
        hallucinated_citations=[],
        reasoning="All claims grounded in cited Section 3(p).",
        passed=True,
    )

    result = EvaluationResult(
        id=1,
        query_text="Can Triphala be patented?",
        expected_status="answered",
        actual_status="answered",
        expected_category="Classical Ayurveda",
        actual_category="Classical Ayurveda",
        expected_abs_flag=False,
        actual_abs_flag=False,
        mandatory_citations=["Section 3(p)"],
        actual_citations=["Section 3(p)"],
        citations_found=["Section 3(p)"],
        status_match=True,
        category_match=True,
        abs_match=True,
        mandatory_citations_present=True,
        confidence_score=0.88,
        grounding_score=0.95,
        latency_ms=120.5,
        passed=True,
        judge_score=judge,
    )
    assert result.passed is True
    assert result.judge_score.faithfulness == 0.95

    summary = MetricSummary(
        total_queries=1,
        passed_queries=1,
        failed_queries=0,
        overall_pass_rate=100.0,
        status_accuracy=100.0,
        category_accuracy=100.0,
        abs_accuracy=100.0,
        mandatory_citation_recall=100.0,
        avg_latency_ms=120.5,
        p50_latency_ms=120.5,
        p90_latency_ms=120.5,
        p99_latency_ms=120.5,
        category_distribution={"Classical Ayurveda": 1},
        avg_faithfulness=0.95,
        avg_answer_relevance=0.90,
        avg_abstention_precision=1.0,
        hallucination_violations_count=0,
    )

    report = EvaluationReport(
        timestamp="2026-09-04T12:00:00Z",
        dataset_path="evaluation/data/golden_expanded.json",
        summary=summary,
        results=[result],
    )
    assert report.summary.total_queries == 1
    assert len(report.results) == 1
