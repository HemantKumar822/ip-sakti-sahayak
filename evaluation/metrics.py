"""Statistical aggregation and report formatting metrics for the evaluation framework."""

from datetime import datetime, timezone

import numpy as np

from evaluation.schemas import (
    EvaluationReport,
    EvaluationResult,
    MetricSummary,
)


def compute_metrics(
    results: list[EvaluationResult],
    dataset_path: str = "evaluation/data/golden_expanded.json",
) -> EvaluationReport:
    """Aggregates execution results into statistical metrics and generates an EvaluationReport."""
    total_queries = len(results)
    if total_queries == 0:
        empty_summary = MetricSummary(
            total_queries=0,
            passed_queries=0,
            failed_queries=0,
            overall_pass_rate=0.0,
            status_accuracy=0.0,
            category_accuracy=0.0,
            abs_accuracy=0.0,
            mandatory_citation_recall=0.0,
            avg_latency_ms=0.0,
            p50_latency_ms=0.0,
            p90_latency_ms=0.0,
            p99_latency_ms=0.0,
            category_distribution={},
            hallucination_violations_count=0,
        )
        return EvaluationReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            dataset_path=dataset_path,
            summary=empty_summary,
            results=[],
        )

    passed_count = sum(1 for r in results if r.passed)
    status_matches = sum(1 for r in results if r.status_match)
    category_matches = sum(1 for r in results if r.category_match)
    abs_matches = sum(1 for r in results if r.abs_match)
    citation_matches = sum(1 for r in results if r.mandatory_citations_present)

    latencies = [r.latency_ms for r in results]
    avg_latency = float(np.mean(latencies))
    p50_latency = float(np.percentile(latencies, 50))
    p90_latency = float(np.percentile(latencies, 90))
    p99_latency = float(np.percentile(latencies, 99))

    category_dist: dict[str, int] = {}
    for r in results:
        category_dist[r.expected_category] = (
            category_dist.get(r.expected_category, 0) + 1
        )

    # Calculate judge metrics if present
    judge_scores = [r.judge_score for r in results if r.judge_score is not None]
    avg_faithfulness = (
        float(np.mean([js.faithfulness for js in judge_scores]))
        if judge_scores
        else None
    )
    avg_relevance = (
        float(np.mean([js.answer_relevance for js in judge_scores]))
        if judge_scores
        else None
    )
    avg_abstention = (
        float(np.mean([js.abstention_precision for js in judge_scores]))
        if judge_scores
        else None
    )

    hallucinations_count = sum(
        len(js.hallucinated_citations)
        for js in judge_scores
        if js.hallucinated_citations
    )

    summary = MetricSummary(
        total_queries=total_queries,
        passed_queries=passed_count,
        failed_queries=total_queries - passed_count,
        overall_pass_rate=round((passed_count / total_queries) * 100, 2),
        status_accuracy=round((status_matches / total_queries) * 100, 2),
        category_accuracy=round((category_matches / total_queries) * 100, 2),
        abs_accuracy=round((abs_matches / total_queries) * 100, 2),
        mandatory_citation_recall=round((citation_matches / total_queries) * 100, 2),
        avg_latency_ms=round(avg_latency, 2),
        p50_latency_ms=round(p50_latency, 2),
        p90_latency_ms=round(p90_latency, 2),
        p99_latency_ms=round(p99_latency, 2),
        category_distribution=category_dist,
        avg_faithfulness=(
            round(avg_faithfulness, 3) if avg_faithfulness is not None else None
        ),
        avg_answer_relevance=(
            round(avg_relevance, 3) if avg_relevance is not None else None
        ),
        avg_abstention_precision=(
            round(avg_abstention, 3) if avg_abstention is not None else None
        ),
        hallucination_violations_count=hallucinations_count,
    )

    return EvaluationReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        dataset_path=dataset_path,
        summary=summary,
        results=results,
    )


def format_markdown_report(report: EvaluationReport) -> str:
    """Generates a structured GitHub Flavored Markdown report for the evaluation run."""
    s = report.summary
    lines = [
        "# IP-SAKTI Sahayak — Evaluation Benchmark Report",
        f"**Timestamp:** `{report.timestamp}`  ",
        f"**Dataset:** `{report.dataset_path}`  ",
        f"**Total Queries Evaluated:** `{s.total_queries}`  ",
        "",
        "## Executive Summary",
        "",
        "| Metric | Result | Target | Status |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Overall Benchmark Pass Rate** | `{s.overall_pass_rate}%` ({s.passed_queries}/{s.total_queries}) | `>= 80.0%` | {'✅ PASS' if s.overall_pass_rate >= 80 else '❌ FAIL'} |",
        f"| **Status / Gating Accuracy** | `{s.status_accuracy}%` | `>= 90.0%` | {'✅ PASS' if s.status_accuracy >= 90 else '⚠️ WARN'} |",
        f"| **Category Accuracy** | `{s.category_accuracy}%` | `>= 85.0%` | {'✅ PASS' if s.category_accuracy >= 85 else '⚠️ WARN'} |",
        f"| **ABS Flag Accuracy** | `{s.abs_accuracy}%` | `>= 95.0%` | {'✅ PASS' if s.abs_accuracy >= 95 else '⚠️ WARN'} |",
        f"| **Mandatory Citation Recall** | `{s.mandatory_citation_recall}%` | `>= 85.0%` | {'✅ PASS' if s.mandatory_citation_recall >= 85 else '⚠️ WARN'} |",
        "",
        "## Latency Benchmarks",
        "",
        "| Percentile | Latency (ms) | Target |",
        "| :--- | :--- | :--- |",
        f"| **Average Latency** | `{s.avg_latency_ms} ms` | `< 2500 ms` |",
        f"| **p50 (Median)** | `{s.p50_latency_ms} ms` | `< 2000 ms` |",
        f"| **p90** | `{s.p90_latency_ms} ms` | `< 4000 ms` |",
        f"| **p99** | `{s.p99_latency_ms} ms` | `< 6000 ms` |",
        "",
    ]

    if s.avg_faithfulness is not None:
        lines.extend(
            [
                "## LLM-as-a-Judge Quality Metrics",
                "",
                "| Criterion | Average Score | Description |",
                "| :--- | :--- | :--- |",
                f"| **Faithfulness** | `{s.avg_faithfulness}` / 1.00 | Citation grounding and factual adherence |",
                f"| **Answer Relevance** | `{s.avg_answer_relevance}` / 1.00 | Direct responsiveness to IP query |",
                f"| **Abstention Precision** | `{s.avg_abstention_precision}` / 1.00 | Precision in refusing out-of-scope queries |",
                f"| **Hallucination Violations** | `{s.hallucination_violations_count}` | Fabricated citations or statutes |",
                "",
            ]
        )

    lines.extend(
        [
            "## Category Distribution",
            "",
            "| Category | Count | Proportion |",
            "| :--- | :--- | :--- |",
        ]
    )
    for cat, count in s.category_distribution.items():
        prop = round((count / s.total_queries) * 100, 1)
        lines.append(f"| {cat} | {count} | {prop}% |")
    lines.append("")

    lines.extend(
        [
            "## Query Level Breakdown",
            "",
            "| ID | Query | Expected Status | Actual Status | ABS (Exp/Act) | Latency | Pass/Fail |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )
    for r in report.results:
        preview = r.query_text[:50] + "..." if len(r.query_text) > 50 else r.query_text
        abs_str = (
            f"{'T' if r.expected_abs_flag else 'F'}/{'T' if r.actual_abs_flag else 'F'}"
        )
        verdict = "✅ PASS" if r.passed else "❌ FAIL"
        lines.append(
            f"| {r.id} | {preview} | `{r.expected_status}` | `{r.actual_status}` | `{abs_str}` | `{r.latency_ms} ms` | {verdict} |"
        )

    # If there are hallucination violations, list them prominently
    hallucinated_entries = [
        r
        for r in report.results
        if r.judge_score and r.judge_score.hallucinated_citations
    ]
    if hallucinated_entries:
        lines.extend(
            [
                "",
                "## ⚠️ Hallucination Violations Detected",
                "",
                "> [!CAUTION]",
                f"> Detected {len(hallucinated_entries)} query response(s) containing fabricated statutes or citations!",
                "",
            ]
        )
        for r in hallucinated_entries:
            lines.append(f"- **Query #{r.id}**: {r.query_text}")
            lines.append(
                f"  - **Hallucinated citations**: `{r.judge_score.hallucinated_citations}`"
            )
            lines.append(f"  - **Reasoning**: {r.judge_score.reasoning}")

    return "\n".join(lines) + "\n"
