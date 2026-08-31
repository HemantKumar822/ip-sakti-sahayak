import logging
import time

from fastapi import APIRouter, HTTPException

from src.config import config
from src.models.request import QueryRequest
from src.models.response import Citation, QueryResponse
from src.pipeline.abs_tkdl_checker import ABSChecker
from src.pipeline.answer_generator import AnswerGenerator
from src.pipeline.classifier import Classifier
from src.pipeline.confidence_gate import ConfidenceGate
from src.pipeline.jurisdiction_router import JurisdictionRouter
from src.pipeline.retriever import Retriever
from src.privacy.pii_strip import log_query, strip_pii

logger = logging.getLogger("ip_sakti.api.routes")
router = APIRouter()


@router.get("/health", summary="Health check", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify that the API server is alive."""
    return {"status": "ok"}


@router.post(
    "/api/v1/query",
    response_model=QueryResponse,
    summary="Submit IPR query",
    tags=["Query"],
)
async def process_query(request: QueryRequest) -> QueryResponse:
    """Process an intellectual property query through the RAG pipeline."""
    start_time = time.perf_counter()

    try:
        # 1. PII Stripping
        cleaned_query = (
            strip_pii(request.query_text)
            if getattr(config, "PII_STRIP_ENABLED", True)
            else request.query_text
        )

        # 2. Classification
        classifier = Classifier()
        category_out = classifier.classify(cleaned_query)

        # 3. Jurisdiction Routing
        jurisdiction_router = JurisdictionRouter()
        routed_out = jurisdiction_router.route(
            cleaned_query, classifier_output=category_out
        )

        # 4. Retrieval
        retriever = Retriever()
        retrieved_chunks = retriever.retrieve(cleaned_query)

        # 5. ABS / TKDL Prior Art Check
        abs_checker = ABSChecker()
        abs_out = abs_checker.check(cleaned_query)

        # 6. Confidence Gate (Anti-Hallucination)
        confidence_gate = ConfidenceGate()
        gate_out = confidence_gate.evaluate(retrieved_chunks)

        # 7. Answer Generation vs Abstention
        if gate_out.decision == "generate":
            generator = AnswerGenerator()
            gen_out = generator.generate(
                query=cleaned_query,
                chunks=gate_out.chunks,
                product_category=category_out.category,
                abs_flag=abs_out.abs_flag,
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

            status = (
                "answered"
                if response_citations
                or (gen_out.answer and gen_out.answer != config.ABSTENTION_MESSAGE)
                else "abstained"
            )
            final_answer = gen_out.answer if status == "answered" else None
            abstention_msg = (
                None
                if status == "answered"
                else (gen_out.answer or config.ABSTENTION_MESSAGE)
            )
        else:
            status = "abstained"
            final_answer = None
            response_citations = []
            abstention_msg = config.ABSTENTION_MESSAGE

        # Extract retrieved document IDs for audit logging
        retrieved_doc_ids = []
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            doc_id = chunk.get("doc_id") or meta.get("doc_id")
            if doc_id and doc_id not in retrieved_doc_ids:
                retrieved_doc_ids.append(doc_id)

        # 8. Privacy Audit Logging (runs with stripped query)
        log_query(
            session_id=request.session_id,
            query_text=request.query_text,
            category=category_out.category,
            retrieved_doc_ids=retrieved_doc_ids,
            confidence_score=gate_out.max_score,
            decision=gate_out.decision,
        )

        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 0)

        return QueryResponse(
            status=status,
            category=category_out.category,
            jurisdiction=routed_out.jurisdiction,
            answer=final_answer,
            citations=response_citations,
            abs_flag=abs_out.abs_flag,
            abs_detail=abs_out.abs_detail,
            confidence_score=gate_out.max_score,
            abstention_message=abstention_msg,
            disclaimer=config.DISCLAIMER_TEXT,
            response_time_ms=elapsed_ms,
        )

    except Exception as exc:
        logger.error("Error processing query in pipeline: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        ) from exc
