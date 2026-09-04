import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.routes import router
from src.config import config
from src.pipeline.orchestrator import PipelineOrchestrator
from src.session import SQLiteSessionStore
from src.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger("ip_sakti.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    logger.info("Starting IP-SAKTI Sahayak API server...")
    # Validate required configuration before starting
    config.validate()
    # Application startup initialization (e.g. embedding model & vector store pre-warming)
    app.state.pipeline = PipelineOrchestrator()
    app.state.session_store = SQLiteSessionStore()
    app.state.is_ready = True
    yield
    # Application shutdown / resource cleanup
    logger.info("Shutting down IP-SAKTI Sahayak API server...")
    app.state.is_ready = False
    if getattr(app.state, "session_store", None) is not None:
        app.state.session_store.close()
    app.state.session_store = None
    app.state.pipeline = None


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="IP-SAKTI Sahayak API",
    description="Backend API for the IP-SAKTI Sahayak RAG system",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    incident_id = str(uuid.uuid4())
    logger.error(
        "Unhandled exception on %s %s [Incident ID: %s]: %s",
        request.method,
        request.url,
        incident_id,
        exc,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "type": "internal_error",
            "message": "An internal server error occurred.",
            "incident_id": incident_id,
        },
    )
