# ruff: noqa: ASYNC230
"""Integration and unit tests for evaluation framework, runner, judge, and CLI harness."""

import asyncio
import json

from evaluation.judge import EvaluationJudge
from evaluation.metrics import compute_metrics, format_markdown_report
from evaluation.runner import EvaluationRunner
from evaluation.schemas import (
    EvaluationResult,
    GoldenQuery,
    JudgeScore,
)
from scripts.evaluate import main_async
from src.models.response import Citation, QueryResponse


def test_evaluation_runner_mock_single_and_batch():
    """Verify EvaluationRunner executes queries in mock mode with correct match metrics."""

    async def _test():
        queries = [
            GoldenQuery(
                id=1,
                query_text="Can Triphala churna be patented?",
                expected_category="Classical Ayurveda",
                expected_status="answered",
                mandatory_citations=["Section 3(p)"],
                expected_abs_flag=False,
            ),
            GoldenQuery(
                id=2,
                query_text="What is quantum mechanics?",
                expected_category="Unclassifiable",
                expected_status="abstained",
                mandatory_citations=[],
                expected_abs_flag=False,
            ),
        ]

        runner = EvaluationRunner(
            concurrency=2, rate_limit_delay=0.0, mock_pipeline=True
        )
        results = await runner.run_benchmark(queries)

        assert len(results) == 2
        assert results[0].id == 1
        assert results[0].status_match is True
        assert results[0].abs_match is True
        assert results[0].mandatory_citations_present is True
        assert results[0].passed is True

        assert results[1].id == 2
        assert results[1].status_match is True
        assert results[1].actual_status == "abstained"
        assert results[1].passed is True

    asyncio.run(_test())


def test_evaluation_runner_handles_pipeline_exception():
    """Verify runner handles unexpected exceptions from orchestrator gracefully."""

    async def _test():
        class FaultyOrchestrator:
            async def run_pipeline(self, *args, **kwargs):
                raise RuntimeError("Database connection timed out")

        runner = EvaluationRunner(
            orchestrator=FaultyOrchestrator(), mock_pipeline=False
        )
        query = GoldenQuery(
            id=99,
            query_text="Faulty query",
            expected_category="Classical Ayurveda",
            expected_status="answered",
            mandatory_citations=["Section 3(p)"],
            expected_abs_flag=False,
        )
        result = await runner.run_single_query(query)

        assert result.passed is False
        assert result.actual_status == "error"
        assert "Database connection timed out" in (result.error or "")

    asyncio.run(_test())


def test_evaluation_judge_mock_scoring():
    """Verify EvaluationJudge mock scoring for answered, abstained, and citation checks."""

    async def _test():
        judge = EvaluationJudge(mock=True)

        # 1. Answered with citations present
        q_classical = GoldenQuery(
            id=1,
            query_text="Can Triphala be patented?",
            expected_category="Classical Ayurveda",
            expected_status="answered",
            mandatory_citations=["Section 3(p)"],
            expected_abs_flag=False,
        )
        resp_classical = QueryResponse(
            status="answered",
            category="Classical Ayurveda",
            jurisdiction="India",
            answer="Triphala is barred from patenting under Section 3(p) of the Patents Act.",
            citations=[Citation(doc_id="tkdl-01", section="Section 3(p)")],
            abs_flag=False,
            confidence_score=0.9,
        )
        score1 = await judge.evaluate(q_classical, resp_classical)
        assert score1.passed is True
        assert score1.faithfulness >= 0.9
        assert len(score1.hallucinated_citations) == 0

        # 2. Correctly abstained
        q_abstained = GoldenQuery(
            id=2,
            query_text="Quantum physics query",
            expected_category="Unclassifiable",
            expected_status="abstained",
            mandatory_citations=[],
            expected_abs_flag=False,
        )
        resp_abstained = QueryResponse(
            status="abstained",
            category="Unclassifiable",
            jurisdiction="India",
            answer=None,
            citations=[],
            abs_flag=False,
            abstention_message="Out of scope query.",
        )
        score2 = await judge.evaluate(q_abstained, resp_abstained)
        assert score2.passed is True
        assert score2.abstention_precision == 1.0

        # 3. Failed abstention (answered out-of-scope query)
        resp_bad_answered = QueryResponse(
            status="answered",
            category="Unclassifiable",
            jurisdiction="India",
            answer="Quantum entanglement works via wavefunctions.",
            citations=[],
            abs_flag=False,
        )
        score3 = await judge.evaluate(q_abstained, resp_bad_answered)
        assert score3.passed is False
        assert score3.abstention_precision == 0.0

    asyncio.run(_test())


def test_compute_metrics_and_markdown_report():
    """Verify metrics calculation and markdown formatting including hallucination alert."""
    result = EvaluationResult(
        id=1,
        query_text="Test query",
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
        confidence_score=0.95,
        grounding_score=0.98,
        latency_ms=100.0,
        passed=True,
        judge_score=JudgeScore(
            faithfulness=0.95,
            answer_relevance=0.90,
            abstention_precision=1.0,
            hallucinated_citations=[],
            reasoning="Valid ground truth citation",
            passed=True,
        ),
    )

    report = compute_metrics([result], dataset_path="test_dataset.json")
    assert report.summary.total_queries == 1
    assert report.summary.passed_queries == 1
    assert report.summary.overall_pass_rate == 100.0
    assert report.summary.p50_latency_ms == 100.0
    assert report.summary.avg_faithfulness == 0.95

    md = format_markdown_report(report)
    assert "# IP-SAKTI Sahayak — Evaluation Benchmark Report" in md
    assert "Overall Benchmark Pass Rate" in md
    assert "LLM-as-a-Judge Quality Metrics" in md


def test_cli_evaluate_end_to_end(tmp_path, monkeypatch):
    """Verify scripts/evaluate.py runs end-to-end with mock flags and outputs valid reports."""

    async def _test():
        dataset_file = tmp_path / "sample_golden.json"
        output_json = tmp_path / "eval_out.json"
        output_md = tmp_path / "eval_out.md"

        sample_data = [
            {
                "id": 1,
                "query_text": "Can Triphala churna be patented in India?",
                "expected_category": "Classical Ayurveda",
                "expected_status": "answered",
                "mandatory_citations": ["Section 3(p)"],
                "expected_abs_flag": False,
                "description": "Classical test query",
            },
            {
                "id": 2,
                "query_text": "How do rocket engines work?",
                "expected_category": "Unclassifiable",
                "expected_status": "abstained",
                "mandatory_citations": [],
                "expected_abs_flag": False,
                "description": "Out of corpus test query",
            },
        ]
        with open(dataset_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)

        test_argv = [
            "evaluate.py",
            "--dataset",
            str(dataset_file),
            "--output",
            str(output_json),
            "--output-md",
            str(output_md),
            "--concurrency",
            "2",
            "--rate-limit-delay",
            "0.0",
            "--mock-pipeline",
            "--with-judge",
            "--mock-judge",
            "--min-pass-rate",
            "50.0",
        ]
        monkeypatch.setattr("sys.argv", test_argv)

        exit_code = await main_async()
        assert exit_code == 0
        assert output_json.exists()
        assert output_md.exists()

        with open(output_json, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        assert report_data["summary"]["total_queries"] == 2
        assert report_data["summary"]["overall_pass_rate"] == 100.0

        with open(output_md, "r", encoding="utf-8") as f:
            md_text = f.read()
        assert "# IP-SAKTI Sahayak — Evaluation Benchmark Report" in md_text

    asyncio.run(_test())
