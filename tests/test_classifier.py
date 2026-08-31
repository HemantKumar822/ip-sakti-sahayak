import json
from unittest.mock import patch

import pytest

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
        result = classifier.classify("What is the IP protection for Chyawanprash?")
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
        result = classifier.classify("How is Triphala traditionally made?")
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
        result = classifier.classify("What is the best programming language?")
        assert isinstance(result, ClassifierOutput)
        assert result.category == "Unclassifiable"
        assert result.confidence == 0.95


def test_classifier_api_failure(classifier):
    with patch.object(
        classifier.model, "generate_content", side_effect=Exception("API Timeout")
    ):
        result = classifier.classify("Does this error out gracefully?")
        assert isinstance(result, ClassifierOutput)
        assert result.category == "Unclassifiable"
        assert result.confidence == 0.0
        assert "error" in result.reason.lower()
