import json
from unittest.mock import patch

import pytest

from src.models.query_context import QueryContext
from src.pipeline.classifier import Classifier, ClassifierOutput


@pytest.fixture
def classifier():
    return Classifier()


class MockGenerateContentResponse:
    def __init__(self, text: str):
        self.text = text


def test_classifier_proprietary(classifier):
    mock_response = MockGenerateContentResponse(
        json.dumps(
            {
                "category": "Proprietary Ayurveda",
                "confidence": 0.9,
                "reason": "Chyawanprash is a well-known proprietary formulation.",
            }
        )
    )
    with patch.object(classifier.model, "generate_content", return_value=mock_response):
        ctx = QueryContext(
            raw_query="What is the IP protection for Chyawanprash?",
            english_keywords="",
            is_hindi=False,
        )
        result = classifier.classify(ctx)
        assert isinstance(result, ClassifierOutput)
        assert result.category == "Proprietary Ayurveda"
        assert result.confidence == 0.9


def test_classifier_classical(classifier):
    mock_response = MockGenerateContentResponse(
        json.dumps(
            {
                "category": "Classical Ayurveda",
                "confidence": 0.95,
                "reason": "Triphala is a traditional formula.",
            }
        )
    )
    with patch.object(classifier.model, "generate_content", return_value=mock_response):
        ctx = QueryContext(
            raw_query="How is Triphala traditionally made?",
            english_keywords="",
            is_hindi=False,
        )
        result = classifier.classify(ctx)
        assert isinstance(result, ClassifierOutput)
        assert result.category == "Classical Ayurveda"
        assert result.confidence == 0.95


def test_classifier_unclassifiable(classifier):
    mock_response = MockGenerateContentResponse(
        json.dumps(
            {
                "category": "General Non-Legal",
                "confidence": 0.95,
                "reason": "Not related to Ayurveda.",
            }
        )
    )
    with patch.object(classifier.model, "generate_content", return_value=mock_response):
        ctx = QueryContext(
            raw_query="What is the best programming language?",
            english_keywords="",
            is_hindi=False,
        )
        result = classifier.classify(ctx)
        assert isinstance(result, ClassifierOutput)
        assert result.category == "General Non-Legal"
        assert result.confidence == 0.95


def test_classifier_api_failure(classifier):
    with patch.object(
        classifier.model, "generate_content", side_effect=Exception("API Timeout")
    ):
        ctx = QueryContext(
            raw_query="Does this error out gracefully?",
            english_keywords="",
            is_hindi=False,
        )
        result = classifier.classify(ctx)
        assert isinstance(result, ClassifierOutput)
        assert result.category == "General Non-Legal"
        assert result.confidence == 0.0
        assert "error" in result.reason.lower()


def test_classifier_timeout_fallback_classical(classifier):
    with patch.object(
        classifier.model,
        "generate_content",
        side_effect=TimeoutError("Gemini Request Timed Out"),
    ):
        ctx = QueryContext(
            raw_query="How is Triphala classical churna mentioned in Charaka Samhita?",
            english_keywords="",
            is_hindi=False,
        )
        result = classifier.classify(ctx)
        assert isinstance(result, ClassifierOutput)
        assert result.category == "Classical Ayurveda"
        assert result.confidence == 0.85
        assert "heuristic" in result.reason.lower()


def test_classifier_timeout_fallback_conversational(classifier):
    with patch.object(
        classifier.model,
        "generate_content",
        side_effect=TimeoutError("Request timed out"),
    ):
        ctx = QueryContext(
            raw_query="hello",
            english_keywords="",
            is_hindi=False,
        )
        result = classifier.classify(ctx)
        assert isinstance(result, ClassifierOutput)
        assert result.category == "Conversational"
        assert result.confidence == 0.90


def test_classifier_rate_limit_retry_and_recovery(classifier):
    mock_success = MockGenerateContentResponse(
        json.dumps(
            {
                "category": "Classical Ayurveda",
                "confidence": 0.98,
                "reason": "Recovered classical Ayurveda query.",
            }
        )
    )
    with (
        patch("time.sleep") as mock_sleep,
        patch.object(
            classifier.model,
            "generate_content",
            side_effect=[
                RuntimeError("ResourceExhausted: 429 Quota exceeded"),
                mock_success,
            ],
        ) as mock_gen,
    ):
        ctx = QueryContext(
            raw_query="Is Triphala covered under Section 3(p)?",
            english_keywords="",
            is_hindi=False,
        )
        result = classifier.classify(ctx)
        assert isinstance(result, ClassifierOutput)
        assert result.category == "Classical Ayurveda"
        assert result.confidence == 0.98
        assert mock_gen.call_count == 2
        mock_sleep.assert_called_once()


def test_classifier_rate_limit_exhaustion_fallback(classifier):
    with (
        patch("time.sleep") as mock_sleep,
        patch.object(
            classifier.model,
            "generate_content",
            side_effect=RuntimeError("429 Too Many Requests"),
        ) as mock_gen,
    ):
        ctx = QueryContext(
            raw_query="Can I patent herbal neem extract formulation with curcumin?",
            english_keywords="",
            is_hindi=False,
        )
        result = classifier.classify(ctx)
        assert isinstance(result, ClassifierOutput)
        assert result.category == "Proprietary Ayurveda"
        assert result.confidence == 0.80
        # 1 initial attempt + 2 retries = 3 calls
        assert mock_gen.call_count == 3
        assert mock_sleep.call_count == 2
