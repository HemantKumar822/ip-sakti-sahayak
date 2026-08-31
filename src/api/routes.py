import time

from fastapi import APIRouter

from src.models.request import QueryRequest
from src.models.response import QueryResponse

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

    # Stub response for Story 2.1 (pipeline stages will be connected in subsequent stories)
    elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 0)

    return QueryResponse(
        status="answered",
        answer="This is a stub response.",
        citations=[],
        abs_flag=False,
        abstention_message=None,
        disclaimer="This is for awareness only. Not legal advice.",
        response_time_ms=elapsed_ms,
    )
