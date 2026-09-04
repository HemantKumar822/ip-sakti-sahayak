import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.admin import router as admin_router
from src.api.auth import verify_api_key
from src.api.routes import api_v1_router, system_router
from src.config import config
from src.pipeline.orchestrator import PipelineOrchestrator
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
    app.state.is_ready = True
    yield
    # Application shutdown / resource cleanup
    logger.info("Shutting down IP-SAKTI Sahayak API server...")
    app.state.is_ready = False
    app.state.pipeline = None


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

app.include_router(system_router)
app.include_router(api_v1_router, dependencies=[Depends(verify_api_key)])
app.include_router(admin_router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        detail_msg = (
            exc.detail if isinstance(exc.detail, str) else "Invalid or missing API key."
        )
        return JSONResponse(
            status_code=401,
            content={
                "error": True,
                "type": "unauthorized",
                "message": detail_msg,
            },
            headers=exc.headers,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


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
