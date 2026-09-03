from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.config import config
from src.main import app
from src.models.response import Citation, QueryResponse

client = TestClient(app)
app.state.pipeline = MagicMock()


def test_query_endpoint_answered_success():
    payload = {
        "query_text": "Can I patent a classical Triphala formulation in India?",
        "session_id": "abc-123",
    }

    mock_response = QueryResponse(
        status="answered",
        category="Classical Ayurveda",
        jurisdiction="India",
        answer="Under Section 3(p) of the Patents Act [1], classical formulations cannot be patented.",
        citations=[
            Citation(
                doc_id="patents-act-1970",
                source_url="https://indiacode.nic.in",
                doc_type="statute",
                section="Section 3(p)",
                date_retrieved="2026-08-31",
            )
        ],
        abs_flag=False,
        abs_detail=None,
        confidence_score=0.88,
        abstention_message=None,
        disclaimer=config.DISCLAIMER_TEXT,
        response_time_ms=150,
    )

    with patch.object(
        app.state.pipeline,
        "run_pipeline",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_run:
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200
        mock_run.assert_called_once_with(
            query_text="Can I patent a classical Triphala formulation in India?",
            session_id="abc-123",
            conversation_history=None,
        )

        data = response.json()
        assert data["status"] == "answered"
        assert "Section 3(p)" in data["answer"]
        assert len(data["citations"]) == 1
        assert data["citations"][0]["doc_id"] == "patents-act-1970"
        assert data["abs_flag"] is False
        assert data["abstention_message"] is None
        assert data["disclaimer"] == config.DISCLAIMER_TEXT
        assert data["response_time_ms"] == 150


def test_query_endpoint_abstained_low_confidence():
    payload = {
        "query_text": "What is the patent status of quantum computing semiconductor?",
        "session_id": "abc-456",
    }

    mock_response = QueryResponse(
        status="abstained",
        category="Unclassifiable",
        jurisdiction="India",
        answer=None,
        citations=[],
        abs_flag=False,
        abs_detail=None,
        confidence_score=0.1,
        abstention_message=config.ABSTENTION_MESSAGE,
        disclaimer=config.DISCLAIMER_TEXT,
        response_time_ms=50,
    )

    with patch.object(
        app.state.pipeline,
        "run_pipeline",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "abstained"
        assert data["answer"] is None
        assert data["citations"] == []
        assert data["abstention_message"] == config.ABSTENTION_MESSAGE
        assert data["disclaimer"] == config.DISCLAIMER_TEXT


def test_query_endpoint_service_error_503():
    payload = {
        "query_text": "Trigger a server failure.",
        "session_id": "abc-789",
    }

    with patch.object(
        app.state.pipeline,
        "run_pipeline",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Fatal pipeline crash"),
    ):
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 503
        data = response.json()
        assert data["detail"] == "Service temporarily unavailable"


def test_query_endpoint_missing_query_text():
    payload = {"session_id": "abc-123"}
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 422


def test_query_endpoint_missing_session_id():
    payload = {"query_text": "Can I patent an Ayurveda formulation?"}
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 422


def test_query_endpoint_empty_payload():
    response = client.post("/api/v1/query", json={})
    assert response.status_code == 422


@patch("src.main.PipelineOrchestrator")
def test_lifespan_startup_and_shutdown(mock_orchestrator):
    with TestClient(app) as test_client:
        assert app.state.is_ready is True
        res = test_client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok", "version": "0.1.0"}

    # Also test readiness endpoint
    res_ready = client.get("/ready")
    # since client (no context manager) won't have is_ready=True after lifespan teardown:
    assert res_ready.status_code == 503
