import asyncio
import logging
import time

from src.config import config
from src.models.response import Citation, QueryResponse
from src.pipeline.abs_tkdl_checker import ABSChecker, ABSCheckerOutput
from src.pipeline.answer_generator import AnswerGenerator
from src.pipeline.bilingual import BilingualNormalizer
from src.pipeline.classifier import Classifier
from src.pipeline.confidence_gate import ConfidenceGate, ConfidenceGateOutput
from src.pipeline.jurisdiction_router import JurisdictionRouter
from src.pipeline.retriever import Retriever
from src.pipeline.verifier import GroundingVerifier
from src.privacy.pii_strip import log_query, strip_pii

logger = logging.getLogger("ip_sakti.pipeline.orchestrator")


class PipelineOrchestrator:
    """Orchestrates the end-to-end execution of the IP Sakti Sahayak RAG pipeline."""

    def __init__(
        self,
        classifier: Classifier | None = None,
        jurisdiction_router: JurisdictionRouter | None = None,
        retriever: Retriever | None = None,
        abs_checker: ABSChecker | None = None,
        confidence_gate: ConfidenceGate | None = None,
        answer_generator: AnswerGenerator | None = None,
        verifier: GroundingVerifier | None = None,
    ) -> None:
        """Initialize pipeline components with optional dependency injection."""
        self.classifier = classifier or Classifier()
        self.jurisdiction_router = jurisdiction_router or JurisdictionRouter()
        self.retriever = retriever or Retriever()
        self.abs_checker = abs_checker or ABSChecker()
        self.confidence_gate = confidence_gate or ConfidenceGate()
        self.answer_generator = answer_generator or AnswerGenerator()
        self.verifier = verifier or GroundingVerifier()

    async def run_pipeline(
        self,
        query_text: str,
        session_id: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> QueryResponse:
        """Execute the full pipeline asynchronously for an incoming user query.

        Execution flow:
        1. PII Stripping (DPDP Act compliance)
        2. Category Classification
        3. Jurisdiction Routing
        4. Vector Retrieval & ABS/TKDL Prior Art Check (Parallelized via asyncio.gather)
        5. Anti-Hallucination Confidence Gate
        6. Citation-Grounded Answer Generation vs Abstention
        7. Structured Privacy Audit Logging
        8. Response Assembly & Latency Calculation

        Args:
            query_text: Raw query text submitted by the user.
            session_id: Anonymous session identifier.

        Returns:
            QueryResponse containing the final answer or abstention, citations,
            and verification metadata.
        """
        start_time = time.perf_counter()
        short_id = session_id[:8] if session_id else "anon"
        preview_text = query_text[:60] + "..." if len(query_text) > 60 else query_text

        logger.info("--> [%s] Processing query: %r", short_id, preview_text)

        # 1. PII Stripping
        cleaned_query = (
            strip_pii(query_text) if config.PII_STRIP_ENABLED else query_text
        )
        if config.PII_STRIP_ENABLED and cleaned_query != query_text:
            logger.info(
                "[PII-GUARD] [%s] Redacted sensitive personal entities", short_id
            )

        # 2. Classification
        category_out = await asyncio.to_thread(self.classifier.classify, cleaned_query)
        logger.info(
            "[CLASSIFIER] [%s] Category: '%s' (confidence: %.1f%%)",
            short_id,
            category_out.category,
            category_out.confidence * 100,
        )

        # 3. Jurisdiction Routing
        routed_out = self.jurisdiction_router.route(
            cleaned_query, classifier_output=category_out
        )

        if routed_out.status == "out_of_scope_international":
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                "[ROUTER] [%s] Out of scope (Jurisdiction: %s, latency: %dms)",
                short_id,
                routed_out.jurisdiction,
                latency_ms,
            )
            return QueryResponse(
                status="abstained",
                category=category_out.category,
                jurisdiction=routed_out.jurisdiction,
                answer=None,
                citations=[],
                abs_flag=False,
                abs_detail=None,
                tkdl_flag=False,
                tkdl_detail=None,
                confidence_score=0.0,
                abstention_message=routed_out.message or config.ABSTENTION_MESSAGE,
                disclaimer=config.DISCLAIMER_TEXT,
                response_time_ms=latency_ms,
            )

        # 4. Retrieval & ABS / TKDL Prior Art Check
        if category_out.category == "Conversational":
            logger.info(
                "[CONVERSATIONAL] [%s] Direct conversational response", short_id
            )
            retrieved_chunks = []
            abs_out = ABSCheckerOutput(abs_flag=False, abs_detail=None)
            gate_out = ConfidenceGateOutput(
                decision="generate", max_score=1.0, chunks=[]
            )

            gen_out = await asyncio.to_thread(
                self.answer_generator.generate_conversational,
                query=cleaned_query,
                conversation_history=conversation_history,
            )

            status = "answered"
            final_answer = gen_out.answer
            response_citations = []
            abstention_msg = None
        else:
            # Bilingual Query Expansion Bridge (if Devanagari Hindi is detected)
            bilingual_res = BilingualNormalizer.expand_query(cleaned_query)
            search_query = (
                bilingual_res.expanded_search_query
                if bilingual_res.is_hindi
                else cleaned_query
            )
            if bilingual_res.is_hindi:
                logger.info(
                    "[BILINGUAL-BRIDGE] [%s] Hindi detected. Expanded search terms: %s",
                    short_id,
                    bilingual_res.matched_terms,
                )

            # Parallel execution of external checks
            try:
                retrieved_chunks, abs_out = await asyncio.gather(
                    asyncio.to_thread(self.retriever.retrieve, search_query),
                    asyncio.to_thread(self.abs_checker.check, search_query),
                )
            except Exception as e:
                logger.error("[HYBRID-SEARCH] [%s] External search failure: %s", short_id, e)
                retrieved_chunks = []
                abs_out = ABSCheckerOutput(abs_flag=False, abs_detail=None)

            logger.info(
                "[HYBRID-SEARCH] [%s] Retrieved %d chunks | ABS: %s | TKDL: %s",
                short_id,
                len(retrieved_chunks),
                abs_out.abs_flag,
                abs_out.tkdl_flag,
            )

            # 5. Confidence Gate (Anti-Hallucination)
            gate_out = self.confidence_gate.evaluate(retrieved_chunks)

            # 6. Answer Generation vs Abstention
            if (
                gate_out.decision == "generate"
                and category_out.category != "Unclassifiable"
            ):
                logger.info(
                    "[CONF-GATE] [%s] Decision: PASSED (score: %.3f >= %.2f threshold)",
                    short_id,
                    gate_out.max_score,
                    self.confidence_gate.threshold,
                )
                gen_out = await asyncio.to_thread(
                    self.answer_generator.generate,
                    query=cleaned_query,
                    chunks=gate_out.chunks,
                    product_category=category_out.category,
                    abs_flag=abs_out.abs_flag,
                    conversation_history=conversation_history,
                )

                # Map generator citations to API response citation models
                response_citations = [
                    Citation(
                        doc_id=c.doc_id,
                        source_url=c.source_url,
                        doc_type=c.doc_type,
                        section=c.section,
                        date_retrieved=c.date_retrieved,
                    )
                    for c in gen_out.citations
                ]

                # Deterministic Grounding Verification (VERIFY step)
                verify_out = self.verifier.verify(
                    answer=gen_out.answer,
                    citations=response_citations,
                    retrieved_chunks=gate_out.chunks,
                )
                logger.info(
                    "[VERIFY] [%s] Grounding check: %s (score=%.2f, status=%s)",
                    short_id,
                    verify_out.is_verified,
                    verify_out.grounding_score,
                    verify_out.status,
                )

                if not verify_out.is_verified:
                    logger.warning(
                        "[VERIFY-REJECT] [%s] Grounding verification failed: %s. Abstaining.",
                        short_id,
                        verify_out.audit_trail,
                    )
                    status = "abstained"
                    final_answer = None
                    response_citations = []
                    abstention_msg = config.ABSTENTION_MESSAGE
                    grounding_score = verify_out.grounding_score
                    verification_status = verify_out.status
                else:
                    status = "answered" if response_citations else "abstained"
                    final_answer = gen_out.answer if status == "answered" else None
                    abstention_msg = (
                        None
                        if status == "answered"
                        else (gen_out.answer or config.ABSTENTION_MESSAGE)
                    )
                    grounding_score = verify_out.grounding_score
                    verification_status = verify_out.status
            else:
                status = "abstained"
                final_answer = None
                response_citations = []
                grounding_score = 1.0
                verification_status = "verified"
                abstention_msg = await asyncio.to_thread(
                    self.answer_generator.generate_refusal,
                    query=cleaned_query,
                )

        # Extract retrieved document IDs for audit logging
        retrieved_doc_ids = []
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            doc_id = chunk.get("doc_id") or meta.get("doc_id")
            if doc_id and doc_id not in retrieved_doc_ids:
                retrieved_doc_ids.append(doc_id)

        # 7. Privacy Audit Logging (runs with stripped query)
        await asyncio.to_thread(
            log_query,
            session_id=session_id,
            query_text=query_text,
            category=category_out.category,
            retrieved_doc_ids=retrieved_doc_ids,
            confidence_score=gate_out.max_score,
            decision=gate_out.decision,
        )

        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 0)
        logger.info(
            "[PIPELINE-COMPLETE] [%s] Status: %s | Citations: %d | Grounding: %.2f | Latency: %dms",
            short_id,
            status,
            len(response_citations),
            grounding_score if "grounding_score" in locals() else 1.0,
            elapsed_ms,
        )

        return QueryResponse(
            status=status,
            category=category_out.category,
            jurisdiction=routed_out.jurisdiction,
            answer=final_answer,
            citations=response_citations,
            abs_flag=abs_out.abs_flag,
            abs_detail=abs_out.abs_detail,
            tkdl_flag=abs_out.tkdl_flag,
            tkdl_detail=abs_out.tkdl_detail,
            confidence_score=gate_out.max_score,
            grounding_score=grounding_score if "grounding_score" in locals() else 1.0,
            verification_status=(
                verification_status if "verification_status" in locals() else "verified"
            ),
            abstention_message=abstention_msg,
            disclaimer=config.DISCLAIMER_TEXT,
            response_time_ms=elapsed_ms,
        )


async def run_pipeline(
    query_text: str | None = None,
    session_id: str = "",
    query: str | None = None,
    conversation_history: list[dict[str, str]] | None = None,
) -> QueryResponse:
    """Convenience functional wrapper for executing the RAG pipeline asynchronously."""
    target_query = query_text if query_text is not None else (query or "")
    orchestrator = PipelineOrchestrator()
    return await orchestrator.run_pipeline(
        query_text=target_query,
        session_id=session_id,
        conversation_history=conversation_history,
    )
