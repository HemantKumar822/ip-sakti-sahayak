from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.config import config
from src.main import app
from src.models.response import Citation, QueryResponse


def test_query_endpoint_answered_success(client: TestClient) -> None:
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
        client.app.state.pipeline,
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


def test_query_endpoint_abstained_low_confidence(client: TestClient) -> None:
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
        client.app.state.pipeline,
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


def test_query_endpoint_service_error_503(client: TestClient) -> None:
    payload = {
        "query_text": "Trigger a server failure.",
        "session_id": "abc-789",
    }

    with patch.object(
        client.app.state.pipeline,
        "run_pipeline",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Fatal pipeline crash"),
    ):
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 503
        data = response.json()
        assert data["detail"] == "Service temporarily unavailable"


def test_query_endpoint_missing_query_text(client: TestClient) -> None:
    payload = {"session_id": "abc-123"}
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 422


def test_query_endpoint_missing_session_id(client: TestClient) -> None:
    payload = {"query_text": "Can I patent an Ayurveda formulation?"}
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 422


def test_query_endpoint_empty_payload(client: TestClient) -> None:
    response = client.post("/api/v1/query", json={})
    assert response.status_code == 422


def test_lifespan_startup_and_shutdown() -> None:
    """Verifies that lifespan startup and shutdown hooks transition app.state cleanly."""
    with (
        patch("src.main.PipelineOrchestrator"),
        TestClient(app) as test_client,
    ):
        assert test_client.app.state.is_ready is True
        res_health = test_client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json() == {"status": "ok", "version": "0.1.0"}

        res_ready = test_client.get("/ready")
        assert res_ready.status_code == 200
        assert res_ready.json() == {"status": "ready"}

    # After exiting the with-context, lifespan shutdown has executed
    unstarted = TestClient(app)
    res_unready = unstarted.get("/ready")
    assert res_unready.status_code == 503
    assert res_unready.json() == {"status": "not_ready"}


def test_readiness_probe_unstarted(unstarted_client: TestClient) -> None:
    """Verifies that an unstarted client outside of lifespan context reports 503 not_ready."""
    res_unready = unstarted_client.get("/ready")
    assert res_unready.status_code == 503
    assert res_unready.json() == {"status": "not_ready"}


def test_get_session_endpoint_success_and_not_found(client: TestClient) -> None:
    session_id = "sess-api-test-01"
    # 404 before any turns exist
    res_404 = client.get(f"/api/v1/sessions/{session_id}")
    assert res_404.status_code == 404
    assert f"Session '{session_id}' not found." in res_404.json()["detail"]

    # Save turn via store directly
    store = client.app.state.session_store
    store.save_turn(session_id, "user", "What is ABS?")
    store.save_turn(
        session_id,
        "assistant",
        "ABS stands for Access and Benefit Sharing.",
        citations=[{"doc_id": "bda-2002", "section": "Section 6"}],
    )

    res_200 = client.get(f"/api/v1/sessions/{session_id}")
    assert res_200.status_code == 200
    data = res_200.json()
    assert data["session_id"] == session_id
    assert data["total_turns"] == 2
    assert len(data["turns"]) == 2
    assert data["turns"][0]["role"] == "user"
    assert data["turns"][0]["content"] == "What is ABS?"
    assert data["turns"][1]["role"] == "assistant"
    assert data["turns"][1]["citations"][0]["doc_id"] == "bda-2002"


def test_list_sessions_endpoint(client: TestClient) -> None:
    store = client.app.state.session_store
    s_id = "sess-list-api-test"
    store.save_turn(s_id, "user", "How does Section 3(p) apply to turmeric?")
    store.save_turn(s_id, "assistant", "Turmeric is documented in TKDL.")

    res = client.get("/api/v1/sessions")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    matching = [s for s in items if s["session_id"] == s_id]
    assert len(matching) == 1
    assert matching[0]["preview"] == "How does Section 3(p) apply to turmeric?"
    assert matching[0]["total_turns"] == 2
    assert matching[0]["updated_at"] is not None


def test_query_persists_turns_and_enforces_6_turn_limit(client: TestClient) -> None:
    session_id = "sess-limit-test-01"
    mock_response = QueryResponse(
        status="answered",
        category="Classical Ayurveda",
        jurisdiction="India",
        answer="Under Section 3(p), classical formulations cannot be patented.",
        citations=[],
        abs_flag=False,
        abs_detail=None,
        confidence_score=0.9,
        abstention_message=None,
        disclaimer=config.DISCLAIMER_TEXT,
        response_time_ms=100,
    )

    with patch.object(
        client.app.state.pipeline,
        "run_pipeline",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        # Submit 6 queries - all should succeed
        for i in range(6):
            payload = {
                "query_text": f"Question turn {i + 1}",
                "session_id": session_id,
            }
            res = client.post("/api/v1/query", json=payload)
            assert res.status_code == 200

        # Verify 12 total turns (6 user + 6 assistant) persisted
        store = client.app.state.session_store
        assert store.count_turns(session_id, role="user") == 6
        assert store.count_turns(session_id, role="assistant") == 6
        assert store.count_turns(session_id) == 12

        # 7th query must be rejected with 400
        payload_7 = {
            "query_text": "Question turn 7 (exceeds limit)",
            "session_id": session_id,
        }
        res_7 = client.post("/api/v1/query", json=payload_7)
        assert res_7.status_code == 400
        assert (
            "Session turn limit (6) reached. Please start a new session."
            in res_7.json()["detail"]
        )


def test_query_request_validation_length_constraints(client: TestClient) -> None:
    # Query text exceeding 4000 characters
    long_query = "A" * 4001
    res_long = client.post(
        "/api/v1/query",
        json={"query_text": long_query, "session_id": "test-valid-len"},
    )
    assert res_long.status_code == 422

    # Conversation history exceeding 6 items
    too_many_turns = [{"role": "user", "content": f"msg {i}"} for i in range(7)]
    res_history = client.post(
        "/api/v1/query",
        json={
            "query_text": "Valid query",
            "session_id": "test-valid-len",
            "conversation_history": too_many_turns,
        },
    )
    assert res_history.status_code == 422
