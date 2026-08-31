import logging

from fastapi import APIRouter, HTTPException

from src.models.request import QueryRequest
from src.models.response import QueryResponse
from src.pipeline.orchestrator import PipelineOrchestrator

logger = logging.getLogger("ip_sakti.api.routes")
router = APIRouter()
orchestrator = PipelineOrchestrator()


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
    try:
        return await orchestrator.run_pipeline(
            query_text=request.query_text,
            session_id=request.session_id,
        )
    except Exception as exc:
        logger.error("Error processing query in pipeline: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        ) from exc
