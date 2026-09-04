from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from ingestion.ingest import ingest_single_document
from src.vector_store.chroma_store import ChromaStore

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post(
    "/corpus/ingest",
    summary="Live Corpus Ingestion",
    description="Upload a PDF document to be parsed, chunked, and upserted into the ChromaDB vector store.",
)
async def ingest_corpus(
    file: Annotated[UploadFile, File(...)],
    doc_id: Annotated[str, Form(...)],
    title: Annotated[str | None, Form(None)] = None,
    document_type: Annotated[str, Form()] = "statute",
    source_url: Annotated[str, Form()] = "",
    date_retrieved: Annotated[str, Form()] = "",
    version_or_amendment_date: Annotated[str, Form()] = "",
) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported for ingestion.",
        )

    try:
        content = await file.read()
    except Exception as e:  # noqa: BLE001
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
        # Initialize VectorStore
        store = ChromaStore()
        chunks_ingested = ingest_single_document(
            file_content=content,
            metadata=metadata,
            vector_store=store,
        )
    except Exception as e:  # noqa: BLE001
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
