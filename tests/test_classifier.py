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
                "category": "Unclassifiable",
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
        assert result.category == "Unclassifiable"
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
        assert result.category == "Unclassifiable"
        assert result.confidence == 0.0
        assert "error" in result.reason.lower()
