import logging

from fastapi import APIRouter, HTTPException, Request, Response

from src.models.request import QueryRequest
from src.models.response import QueryResponse

logger = logging.getLogger("ip_sakti.api.routes")
router = APIRouter()


@router.get("/health", summary="Health check", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify that the API server is alive."""
    return {"status": "ok", "version": "0.1.0"}


@router.get("/ready", summary="Readiness check", tags=["System"])
async def ready_check(request: Request, response: Response) -> dict[str, str]:
    """Readiness check endpoint to verify that the application is fully loaded and connected."""
    is_ready = getattr(request.app.state, "is_ready", False)
    if not is_ready:
        response.status_code = 503
        return {"status": "not_ready"}

    # We could optionally ping ChromaDB here, but since the embedding model and
    # collection is loaded synchronously right now, checking is_ready is sufficient.
    return {"status": "ready"}


@router.post(
    "/api/v1/query",
    response_model=QueryResponse,
    summary="Submit IPR query",
    tags=["Query"],
)
async def process_query(payload: QueryRequest, request: Request) -> QueryResponse:
    """Process an intellectual property query through the RAG pipeline."""
    orchestrator = request.app.state.pipeline
    try:
        history = [t.model_dump() for t in payload.conversation_history]
        return await orchestrator.run_pipeline(
            query_text=payload.query_text,
            session_id=payload.session_id,
            conversation_history=history or None,
        )
    except Exception as exc:
        logger.error("Error processing query in pipeline: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        ) from exc
