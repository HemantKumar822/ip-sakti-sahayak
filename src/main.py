import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger("ip_sakti.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    logger.info("Starting IP-SAKTI Sahayak API server...")
    # Application startup initialization (e.g. embedding model & vector store pre-warming)
    app.state.is_ready = True
    yield
    # Application shutdown / resource cleanup
    logger.info("Shutting down IP-SAKTI Sahayak API server...")
    app.state.is_ready = False


app = FastAPI(
    title="IP-SAKTI Sahayak API",
    description="Backend API for the IP-SAKTI Sahayak RAG system",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
