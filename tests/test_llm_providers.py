"""Unit and integration tests for LLM Provider Factory and implementations."""

import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from src.config import config
from src.pipeline.answer_generator import AnswerGenerator, GeneratorOutput
from src.pipeline.classifier import Classifier, ClassifierOutput
from src.pipeline.providers import (
    BaseLLMClient,
    GeminiProvider,
    OpenRouterProvider,
    get_llm_client,
)
from src.pipeline.providers.openrouter import _extract_json_text


class SampleSchema(BaseModel):
    title: str = Field(description="Sample title")
    score: float = Field(description="Sample score")


# ---------------------------------------------------------------------------
# Factory Tests
# ---------------------------------------------------------------------------


def test_factory_default_gemini(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "gemini")
    client = get_llm_client()
    assert isinstance(client, GeminiProvider)
    assert isinstance(client, BaseLLMClient)


def test_factory_explicit_openrouter():
    client = get_llm_client("openrouter")
    assert isinstance(client, OpenRouterProvider)
    assert isinstance(client, BaseLLMClient)


def test_factory_unsupported_provider():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_llm_client("anthropic_direct")


# ---------------------------------------------------------------------------
# GeminiProvider Tests
# ---------------------------------------------------------------------------


def test_gemini_provider_generate_text():
    provider = GeminiProvider(api_key="test-key", model_name="gemini-1.5-flash")
    mock_resp = MagicMock()
    mock_resp.text = "Sample response text"

    with patch.object(
        provider.model, "generate_content", return_value=mock_resp
    ) as mock_gen:
        res = provider.generate_text("Hello test")
        assert res == "Sample response text"
        mock_gen.assert_called_once()


def test_gemini_provider_generate_text_empty():
    provider = GeminiProvider(api_key="test-key", model_name="gemini-1.5-flash")
    mock_resp = MagicMock()
    mock_resp.text = None

    with patch.object(provider.model, "generate_content", return_value=mock_resp):
        res = provider.generate_text("Hello test")
        assert res == ""


def test_gemini_provider_generate_structured_success():
    provider = GeminiProvider(api_key="test-key", model_name="gemini-1.5-flash")
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({"title": "Test Patent", "score": 0.95})

    with patch.object(provider.model, "generate_content", return_value=mock_resp):
        res = provider.generate_structured("Extract info", response_schema=SampleSchema)
        assert isinstance(res, SampleSchema)
        assert res.title == "Test Patent"
        assert res.score == 0.95


def test_gemini_provider_generate_structured_empty_raises():
    provider = GeminiProvider(api_key="test-key", model_name="gemini-1.5-flash")
    mock_resp = MagicMock()
    mock_resp.text = ""

    with (
        patch.object(provider.model, "generate_content", return_value=mock_resp),
        pytest.raises(RuntimeError, match="empty structured response"),
    ):
        provider.generate_structured("Extract info", response_schema=SampleSchema)


def test_gemini_provider_generate_chat_text():
    provider = GeminiProvider(api_key="test-key", model_name="gemini-1.5-flash")
    mock_chat = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "Chat message response"
    mock_chat.send_message.return_value = mock_resp

    with patch.object(provider.model, "start_chat", return_value=mock_chat):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "model", "content": "Hello"},
        ]
        res = provider.generate_chat("How are you?", conversation_history=history)
        assert res == "Chat message response"
        mock_chat.send_message.assert_called_once()


def test_gemini_provider_generate_chat_structured():
    provider = GeminiProvider(api_key="test-key", model_name="gemini-1.5-flash")
    mock_chat = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({"title": "Chat Schema", "score": 0.88})
    mock_chat.send_message.return_value = mock_resp

    with patch.object(provider.model, "start_chat", return_value=mock_chat):
        history = [{"role": "user", "content": "Query"}]
        res = provider.generate_chat(
            "Give JSON", conversation_history=history, response_schema=SampleSchema
        )
        assert isinstance(res, SampleSchema)
        assert res.title == "Chat Schema"
        assert res.score == 0.88


# ---------------------------------------------------------------------------
# OpenRouterProvider Tests
# ---------------------------------------------------------------------------


def test_extract_json_text_helper():
    assert _extract_json_text('{"key": "value"}') == '{"key": "value"}'
    markdown_wrapped = '```json\n{"key": "value"}\n```'
    assert _extract_json_text(markdown_wrapped) == '{"key": "value"}'
    markdown_generic = '```\n{"key": "val"}\n```'
    assert _extract_json_text(markdown_generic) == '{"key": "val"}'


def test_openrouter_provider_generate_text():
    provider = OpenRouterProvider(
        api_key="sk-test", model_name="meta-llama/llama-3.3-70b-instruct"
    )
    mock_choice = MagicMock()
    mock_choice.message.content = "OpenRouter response"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(
        provider.client.chat.completions, "create", return_value=mock_response
    ) as mock_create:
        res = provider.generate_text("Test query")
        assert res == "OpenRouter response"
        mock_create.assert_called_once()


def test_openrouter_provider_generate_text_empty():
    provider = OpenRouterProvider(api_key="sk-test")
    mock_choice = MagicMock()
    mock_choice.message.content = None
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(
        provider.client.chat.completions, "create", return_value=mock_response
    ):
        res = provider.generate_text("Test query")
        assert res == ""


def test_openrouter_provider_generate_structured_success():
    provider = OpenRouterProvider(api_key="sk-test")
    mock_choice = MagicMock()
    mock_choice.message.content = (
        '```json\n{"title": "OpenRouter Extraction", "score": 0.99}\n```'
    )
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(
        provider.client.chat.completions, "create", return_value=mock_response
    ):
        res = provider.generate_structured("Parse prompt", response_schema=SampleSchema)
        assert isinstance(res, SampleSchema)
        assert res.title == "OpenRouter Extraction"
        assert res.score == 0.99


def test_openrouter_provider_generate_structured_empty_raises():
    provider = OpenRouterProvider(api_key="sk-test")
    mock_response = MagicMock()
    mock_response.choices = []

    with (
        patch.object(
            provider.client.chat.completions, "create", return_value=mock_response
        ),
        pytest.raises(RuntimeError, match="empty response"),
    ):
        provider.generate_structured("Parse prompt", response_schema=SampleSchema)


def test_openrouter_provider_generate_chat_with_history():
    provider = OpenRouterProvider(api_key="sk-test")
    mock_choice = MagicMock()
    mock_choice.message.content = "Chat turn answer"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(
        provider.client.chat.completions, "create", return_value=mock_response
    ) as mock_create:
        history = [
            {"role": "user", "content": "First turn"},
            {"role": "model", "parts": ["First answer"]},
        ]
        res = provider.generate_chat("Second turn", conversation_history=history)
        assert res == "Chat turn answer"
        called_args = mock_create.call_args[1]
        assert len(called_args["messages"]) == 3
        assert called_args["messages"][0]["role"] == "user"
        assert called_args["messages"][1]["role"] == "assistant"
        assert called_args["messages"][2]["role"] == "user"


def test_openrouter_provider_generate_chat_structured():
    provider = OpenRouterProvider(api_key="sk-test")
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(
        {"title": "Chat Structured", "score": 0.77}
    )
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(
        provider.client.chat.completions, "create", return_value=mock_response
    ):
        res = provider.generate_chat(
            "Extract structured info",
            conversation_history=[],
            response_schema=SampleSchema,
        )
        assert isinstance(res, SampleSchema)
        assert res.title == "Chat Structured"
        assert res.score == 0.77


# ---------------------------------------------------------------------------
# Integration with Classifier & AnswerGenerator under OpenRouter
# ---------------------------------------------------------------------------


def test_classifier_with_openrouter_provider():
    openrouter = OpenRouterProvider(api_key="sk-test")
    classifier = Classifier(llm_client=openrouter)

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(
        {
            "category": "Classical Ayurveda",
            "confidence": 0.96,
            "reason": "Triphala classical formulation classified via OpenRouter.",
        }
    )
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(
        openrouter.client.chat.completions, "create", return_value=mock_response
    ):
        ctx = MagicMock()
        ctx.raw_query = "What is the patent status of Triphala Churna?"
        out = classifier.classify(ctx)
        assert isinstance(out, ClassifierOutput)
        assert out.category == "Classical Ayurveda"
        assert out.confidence == 0.96


def test_answer_generator_with_openrouter_provider(tmp_path):
    manifest_file = tmp_path / "manifest.json"
    manifest_data = [{"doc_id": "patents-act-1970"}]
    manifest_file.write_text(json.dumps(manifest_data))

    openrouter = OpenRouterProvider(api_key="sk-test")
    gen = AnswerGenerator(manifest_path=str(manifest_file), llm_client=openrouter)

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(
        {
            "answer": "Section 3(p) bars traditional knowledge [1].",
            "citations": [
                {
                    "doc_id": "patents-act-1970",
                    "source_url": "https://indiacode.nic.in",
                    "doc_type": "statute",
                    "section": "Section 3(p)",
                    "date_retrieved": "2026-09-01",
                }
            ],
            "abs_flag": False,
            "disclaimer": config.DISCLAIMER_TEXT,
        }
    )
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(
        openrouter.client.chat.completions, "create", return_value=mock_response
    ):
        chunks = [
            {
                "doc_id": "patents-act-1970",
                "section": "Section 3(p)",
                "document_type": "statute",
                "source_url": "https://indiacode.nic.in",
                "date_retrieved": "2026-09-01",
                "content": "Section 3(p) statutory provision content",
                "similarity_score": 0.91,
            }
        ]
        res = gen.generate("Is neem patentable?", chunks=chunks)
        assert isinstance(res, GeneratorOutput)
        assert "[1]" in res.answer
        assert len(res.citations) == 1
        assert res.citations[0].doc_id == "patents-act-1970"
