from unittest.mock import patch

from fastapi.testclient import TestClient

from src.config import config
from src.main import app
from src.pipeline.abs_tkdl_checker import ABSCheckerOutput
from src.pipeline.answer_generator import Citation as GenCitation
from src.pipeline.answer_generator import GeneratorOutput
from src.pipeline.classifier import ClassifierOutput

client = TestClient(app)


def test_query_endpoint_answered_success():
    payload = {
        "query_text": "Can I patent a classical Triphala formulation in India?",
        "session_id": "abc-123",
    }

    mock_classifier = ClassifierOutput(
        category="Classical Ayurveda",
        confidence=0.95,
        reason="Triphala is a classical recipe.",
    )

    mock_chunks = [
        {
            "doc_id": "patents-act-1970",
            "section": "Section 3(p)",
            "document_type": "statute",
            "source_url": "https://indiacode.nic.in",
            "date_retrieved": "2026-08-31",
            "content": "Section 3(p) excludes traditional knowledge.",
            "similarity_score": 0.88,
        }
    ]

    mock_abs_out = ABSCheckerOutput(
        abs_flag=False,
        abs_detail=None,
        citations=[],
        similarity_score=0.2,
    )

    mock_gen_out = GeneratorOutput(
        answer="Under Section 3(p) of the Patents Act [1], classical formulations cannot be patented.",
        citations=[
            GenCitation(
                doc_id="patents-act-1970",
                source_url="https://indiacode.nic.in",
                doc_type="statute",
                section="Section 3(p)",
                date_retrieved="2026-08-31",
            )
        ],
        abs_flag=False,
        disclaimer=config.DISCLAIMER_TEXT,
    )

    with (
        patch(
            "src.pipeline.classifier.Classifier.classify", return_value=mock_classifier
        ),
        patch("src.pipeline.retriever.Retriever.retrieve", return_value=mock_chunks),
        patch(
            "src.pipeline.abs_tkdl_checker.ABSChecker.check", return_value=mock_abs_out
        ),
        patch(
            "src.pipeline.answer_generator.AnswerGenerator.generate",
            return_value=mock_gen_out,
        ),
    ):
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "answered"
        assert "Section 3(p)" in data["answer"]
        assert len(data["citations"]) == 1
        assert data["citations"][0]["doc_id"] == "patents-act-1970"
        assert data["abs_flag"] is False
        assert data["abstention_message"] is None
        assert data["disclaimer"] == config.DISCLAIMER_TEXT
        assert isinstance(data["response_time_ms"], int)
        assert data["response_time_ms"] >= 0


def test_query_endpoint_abstained_low_confidence():
    payload = {
        "query_text": "What is the patent status of quantum computing semiconductor?",
        "session_id": "abc-456",
    }

    mock_classifier = ClassifierOutput(
        category="Unclassifiable",
        confidence=0.1,
        reason="Not Ayurveda.",
    )

    with (
        patch(
            "src.pipeline.classifier.Classifier.classify", return_value=mock_classifier
        ),
        patch("src.pipeline.retriever.Retriever.retrieve", return_value=[]),
    ):
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "abstained"
        assert data["answer"] is None
        assert data["citations"] == []
        assert data["abstention_message"] is not None
        assert data["disclaimer"] == config.DISCLAIMER_TEXT


def test_query_endpoint_service_error_503():
    payload = {
        "query_text": "Trigger a server failure.",
        "session_id": "abc-789",
    }

    with patch(
        "src.pipeline.classifier.Classifier.classify",
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


def test_lifespan_startup_and_shutdown():
    with TestClient(app) as test_client:
        assert app.state.is_ready is True
        res = test_client.get("/health")
        assert res.status_code == 200
