import logging

from fastapi import APIRouter, HTTPException, Request, Response

from src.config import config
from src.models.request import QueryRequest
from src.models.response import QueryResponse
from src.models.session import SessionDetailResponse, SessionTurnResponse

logger = logging.getLogger("ip_sakti.api.routes")

system_router = APIRouter(tags=["System"])
api_v1_router = APIRouter(prefix="/api/v1", tags=["Query"])


@system_router.get("/health", summary="Health check", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify that the API server is alive."""
    return {"status": "ok", "version": "0.1.0"}


@system_router.get("/ready", summary="Readiness check", tags=["System"])
async def ready_check(request: Request, response: Response) -> dict[str, str]:
    """Readiness check endpoint to verify that the application is fully loaded and connected."""
    is_ready = getattr(request.app.state, "is_ready", False)
    if not is_ready:
        response.status_code = 503
        return {"status": "not_ready"}

    return {"status": "ready"}


@api_v1_router.get(
    "/sessions/{session_id}",
    response_model=SessionDetailResponse,
    summary="Retrieve session history",
    tags=["Session"],
)
async def get_session_history(
    session_id: str, request: Request
) -> SessionDetailResponse:
    """Retrieve full conversation turn history and metadata for a session."""
    session_store = getattr(request.app.state, "session_store", None)
    if session_store is None:
        raise HTTPException(
            status_code=503,
            detail="Session store service unavailable",
        )

    session_info = session_store.get_session(session_id)
    if session_info is None or session_info.get("total_turns", 0) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found.",
        )

    raw_turns = session_store.get_session_turns(
        session_id, limit=config.MAX_SESSION_TURNS * 2
    )
    turn_models = [
        SessionTurnResponse(
            id=t["id"],
            role=t["role"],
            content=t["content"],
            citations=t.get("citations"),
            response_metadata=t.get("response_metadata"),
            created_at=t.get("created_at"),
        )
        for t in raw_turns
    ]

    return SessionDetailResponse(
        session_id=session_info["session_id"],
        turns=turn_models,
        total_turns=session_info["total_turns"],
        created_at=session_info["created_at"],
        updated_at=session_info["updated_at"],
    )


@api_v1_router.post(
    "/query",
    response_model=QueryResponse,
    summary="Submit IPR query",
    tags=["Query"],
)
async def process_query(payload: QueryRequest, request: Request) -> QueryResponse:
    """Process an intellectual property query through the RAG pipeline."""
    orchestrator = request.app.state.pipeline
    session_store = getattr(request.app.state, "session_store", None)

    # 1. Enforce 6-turn ceiling per session
    if session_store is not None:
        user_turn_count = session_store.count_turns(payload.session_id, role="user")
        if user_turn_count >= config.MAX_SESSION_TURNS:
            logger.warning(
                "Session [%s] rejected: exceeded turn limit of %d",
                payload.session_id[:8],
                config.MAX_SESSION_TURNS,
            )
            raise HTTPException(
                status_code=400,
                detail=f"Session turn limit ({config.MAX_SESSION_TURNS}) reached. Please start a new session.",
            )

    try:
        # 2. Reconstruct or use submitted conversation history
        history = [t.model_dump() for t in payload.conversation_history]
        if not history and session_store is not None:
            stored_turns = session_store.get_session_turns(
                payload.session_id, limit=config.MAX_SESSION_TURNS * 2
            )
            history = [
                {"role": st["role"], "content": st["content"]} for st in stored_turns
            ]

        # 3. Persist incoming user turn
        if session_store is not None:
            session_store.save_turn(
                session_id=payload.session_id,
                role="user",
                content=payload.query_text,
            )

        # 4. Execute RAG pipeline
        response = await orchestrator.run_pipeline(
            query_text=payload.query_text,
            session_id=payload.session_id,
            conversation_history=history or None,
        )

        # 5. Persist assistant response turn with citations and metadata
        if session_store is not None:
            assistant_content = response.answer or response.abstention_message or ""
            serialized_citations = [c.model_dump() for c in response.citations]
            session_store.save_turn(
                session_id=payload.session_id,
                role="assistant",
                content=assistant_content,
                citations=serialized_citations,
                response_metadata=response.model_dump(),
            )

        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error processing query in pipeline: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        ) from exc


router = APIRouter()
router.include_router(system_router)
router.include_router(api_v1_router)
