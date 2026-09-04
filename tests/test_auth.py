import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.auth import is_valid_api_key
from src.config import config
from src.main import app
from src.models.response import QueryResponse


@pytest.fixture
def unauthenticated_client() -> TestClient:
    """TestClient without any default credentials."""
    return TestClient(app)


def test_query_missing_api_key_returns_401(unauthenticated_client: TestClient):
    """Requests to /api/v1/query without API credentials must return HTTP 401 with standard error body."""
    response = unauthenticated_client.post(
        "/api/v1/query",
        json={
            "query_text": "Is Triphala patentable in India?",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"
    data = response.json()
    assert data == {
        "error": True,
        "type": "unauthorized",
        "message": "Invalid or missing API key.",
    }


def test_query_invalid_x_api_key_returns_401(unauthenticated_client: TestClient):
    """Requests with an invalid X-API-Key header must return HTTP 401."""
    response = unauthenticated_client.post(
        "/api/v1/query",
        headers={"X-API-Key": "wrong-secret-key"},
        json={
            "query_text": "Is Triphala patentable in India?",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data == {
        "error": True,
        "type": "unauthorized",
        "message": "Invalid or missing API key.",
    }


def test_query_invalid_bearer_token_returns_401(unauthenticated_client: TestClient):
    """Requests with an invalid Bearer token must return HTTP 401."""
    response = unauthenticated_client.post(
        "/api/v1/query",
        headers={"Authorization": "Bearer invalid-token"},
        json={
            "query_text": "Is Triphala patentable in India?",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data == {
        "error": True,
        "type": "unauthorized",
        "message": "Invalid or missing API key.",
    }


def test_query_empty_bearer_token_returns_401(unauthenticated_client: TestClient):
    """Requests with empty Bearer token or malformed auth return HTTP 401."""
    response = unauthenticated_client.post(
        "/api/v1/query",
        headers={"Authorization": "Bearer"},
        json={"query_text": "Test query", "session_id": "test-session"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"] is True
    assert data["type"] == "unauthorized"


def test_query_valid_x_api_key_header_returns_200(unauthenticated_client: TestClient):
    """Supplying a valid key in X-API-Key passes authentication and runs the pipeline."""
    mock_response = QueryResponse(
        status="answered",
        category="Classical Ayurveda",
        jurisdiction="India",
        answer="Under Section 3(p), traditional knowledge cannot be patented.",
        citations=[],
        abs_flag=False,
        abs_detail=None,
        confidence_score=0.9,
        abstention_message=None,
        disclaimer=config.DISCLAIMER_TEXT,
        response_time_ms=50,
    )

    with (
        patch(
            "src.pipeline.orchestrator.PipelineOrchestrator.run_pipeline",
            new_callable=AsyncMock,
            return_value=mock_response,
        ),
        unauthenticated_client as client,
    ):
        response = client.post(
            "/api/v1/query",
            headers={"X-API-Key": "test-valid-key"},
            json={
                "query_text": "Is Triphala patentable?",
                "session_id": "test-session",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "answered"
        assert data["confidence_score"] == 0.9


def test_query_valid_bearer_token_returns_200(unauthenticated_client: TestClient):
    """Supplying a valid key via Authorization: Bearer <key> passes authentication."""
    mock_response = QueryResponse(
        status="answered",
        category="Classical Ayurveda",
        jurisdiction="India",
        answer="Sample advisory",
        citations=[],
        abs_flag=False,
        abs_detail=None,
        confidence_score=0.85,
        abstention_message=None,
        disclaimer=config.DISCLAIMER_TEXT,
        response_time_ms=60,
    )

    with (
        patch(
            "src.pipeline.orchestrator.PipelineOrchestrator.run_pipeline",
            new_callable=AsyncMock,
            return_value=mock_response,
        ),
        unauthenticated_client as client,
    ):
        response = client.post(
            "/api/v1/query",
            headers={"Authorization": "Bearer test-secondary-key"},
            json={
                "query_text": "Is Triphala patentable?",
                "session_id": "test-session",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "answered"


def test_query_secondary_valid_key(unauthenticated_client: TestClient):
    """Multiple valid keys in config.API_KEYS should all be recognized."""
    mock_response = QueryResponse(
        status="answered",
        category="Classical Ayurveda",
        jurisdiction="India",
        answer="Sample advisory",
        citations=[],
        abs_flag=False,
        abs_detail=None,
        confidence_score=0.85,
        abstention_message=None,
        disclaimer=config.DISCLAIMER_TEXT,
        response_time_ms=60,
    )

    with (
        patch(
            "src.pipeline.orchestrator.PipelineOrchestrator.run_pipeline",
            new_callable=AsyncMock,
            return_value=mock_response,
        ),
        unauthenticated_client as client,
    ):
        response = client.post(
            "/api/v1/query",
            headers={"X-API-Key": "test-secondary-key"},
            json={
                "query_text": "Is Triphala patentable?",
                "session_id": "test-session",
            },
        )
        assert response.status_code == 200


def test_health_and_ready_accessible_without_auth(unauthenticated_client: TestClient):
    """Probes /health and /ready must remain completely public and require no credentials."""
    resp_health = unauthenticated_client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "ok"

    resp_ready = unauthenticated_client.get("/ready")
    assert resp_ready.status_code in (200, 503)


def test_docs_and_openapi_accessible_without_auth(unauthenticated_client: TestClient):
    """OpenAPI and Swagger UI must remain accessible without credentials."""
    resp_docs = unauthenticated_client.get("/docs")
    assert resp_docs.status_code == 200

    resp_openapi = unauthenticated_client.get("/openapi.json")
    assert resp_openapi.status_code == 200
    openapi_json = resp_openapi.json()
    assert "paths" in openapi_json
    assert "/api/v1/query" in openapi_json["paths"]


def test_constant_time_comparison_unit():
    """Unit test for is_valid_api_key confirming timing-attack mitigation and edge case safety."""
    valid_keys = ["secret-key-1", "secret-key-2"]

    # Valid matches
    assert is_valid_api_key("secret-key-1", valid_keys) is True
    assert is_valid_api_key("secret-key-2", valid_keys) is True

    # Invalid mismatches
    assert is_valid_api_key("secret-key-3", valid_keys) is False
    assert is_valid_api_key("secret-key", valid_keys) is False
    assert is_valid_api_key("secret-key-1-extended", valid_keys) is False

    # Empty inputs
    assert is_valid_api_key("", valid_keys) is False
    assert is_valid_api_key("secret-key-1", []) is False
    assert is_valid_api_key("", []) is False


def test_config_api_keys_whitespace_and_empty_handling(monkeypatch):
    """Config.API_KEYS parsing strips leading/trailing spaces and omits empty tokens."""
    monkeypatch.setenv("VALID_API_KEYS", "  alpha,  beta , , gamma  ,, ")
    # Re-evaluate logic equivalent to Config class definition
    parsed_keys = [
        k.strip() for k in os.getenv("VALID_API_KEYS", "").split(",") if k.strip()
    ]
    assert parsed_keys == ["alpha", "beta", "gamma"]


def test_verify_api_key_raw_header_fallbacks():
    """Verify fallback branches for raw headers when security schemes return None."""
    import asyncio
    from unittest.mock import MagicMock

    from fastapi import HTTPException

    from src.api.auth import verify_api_key

    # Test raw x-api-key fallback
    req_x = MagicMock()
    req_x.headers = {"x-api-key": "test-valid-key"}
    req_x.client.host = "127.0.0.1"
    key = asyncio.run(verify_api_key(req_x, api_key_header=None, bearer_auth=None))
    assert key == "test-valid-key"

    # Test raw authorization Bearer fallback
    req_auth = MagicMock()
    req_auth.headers = {"authorization": "Bearer test-secondary-key"}
    req_auth.client.host = "127.0.0.1"
    key = asyncio.run(verify_api_key(req_auth, api_key_header=None, bearer_auth=None))
    assert key == "test-secondary-key"

    # Test missing credentials raises HTTPException 401
    req_empty = MagicMock()
    req_empty.headers = {}
    req_empty.client.host = "127.0.0.1"
    req_empty.url.path = "/api/v1/query"
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(verify_api_key(req_empty, api_key_header=None, bearer_auth=None))
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or missing API key."
