from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_query_endpoint_success():
    payload = {
        "query_text": "Can I patent an Ayurveda formulation?",
        "session_id": "abc-123",
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "answered"
    assert data["answer"] == "This is a stub response."
    assert data["citations"] == []
    assert data["abs_flag"] is False
    assert data["abstention_message"] is None
    assert data["disclaimer"] == "This is for awareness only. Not legal advice."
    assert isinstance(data["response_time_ms"], int)
    assert data["response_time_ms"] >= 0


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


def test_lifespan_startup_and_shutdown():
    with TestClient(app) as test_client:
        assert app.state.is_ready is True
        res = test_client.get("/health")
        assert res.status_code == 200
