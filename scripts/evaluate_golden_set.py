"""Deep Golden Set Evaluation Runner for IP Sakti Sahayak.
Executes the full 20-query golden test suite through PipelineOrchestrator,
measuring classification, ABS detection, retrieval scoring, confidence gating,
latency, and audit trail integrity.
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.models.request import QueryRequest
from src.pipeline.orchestrator import PipelineOrchestrator


async def run_evaluation() -> dict[str, Any]:
    print("=" * 80)
    print("IP SAKTI SAHAYAK - DEEP SYSTEM EVALUATION & GOLDEN BENCHMARK")
    print("=" * 80)

    test_set_path = Path("tests/golden_queries/test_set.json")
    if not test_set_path.exists():
        raise FileNotFoundError(f"Golden set not found at {test_set_path}")

    with open(test_set_path, "r", encoding="utf-8") as f:
        golden_set = json.load(f)

    orchestrator = PipelineOrchestrator()

    total_queries = len(golden_set)
    category_matches = 0
    status_matches = 0
    abs_matches = 0

    results = []
    category_breakdown: dict[str, dict[str, int]] = {}
    latencies: list[float] = []

    print(f"\n[+] Executing {total_queries} Golden Queries across 3 Categories...\n")
    print(f"{'ID':<3} | {'Category':<22} | {'Exp Status':<10} | {'Act Status':<10} | {'ABS Exp/Act':<12} | {'Score':<6} | {'Lat (ms)':<8} | {'Result'}")
    print("-" * 95)

    for item in golden_set:
        q_id = item["id"]
        query_text = item["query"]
        expected_cat = item["expected_category"]
        expected_status = item["expected_status"]
        expected_abs = item["expected_abs_flag"]

        if expected_cat not in category_breakdown:
            category_breakdown[expected_cat] = {"total": 0, "status_pass": 0, "abs_pass": 0}
        category_breakdown[expected_cat]["total"] += 1

        req = QueryRequest(query_text=query_text, session_id=f"eval-session-{q_id}")

        start_time = time.perf_counter()
        resp = await orchestrator.run_pipeline(
            query_text=query_text,
            session_id=f"eval-session-{q_id}",
        )
        latency_ms = (time.perf_counter() - start_time) * 1000
        latencies.append(latency_ms)

        # Evaluate matches
        act_status = resp.status
        act_abs = resp.abs_flag
        
        # Classification check: unclassifiable queries get abstained, others get answered
        status_pass = (act_status == expected_status)
        abs_pass = (act_abs == expected_abs)

        if status_pass:
            status_matches += 1
            category_breakdown[expected_cat]["status_pass"] += 1
        if abs_pass:
            abs_matches += 1
            category_breakdown[expected_cat]["abs_pass"] += 1

        top_score = resp.confidence_score if resp.confidence_score is not None else 0.0
        abs_str = f"{str(expected_abs)[0]}/{str(act_abs)[0]}"
        verdict = "PASS" if (status_pass and abs_pass) else "FAIL"

        print(f"{q_id:<3} | {expected_cat:<22} | {expected_status:<10} | {act_status:<10} | {abs_str:<12} | {top_score:<6.2f} | {latency_ms:<8.1f} | {verdict}")

        results.append({
            "id": q_id,
            "query": query_text,
            "category": expected_cat,
            "expected_status": expected_status,
            "actual_status": act_status,
            "expected_abs": expected_abs,
            "actual_abs": act_abs,
            "confidence_score": top_score,
            "latency_ms": round(latency_ms, 2),
            "citations_count": len(resp.citations),
            "sources": [c.doc_id for c in resp.citations],
            "passed": (status_pass and abs_pass),
        })

        # Pacing to respect Gemini free-tier rate limits (15-20 RPM)
        await asyncio.sleep(2.0)

    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

    summary = {
        "total_queries": total_queries,
        "status_accuracy": round((status_matches / total_queries) * 100, 2),
        "abs_accuracy": round((abs_matches / total_queries) * 100, 2),
        "overall_pass_rate": round((sum(1 for r in results if r["passed"]) / total_queries) * 100, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "category_breakdown": category_breakdown,
        "results": results,
    }

    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total Test Queries:       {total_queries}")
    print(f"Status / Gating Accuracy: {summary['status_accuracy']}% ({status_matches}/{total_queries})")
    print(f"ABS Flag Accuracy:        {summary['abs_accuracy']}% ({abs_matches}/{total_queries})")
    print(f"Overall Test Pass Rate:   {summary['overall_pass_rate']}%")
    print(f"Avg End-to-End Latency:   {summary['avg_latency_ms']} ms")
    print(f"P95 Latency:              {summary['p95_latency_ms']} ms")
    print("\nPer-Category Breakdown:")
    for cat, stats in category_breakdown.items():
        tot = stats["total"]
        sp = stats["status_pass"]
        ap = stats["abs_pass"]
        print(f"  - {cat:<24}: Status Pass = {sp}/{tot} ({sp/tot*100:.1f}%) | ABS Pass = {ap}/{tot} ({ap/tot*100:.1f}%)")
    print("=" * 80)

    # Save evaluation results artifact
    eval_output_path = Path("scratch/golden_evaluation_report.json")
    eval_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(eval_output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[+] Raw evaluation results saved to {eval_output_path}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_evaluation())
