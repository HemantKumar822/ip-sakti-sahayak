"""Evaluation package for IP-SAKTI Sahayak benchmark and quality framework."""

from evaluation.judge import EvaluationJudge
from evaluation.metrics import compute_metrics, format_markdown_report
from evaluation.runner import EvaluationRunner
from evaluation.schemas import (
    EvaluationReport,
    EvaluationResult,
    GoldenQuery,
    JudgeScore,
    MetricSummary,
)

__all__ = [
    "EvaluationJudge",
    "EvaluationReport",
    "EvaluationResult",
    "EvaluationRunner",
    "GoldenQuery",
    "JudgeScore",
    "MetricSummary",
    "compute_metrics",
    "format_markdown_report",
]
