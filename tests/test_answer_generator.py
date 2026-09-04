import json
from unittest.mock import patch

import pytest

from src.config import config
from src.pipeline.answer_generator import (
    AnswerGenerator,
    GeneratorOutput,
)


class MockGenerateContentResponse:
    def __init__(self, text: str):
        self.text = text


@pytest.fixture
def sample_chunks():
    return [
        {
            "doc_id": "patents-act-1970",
            "section": "Section 3(p)",
            "document_type": "statute",
            "source_url": "https://indiacode.nic.in/handle/123456789/1392",
            "date_retrieved": "2026-08-31",
            "content": "Section 3(p) provides that an invention which in effect is traditional knowledge is not patentable.",
            "similarity_score": 0.85,
        },
        {
            "doc_id": "tkdl-neem-turmeric-prior-art",
            "section": "Case Study 1",
            "document_type": "policy",
            "source_url": "https://www.csir.res.in/tkdl-success-stories",
            "date_retrieved": "2026-08-31",
            "content": "TKDL documentation prevents patenting of turmeric and neem traditional remedies.",
            "similarity_score": 0.78,
        },
    ]


@pytest.fixture
def answer_generator(tmp_path, monkeypatch):
    manifest_file = tmp_path / "manifest.json"
    manifest_data = [
        {"doc_id": "patents-act-1970"},
        {"doc_id": "tkdl-neem-turmeric-prior-art"},
        {"doc_id": "tkdl-overview"},
    ]
    manifest_file.write_text(json.dumps(manifest_data))
    monkeypatch.setattr(config, "CORPUS_MANIFEST_PATH", str(manifest_file))
    return AnswerGenerator(manifest_path=str(manifest_file))


def test_answer_generator_success(answer_generator, sample_chunks):
    mock_payload = {
        "answer": "Under Section 3(p) of the Patents Act [1], traditional knowledge formulations cannot be patented. TKDL documentation further supports prior art defense [2].",
        "citations": [
            {
                "doc_id": "patents-act-1970",
                "source_url": "https://indiacode.nic.in/handle/123456789/1392",
                "doc_type": "statute",
                "section": "Section 3(p)",
                "date_retrieved": "2026-08-31",
            },
            {
                "doc_id": "tkdl-neem-turmeric-prior-art",
                "source_url": "https://www.csir.res.in/tkdl-success-stories",
                "doc_type": "policy",
                "section": "Case Study 1",
                "date_retrieved": "2026-08-31",
            },
        ],
        "abs_flag": False,
        "disclaimer": config.DISCLAIMER_TEXT,
    }

    mock_resp = MockGenerateContentResponse(json.dumps(mock_payload))
    with patch.object(
        answer_generator.model, "generate_content", return_value=mock_resp
    ):
        res = answer_generator.generate(
            query="Can I patent a classical neem remedy?",
            chunks=sample_chunks,
            product_category="Classical Ayurveda",
            abs_flag=False,
        )

        assert isinstance(res, GeneratorOutput)
        assert "[1]" in res.answer
        assert "[2]" in res.answer
        assert len(res.citations) == 2
        assert res.citations[0].doc_id == "patents-act-1970"
        assert res.citations[0].section == "Section 3(p)"
        assert res.citations[1].doc_id == "tkdl-neem-turmeric-prior-art"
        assert res.abs_flag is False
        assert res.disclaimer == config.DISCLAIMER_TEXT


def test_answer_generator_disclaimer_enforced(answer_generator, sample_chunks):
    # If Gemini returns an altered disclaimer, generator must enforce the canonical one
    mock_payload = {
        "answer": "Formulations are not patentable [1].",
        "citations": [
            {
                "doc_id": "patents-act-1970",
                "source_url": "https://indiacode.nic.in",
                "doc_type": "statute",
                "section": "Section 3(p)",
                "date_retrieved": "2026-08-31",
            }
        ],
        "abs_flag": True,
        "disclaimer": "Some paraphrased disclaimer.",
    }
    mock_resp = MockGenerateContentResponse(json.dumps(mock_payload))
    with patch.object(
        answer_generator.model, "generate_content", return_value=mock_resp
    ):
        res = answer_generator.generate(
            query="Can I patent this?",
            chunks=sample_chunks,
            abs_flag=True,
        )
        assert res.disclaimer == config.DISCLAIMER_TEXT
        assert res.abs_flag is True


def test_answer_generator_invalid_doc_id_p0_bug_abstains(
    answer_generator, sample_chunks
):
    # Citation has hallucinated doc_id not in manifest or chunks -> must abstain
    mock_payload = {
        "answer": "According to hallucinated law [1], this is allowed.",
        "citations": [
            {
                "doc_id": "hallucinated-fake-act-9999",
                "source_url": "https://fake.law",
                "doc_type": "statute",
                "section": "Section 999",
                "date_retrieved": "2026-08-31",
            }
        ],
        "abs_flag": False,
        "disclaimer": config.DISCLAIMER_TEXT,
    }
    mock_resp = MockGenerateContentResponse(json.dumps(mock_payload))
    with patch.object(
        answer_generator.model, "generate_content", return_value=mock_resp
    ):
        res = answer_generator.generate(
            query="Can I patent this?",
            chunks=sample_chunks,
        )
        # Should fallback to abstention, empty citations
        assert res.citations == []
        assert res.disclaimer == config.DISCLAIMER_TEXT
        assert (
            "cannot provide a confident advisory" in res.answer
            or "unable" in res.answer
        )


def test_answer_generator_gemini_api_failure(answer_generator, sample_chunks):
    with patch.object(
        answer_generator.model,
        "generate_content",
        side_effect=Exception("API Network Timeout"),
    ):
        res = answer_generator.generate(
            query="Can I patent this?",
            chunks=sample_chunks,
        )
        assert isinstance(res, GeneratorOutput)
        assert res.citations == []
        assert res.disclaimer == config.DISCLAIMER_TEXT


def test_answer_generator_invalid_json_fallback(answer_generator, sample_chunks):
    mock_resp = MockGenerateContentResponse("INVALID_NON_JSON_STRING")
    with patch.object(
        answer_generator.model, "generate_content", return_value=mock_resp
    ):
        res = answer_generator.generate(
            query="Can I patent this?",
            chunks=sample_chunks,
        )
        assert isinstance(res, GeneratorOutput)
        assert res.citations == []
        assert res.disclaimer == config.DISCLAIMER_TEXT


def test_answer_generator_empty_chunks(answer_generator):
    res = answer_generator.generate(
        query="Can I patent this?",
        chunks=[],
    )
    assert isinstance(res, GeneratorOutput)
    assert res.citations == []
    assert res.disclaimer == config.DISCLAIMER_TEXT


def test_answer_generator_none_chunks(answer_generator):
    res = answer_generator.generate(
        query="Can I patent this?",
        chunks=None,
    )
    assert isinstance(res, GeneratorOutput)
    assert res.citations == []
    assert res.disclaimer == config.DISCLAIMER_TEXT


def test_answer_generator_timeout_fallback(answer_generator, sample_chunks):
    with patch.object(
        answer_generator.model,
        "generate_content",
        side_effect=TimeoutError("Gemini Request Timed Out"),
    ):
        res = answer_generator.generate(
            query="Can I patent this?",
            chunks=sample_chunks,
        )
        assert isinstance(res, GeneratorOutput)
        assert res.citations == []
        assert res.disclaimer == config.DISCLAIMER_TEXT
        assert res.answer == config.ABSTENTION_MESSAGE


def test_answer_generator_rate_limit_429(answer_generator, sample_chunks):
    with patch.object(
        answer_generator.model,
        "generate_content",
        side_effect=Exception("429 ResourceExhausted: Quota exceeded"),
    ):
        res = answer_generator.generate(
            query="Can I patent this?",
            chunks=sample_chunks,
        )
        assert isinstance(res, GeneratorOutput)
        assert res.citations == []
        assert "high traffic and has hit its API rate limits" in res.answer
        assert res.disclaimer == config.DISCLAIMER_TEXT


def test_answer_generator_unrecoverable_api_key_error(answer_generator, sample_chunks):
    with (
        patch.object(
            answer_generator.model,
            "generate_content",
            side_effect=RuntimeError("API key not valid. Please pass a valid API key."),
        ),
        pytest.raises(RuntimeError, match="Gemini API key error"),
    ):
        answer_generator.generate(
            query="Can I patent this?",
            chunks=sample_chunks,
        )


def test_answer_generator_conversation_history_timeout_fallback(
    answer_generator, sample_chunks
):
    from unittest.mock import MagicMock

    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = TimeoutError("Multi-turn chat timeout")
    with patch.object(answer_generator.model, "start_chat", return_value=mock_chat):
        res = answer_generator.generate(
            query="Can I patent this formulation?",
            chunks=sample_chunks,
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "How can I help?"},
            ],
        )
        assert isinstance(res, GeneratorOutput)
        assert res.citations == []
        assert res.disclaimer == config.DISCLAIMER_TEXT


def test_answer_generator_conversational_timeout_fallback(answer_generator):
    with patch.object(
        answer_generator.model,
        "generate_content",
        side_effect=TimeoutError("Conversational timeout"),
    ):
        res = answer_generator.generate_conversational(query="hello")
        assert isinstance(res, GeneratorOutput)
        assert "help you with ayurveda ip" in res.answer.lower()
        assert res.citations == []


def test_answer_generator_refusal_timeout_fallback(answer_generator):
    with patch.object(
        answer_generator.model,
        "generate_content",
        side_effect=TimeoutError("Refusal timeout"),
    ):
        refusal = answer_generator.generate_refusal(query="Who won the World Cup?")
        assert isinstance(refusal, str)
        assert "cannot assist with this query" in refusal.lower()
