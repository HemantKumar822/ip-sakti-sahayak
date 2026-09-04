#!/usr/bin/env python3
# ruff: noqa: ASYNC230, BLE001
"""Standalone Evaluation CLI Harness for Live Pipeline Benchmarking."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.metrics import compute_metrics, format_markdown_report
from evaluation.runner import EvaluationRunner
from evaluation.schemas import GoldenQuery

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("evaluate_cli")


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments for the evaluation harness."""
    parser = argparse.ArgumentParser(
        description="IP-SAKTI Sahayak Evaluation Benchmark CLI Harness",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="evaluation/data/golden_expanded.json",
        help="Path to the JSON golden dataset to evaluate.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evaluation/reports/eval_run.json",
        help="Path to save the JSON evaluation report artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="evaluation/reports/eval_run.md",
        help="Path to save the Markdown evaluation report artifact.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Maximum concurrent evaluation workers.",
    )
    parser.add_argument(
        "--rate-limit-delay",
        type=float,
        default=1.0,
        help="Delay in seconds between worker queries to respect API rate limits.",
    )
    parser.add_argument(
        "--mock-pipeline",
        action="store_true",
        default=False,
        help="Run against simulated in-memory pipeline without external API calls.",
    )
    parser.add_argument(
        "--with-judge",
        action="store_true",
        default=False,
        help="Enable automated LLM-as-a-judge quality and faithfulness scoring.",
    )
    parser.add_argument(
        "--mock-judge",
        action="store_true",
        default=False,
        help="Simulate judge scoring in-memory without invoking Gemini LLM.",
    )
    parser.add_argument(
        "--min-pass-rate",
        type=float,
        default=70.0,
        help="Minimum overall pass rate percentage required to exit with code 0.",
    )
    parser.add_argument(
        "--fail-on-hallucination",
        action="store_true",
        default=True,
        help="Cause non-zero exit code if any hallucinated citations are flagged by judge.",
    )
    return parser.parse_args()


async def main_async() -> int:
    """Asynchronous entrypoint for the evaluation CLI."""
    args = parse_args()
    dataset_path = Path(args.dataset)

    if not dataset_path.exists():
        logger.error("Dataset not found at: %s", dataset_path)
        return 1

    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        queries = [GoldenQuery.model_validate(item) for item in raw_data]
    except Exception as e:
        logger.error("Failed to parse dataset %s: %s", dataset_path, e)
        return 1

    logger.info("Loaded %d benchmark queries from %s", len(queries), dataset_path)

    judge_instance = None
    if args.with_judge:
        from evaluation.judge import EvaluationJudge

        judge_instance = EvaluationJudge(mock=args.mock_judge)
        logger.info(
            "LLM-as-a-judge enabled (mode: %s)",
            "MOCK" if args.mock_judge else "LIVE",
        )

    runner = EvaluationRunner(
        concurrency=args.concurrency,
        rate_limit_delay=args.rate_limit_delay,
        mock_pipeline=args.mock_pipeline,
        judge=judge_instance,
    )

    logger.info(
        "Starting benchmark execution (concurrency: %d, pipeline: %s)...",
        args.concurrency,
        "MOCK" if args.mock_pipeline else "LIVE",
    )
    results = await runner.run_benchmark(queries)

    # Compute aggregate metrics
    report = compute_metrics(results, dataset_path=str(dataset_path))
    md_content = format_markdown_report(report)

    # Write output files
    output_json_path = Path(args.output)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))
    logger.info("Saved JSON report to: %s", output_json_path)

    output_md_path = Path(args.output_md)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info("Saved Markdown report to: %s", output_md_path)

    # Print summary table to console
    print("\n" + "=" * 80)
    print("BENCHMARK EXECUTION SUMMARY")
    print("=" * 80)
    s = report.summary
    print(f"Total Queries:         {s.total_queries}")
    print(
        f"Overall Pass Rate:     {s.overall_pass_rate}% ({s.passed_queries}/{s.total_queries})"
    )
    print(f"Status Accuracy:       {s.status_accuracy}%")
    print(f"ABS Accuracy:          {s.abs_accuracy}%")
    print(f"Mandatory Citations:   {s.mandatory_citation_recall}%")
    print(
        f"Avg Latency:           {s.avg_latency_ms} ms (p50: {s.p50_latency_ms} ms, p90: {s.p90_latency_ms} ms)"
    )
    if s.avg_faithfulness is not None:
        print(f"Faithfulness Score:    {s.avg_faithfulness} / 1.00")
        print(f"Answer Relevance:      {s.avg_answer_relevance} / 1.00")
        print(f"Abstention Precision:  {s.avg_abstention_precision} / 1.00")
        print(f"Hallucination Count:   {s.hallucination_violations_count}")
    print("=" * 80 + "\n")

    # Evaluate CI exit gates
    if args.fail_on_hallucination and s.hallucination_violations_count > 0:
        logger.error(
            "CI FAILURE: Detected %d hallucinated citation violations!",
            s.hallucination_violations_count,
        )
        return 1

    if s.overall_pass_rate < args.min_pass_rate:
        logger.error(
            "CI FAILURE: Overall pass rate %.1f%% below threshold %.1f%%!",
            s.overall_pass_rate,
            args.min_pass_rate,
        )
        return 1

    return 0


def main() -> None:
    """CLI script entrypoint."""
    exit_code = asyncio.run(main_async())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
