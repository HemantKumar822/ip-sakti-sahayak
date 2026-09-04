from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.main import app
from src.api.auth import require_admin

app.dependency_overrides[require_admin] = lambda: "test_admin_key"
client = TestClient(app)


def test_corpus_status_healthy():
    mock_stats = {
        "status": "healthy",
        "collection_name": "ip_sakti_legal_corpus",
        "total_chunks": 150,
        "document_count": 5,
        "documents": ["bda_2002", "patents_act_1970", "tkdl_guide"],
    }
    with patch("src.api.admin.ChromaStore") as MockStore:
        mock_instance = MockStore.return_value
        mock_instance.get_collection_stats.return_value = mock_stats

        response = client.get("/admin/corpus/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["collection_name"] == "ip_sakti_legal_corpus"
        assert data["total_chunks"] == 150
        assert data["document_count"] == 5
        assert data["documents"] == ["bda_2002", "patents_act_1970", "tkdl_guide"]


def test_corpus_status_service_unavailable():
    with patch("src.api.admin.ChromaStore") as MockStore:
        mock_instance = MockStore.return_value
        mock_instance.get_collection_stats.side_effect = RuntimeError(
            "Disk read failure in ChromaDB"
        )

        response = client.get("/admin/corpus/status")
        assert response.status_code == 503
        assert "Vector store is unavailable or corrupted" in response.json()["detail"]


def test_corpus_status_with_pipeline_store():
    mock_stats = {
        "status": "healthy",
        "collection_name": "app_pipeline_col",
        "total_chunks": 10,
        "document_count": 1,
        "documents": ["doc_1"],
    }
    mock_store = MagicMock()
    mock_store.get_collection_stats.return_value = mock_stats

    mock_pipeline = MagicMock()
    mock_pipeline.retriever.vector_store = mock_store

    app.state.pipeline = mock_pipeline
    try:
        response = client.get("/admin/corpus/status")
        assert response.status_code == 200
        assert response.json()["collection_name"] == "app_pipeline_col"
        assert response.json()["total_chunks"] == 10
    finally:
        app.state.pipeline = None
