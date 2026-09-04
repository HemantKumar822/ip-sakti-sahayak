from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.config import config
from src.main import app
from src.pipeline.orchestrator import PipelineOrchestrator


@pytest.fixture(autouse=True)
def setup_test_api_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configures default valid test API keys for test execution."""
    monkeypatch.setattr(config, "API_KEYS", ["test-valid-key", "test-secondary-key"])


@pytest.fixture
def mock_orchestrator() -> MagicMock:
    """Provides an isolated mock for the PipelineOrchestrator."""
    mock = MagicMock(spec=PipelineOrchestrator)
    mock.run_pipeline = AsyncMock()
    return mock


@pytest.fixture
def client(mock_orchestrator: MagicMock) -> Generator[TestClient, None, None]:
    """Provides a lifespan-initialized FastAPI TestClient with isolated mocks.

    Startup lifecycle hooks are executed cleanly with PipelineOrchestrator
    patched so no external vector stores or models are initialized during testing.
    Includes default valid X-API-Key header.
    """
    with (
        patch("src.main.PipelineOrchestrator", return_value=mock_orchestrator),
        TestClient(app, headers={"X-API-Key": "test-valid-key"}) as test_client,
    ):
        yield test_client

    # Guarantee clean state reset after test teardown
    app.state.pipeline = None
    app.state.is_ready = False


@pytest.fixture
def unstarted_client() -> Generator[TestClient, None, None]:
    """Provides a TestClient instance without entering the lifespan context.

    Useful for validating application readiness probes and pre-startup behavior.
    """
    app.state.pipeline = None
    app.state.is_ready = False
    yield TestClient(app)
