# ruff: noqa: BLE001
"""Asynchronous execution runner with concurrency throttling for pipeline benchmarking."""

import asyncio
import logging
import time
from typing import Any

from evaluation.schemas import EvaluationResult, GoldenQuery, JudgeScore
from src.models.response import Citation, QueryResponse
from src.pipeline.orchestrator import PipelineOrchestrator

logger = logging.getLogger("ip_sakti.evaluation.runner")


class EvaluationRunner:
    """Batch execution engine for running benchmark datasets against the RAG pipeline."""

    def __init__(
        self,
        orchestrator: PipelineOrchestrator | None = None,
        concurrency: int = 2,
        rate_limit_delay: float = 1.0,
        mock_pipeline: bool = False,
        judge: Any | None = None,
    ) -> None:
        """Initializes the EvaluationRunner.

        Args:
            orchestrator: PipelineOrchestrator instance (lazily initialized if None and mock_pipeline=False).
            concurrency: Maximum concurrent asynchronous query workers.
            rate_limit_delay: Delay in seconds between tasks to adhere to API rate limits.
            mock_pipeline: If True, uses deterministic in-memory simulated responses without external API calls.
            judge: Optional LLM-as-a-judge instance for answer quality and hallucination scoring.
        """
        self.mock_pipeline = mock_pipeline
        self.orchestrator = (
            orchestrator if (orchestrator or mock_pipeline) else PipelineOrchestrator()
        )
        self.concurrency = max(1, concurrency)
        self.rate_limit_delay = rate_limit_delay
        self.judge = judge
        self._semaphore = asyncio.Semaphore(self.concurrency)

    async def _mock_run(self, query: GoldenQuery) -> QueryResponse:
        """Generates a deterministic simulated QueryResponse for hermetic testing."""
        await asyncio.sleep(0.01)  # Simulate non-blocking execution
        if query.expected_status == "abstained":
            return QueryResponse(
                status="abstained",
                category=query.expected_category,
                jurisdiction="India",
                answer=None,
                citations=[],
                abs_flag=False,
                confidence_score=0.0,
                grounding_score=1.0,
                verification_status="verified",
                abstention_message="The query is outside the scope of Indian IP and traditional knowledge.",
                response_time_ms=10,
            )

        # Build citations matching mandatory citations if present
        mock_citations = []
        for idx, cit in enumerate(query.mandatory_citations):
            mock_citations.append(
                Citation(
                    doc_id=f"doc-statute-{idx + 1}",
                    source_url="https://ipindia.gov.in",
                    doc_type="Statute",
                    section=cit,
                    date_retrieved="2026-09-04",
                )
            )

        if not mock_citations:
            mock_citations.append(
                Citation(
                    doc_id="doc-general-01",
                    source_url="https://ipindia.gov.in",
                    doc_type="Statute",
                    section="Patents Act 1970",
                    date_retrieved="2026-09-04",
                )
            )

        citations_text = ", ".join(query.mandatory_citations)
        simulated_answer = (
            f"Regarding {query.query_text}, under Indian law, relevant provisions include: {citations_text}."
            if citations_text
            else f"Analysis for: {query.query_text}."
        )

        return QueryResponse(
            status="answered",
            category=query.expected_category,
            jurisdiction="India",
            answer=simulated_answer,
            citations=mock_citations,
            abs_flag=query.expected_abs_flag,
            confidence_score=0.92,
            grounding_score=0.95,
            verification_status="verified",
            abstention_message=None,
            response_time_ms=15,
        )

    async def run_single_query(self, query: GoldenQuery) -> EvaluationResult:
        """Executes a single benchmark query with timing and validation."""
        start_time = time.perf_counter()
        session_id = f"benchmark-{query.id}"
        error_msg = None

        try:
            if self.mock_pipeline:
                resp = await self._mock_run(query)
            else:
                assert self.orchestrator is not None
                resp = await self.orchestrator.run_pipeline(
                    query_text=query.query_text,
                    session_id=session_id,
                )
        except Exception as e:
            logger.exception(
                "Benchmark query #%s failed with unexpected exception",
                query.id,
            )
            error_msg = str(e)
            resp = QueryResponse(
                status="error",
                category="Unknown",
                jurisdiction="Unknown",
                answer=None,
                citations=[],
                abs_flag=False,
                confidence_score=0.0,
                grounding_score=0.0,
                verification_status="failed",
                abstention_message=f"Pipeline error: {e}",
                response_time_ms=int((time.perf_counter() - start_time) * 1000),
            )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Collect citation references from response citations and answer text
        actual_citations_list: list[str] = []
        for c in resp.citations:
            if c.section:
                actual_citations_list.append(c.section)
            if c.doc_id:
                actual_citations_list.append(c.doc_id)

        answer_text = resp.answer or ""

        # Check mandatory citations
        missing_citations = []
        found_citations = []
        for mandatory in query.mandatory_citations:
            # Check if mandatory citation is present in citations or mentioned in answer
            in_citations = any(
                mandatory.lower() in ac.lower() for ac in actual_citations_list
            )
            in_answer = mandatory.lower() in answer_text.lower()
            if in_citations or in_answer:
                found_citations.append(mandatory)
            else:
                missing_citations.append(mandatory)

        status_match = resp.status == query.expected_status
        category_match = resp.category == query.expected_category or (
            query.expected_status == "abstained" and resp.status == "abstained"
        )
        abs_match = resp.abs_flag == query.expected_abs_flag
        mandatory_present = len(missing_citations) == 0

        # Base pass condition
        passed = status_match and abs_match and mandatory_present and error_msg is None

        # LLM Judge evaluation if configured
        judge_score: JudgeScore | None = None
        if self.judge is not None and error_msg is None:
            try:
                judge_score = await self.judge.evaluate(query=query, response=resp)
                if not judge_score.passed or judge_score.hallucinated_citations:
                    passed = False
            except Exception as je:
                logger.warning(
                    "Judge evaluation failed for query #%s: %s", query.id, je
                )

        return EvaluationResult(
            id=query.id,
            query_text=query.query_text,
            expected_status=query.expected_status,
            actual_status=resp.status,
            expected_category=query.expected_category,
            actual_category=resp.category,
            expected_abs_flag=query.expected_abs_flag,
            actual_abs_flag=resp.abs_flag,
            mandatory_citations=query.mandatory_citations,
            actual_citations=actual_citations_list,
            citations_found=found_citations,
            status_match=status_match,
            category_match=category_match,
            abs_match=abs_match,
            mandatory_citations_present=mandatory_present,
            confidence_score=resp.confidence_score or 0.0,
            grounding_score=resp.grounding_score or 0.0,
            latency_ms=elapsed_ms,
            passed=passed,
            error=error_msg,
            judge_score=judge_score,
        )

    async def _worker(
        self, query: GoldenQuery, results: list[EvaluationResult]
    ) -> None:
        """Worker task governed by concurrency semaphore and rate-limiting."""
        async with self._semaphore:
            result = await self.run_single_query(query)
            results.append(result)
            if self.rate_limit_delay > 0:
                await asyncio.sleep(self.rate_limit_delay)

    async def run_benchmark(self, queries: list[GoldenQuery]) -> list[EvaluationResult]:
        """Runs the benchmark suite across all provided queries concurrently."""
        results: list[EvaluationResult] = []
        tasks = [self._worker(q, results) for q in queries]
        await asyncio.gather(*tasks)
        # Sort results by ID for deterministic ordering
        results.sort(key=lambda r: int(r.id) if str(r.id).isdigit() else str(r.id))
        return results
