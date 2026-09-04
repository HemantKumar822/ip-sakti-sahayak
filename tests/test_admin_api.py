import io
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.auth import require_admin
from src.main import app

app.dependency_overrides[require_admin] = lambda: "test_admin_key"
client = TestClient(app)


def test_ingest_corpus_success():
    # Mocking the VectorStore to avoid hitting ChromaDB directly during the API test
    with patch("src.api.admin.ChromaStore") as MockStore:
        mock_store_instance = MockStore.return_value

        # We also want to mock ingest_single_document to avoid running actual parsing/chunking
        # in this API boundary test, since those have their own unit tests.
        with patch(
            "src.api.admin.ingest_single_document", return_value=5
        ) as mock_ingest:

            # Dummy PDF content
            dummy_pdf_content = b"%PDF-1.4\n%...\n"
            file = io.BytesIO(dummy_pdf_content)

            data = {
                "doc_id": "test_doc_01",
                "title": "Test Title",
                "document_type": "statute",
            }

            files = {"file": ("test.pdf", file, "application/pdf")}

            response = client.post("/admin/corpus/ingest", data=data, files=files)

            assert response.status_code == 200
            json_response = response.json()
            assert json_response["status"] == "success"
            assert json_response["doc_id"] == "test_doc_01"
            assert json_response["chunks_ingested"] == 5

            # Assert ingest_single_document was called
            mock_ingest.assert_called_once()
            _args, kwargs = mock_ingest.call_args
            assert kwargs["file_content"] == dummy_pdf_content
            assert kwargs["metadata"]["doc_id"] == "test_doc_01"
            assert kwargs["metadata"]["title"] == "Test Title"
            assert kwargs["vector_store"] == mock_store_instance


def test_ingest_corpus_invalid_file_extension():
    # Attempting to upload a txt file should fail at the route validation
    dummy_txt = b"Hello, World!"
    file = io.BytesIO(dummy_txt)

    data = {"doc_id": "test_doc_02"}

    files = {"file": ("test.txt", file, "text/plain")}

    response = client.post("/admin/corpus/ingest", data=data, files=files)

    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_ingest_corpus_zero_chunks():
    with patch("src.api.admin.ChromaStore"), patch(
        "src.api.admin.ingest_single_document", return_value=0
    ):
        dummy_pdf_content = b"%PDF-1.4\n%...\n"
        file = io.BytesIO(dummy_pdf_content)

        data = {"doc_id": "test_doc_03"}

        files = {"file": ("empty.pdf", file, "application/pdf")}

        response = client.post("/admin/corpus/ingest", data=data, files=files)

        # Since chunks_ingested == 0, we expect a 400 Bad Request
        assert response.status_code == 400
        assert "0 chunks" in response.json()["detail"]


def test_ingest_corpus_triggers_retriever_reload():
    from unittest.mock import MagicMock

    mock_pipeline = MagicMock()
    mock_pipeline.retriever.vector_store = MagicMock()

    with patch("src.api.admin.ingest_single_document", return_value=3):
        dummy_pdf_content = b"%PDF-1.4\n%...\n"
        file = io.BytesIO(dummy_pdf_content)
        data = {"doc_id": "test_doc_reload"}
        files = {"file": ("test.pdf", file, "application/pdf")}

        app.state.pipeline = mock_pipeline
        try:
            response = client.post("/admin/corpus/ingest", data=data, files=files)
            assert response.status_code == 200
            assert response.json()["chunks_ingested"] == 3
            mock_pipeline.retriever.reload_hybrid_index.assert_called_once()
        finally:
            app.state.pipeline = None
