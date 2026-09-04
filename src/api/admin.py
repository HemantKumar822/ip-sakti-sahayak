# ruff: noqa: B008, BLE001
import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status

from ingestion.ingest import ingest_single_document
from src.vector_store.chroma_store import ChromaStore

logger = logging.getLogger("ip_sakti.api.admin")
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/corpus/status",
    summary="Corpus Health and Status Inspection",
    description="Inspect the active ChromaDB vector store collection, returning chunk counts, document distribution, and database health.",
)
async def get_corpus_status(request: Request) -> dict[str, Any]:
    try:
        store = None
        if hasattr(request.app.state, "pipeline") and request.app.state.pipeline:
            store = getattr(request.app.state.pipeline.retriever, "vector_store", None)
        if store is None or not hasattr(store, "get_collection_stats"):
            store = ChromaStore()
        return store.get_collection_stats()
    except Exception as e:
        logger.error("Corpus status check failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector store is unavailable or corrupted: {e!s}",
        )


@router.post(
    "/corpus/ingest",
    summary="Live Corpus Ingestion",
    description="Upload a PDF document to be parsed, chunked, and upserted into the ChromaDB vector store.",
)
async def ingest_corpus(
    request: Request,
    file: UploadFile = File(...),
    doc_id: str = Form(...),
    title: str | None = Form(default=None),
    document_type: str = Form(default="statute"),
    source_url: str = Form(default=""),
    date_retrieved: str = Form(default=""),
    version_or_amendment_date: str = Form(default=""),
) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported for ingestion.",
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {e!s}",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    metadata = {
        "doc_id": doc_id,
        "title": title or doc_id,
        "document_type": document_type,
        "source_url": source_url,
        "date_retrieved": date_retrieved,
        "version_or_amendment_date": version_or_amendment_date,
    }

    try:
        # Obtain active VectorStore from pipeline if available, else initialize ChromaStore
        store = None
        pipeline = (
            getattr(request.app.state, "pipeline", None)
            if hasattr(request.app.state, "pipeline")
            else None
        )
        if pipeline and hasattr(pipeline, "retriever"):
            store = getattr(pipeline.retriever, "vector_store", None)
        if store is None:
            store = ChromaStore()

        chunks_ingested = ingest_single_document(
            file_content=content,
            metadata=metadata,
            vector_store=store,
        )

        # Trigger automatic hybrid BM25 index refresh if pipeline/retriever is active
        if chunks_ingested > 0 and pipeline and hasattr(pipeline, "retriever"):
            try:
                pipeline.retriever.reload_hybrid_index()
                logger.info(
                    "Triggered hybrid BM25 index reload following ingestion of '%s'",
                    doc_id,
                )
            except Exception as reindex_err:
                logger.warning(
                    "Failed to refresh hybrid BM25 index after ingestion: %s",
                    reindex_err,
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {e!s}",
        )

    if chunks_ingested == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document parsed but generated 0 chunks. Ensure the PDF contains readable text.",
        )

    return {
        "status": "success",
        "doc_id": doc_id,
        "chunks_ingested": chunks_ingested,
    }
