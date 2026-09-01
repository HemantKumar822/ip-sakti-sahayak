import asyncio
from unittest.mock import MagicMock, patch

from src.config import config
from src.pipeline.abs_tkdl_checker import ABSCheckerOutput
from src.pipeline.answer_generator import Citation as GenCitation
from src.pipeline.answer_generator import GeneratorOutput
from src.pipeline.classifier import ClassifierOutput
from src.pipeline.confidence_gate import ConfidenceGateOutput
from src.pipeline.jurisdiction_router import RouterOutput
from src.pipeline.orchestrator import PipelineOrchestrator, run_pipeline


def test_orchestrator_generate_answered_success():
    """Test full pipeline execution when answer is generated and citations are returned."""
    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = ClassifierOutput(
        category="Classical Ayurveda",
        confidence=0.95,
        reason="Triphala is a classical recipe.",
    )

    mock_router = MagicMock()
    mock_router.route.return_value = RouterOutput(
        jurisdiction="India",
        applicable_laws=["The Patents Act, 1970"],
        confidence=0.9,
    )

    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
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

    mock_abs = MagicMock()
    mock_abs.check.return_value = ABSCheckerOutput(
        abs_flag=False,
        abs_detail=None,
        citations=[],
        similarity_score=0.2,
    )

    mock_gate = MagicMock()
    mock_gate.evaluate.return_value = ConfidenceGateOutput(
        decision="generate",
        max_score=0.88,
        mean_score=0.88,
        retrieved_count=1,
        chunks=mock_retriever.retrieve.return_value,
    )

    mock_gen = MagicMock()
    mock_gen.generate.return_value = GeneratorOutput(
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

    orchestrator = PipelineOrchestrator(
        classifier=mock_classifier,
        jurisdiction_router=mock_router,
        retriever=mock_retriever,
        abs_checker=mock_abs,
        confidence_gate=mock_gate,
        answer_generator=mock_gen,
    )

    response = asyncio.run(
        orchestrator.run_pipeline(
            query_text="Can I patent a classical Triphala formulation in India?",
            session_id="session-123",
        )
    )

    assert response.status == "answered"
    assert response.category == "Classical Ayurveda"
    assert response.jurisdiction == "India"
    assert "Section 3(p)" in response.answer
    assert len(response.citations) == 1
    assert response.citations[0].doc_id == "patents-act-1970"
    assert response.abs_flag is False
    assert response.abstention_message is None
    assert response.disclaimer == config.DISCLAIMER_TEXT
    assert response.response_time_ms >= 0


def test_orchestrator_abstain_on_low_confidence():
    """Test pipeline execution when confidence gate abstains due to low retrieval score."""
    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = ClassifierOutput(
        category="Unclassifiable",
        confidence=0.1,
        reason="Not Ayurveda.",
    )

    mock_router = MagicMock()
    mock_router.route.return_value = RouterOutput(
        jurisdiction="India",
        applicable_laws=[],
        confidence=0.5,
    )

    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []

    mock_abs = MagicMock()
    mock_abs.check.return_value = ABSCheckerOutput(
        abs_flag=False,
        abs_detail=None,
        citations=[],
        similarity_score=0.1,
    )

    mock_gate = MagicMock()
    mock_gate.evaluate.return_value = ConfidenceGateOutput(
        decision="abstain",
        max_score=0.1,
        mean_score=0.1,
        retrieved_count=0,
        chunks=[],
    )

    mock_gen = MagicMock()
    mock_gen.generate_refusal.return_value = "Mocked dynamic refusal message"

    orchestrator = PipelineOrchestrator(
        classifier=mock_classifier,
        jurisdiction_router=mock_router,
        retriever=mock_retriever,
        abs_checker=mock_abs,
        confidence_gate=mock_gate,
        answer_generator=mock_gen,
    )

    response = asyncio.run(
        orchestrator.run_pipeline(
            query_text="What is the patent status of quantum computing semiconductor?",
            session_id="session-456",
        )
    )

    assert response.status == "abstained"
    assert response.answer is None
    assert response.citations == []
    assert response.abstention_message == "Mocked dynamic refusal message"
    assert response.disclaimer == config.DISCLAIMER_TEXT
    mock_gen.generate.assert_not_called()
    mock_gen.generate_refusal.assert_called_once_with(query="What is the patent status of quantum computing semiconductor?")


def test_run_pipeline_wrapper_function():
    """Test top-level run_pipeline convenience function."""
    with (
        patch(
            "src.pipeline.classifier.Classifier.classify",
            return_value=ClassifierOutput(
                category="Herbal Formulations",
                confidence=0.9,
                reason="Herbal formulation query.",
            ),
        ),
        patch(
            "src.pipeline.jurisdiction_router.JurisdictionRouter.route",
            return_value=RouterOutput(
                jurisdiction="India",
                applicable_laws=["The Patents Act, 1970"],
                confidence=0.9,
            ),
        ),
        patch("src.pipeline.retriever.Retriever.retrieve", return_value=[]),
        patch(
            "src.pipeline.abs_tkdl_checker.ABSChecker.check",
            return_value=ABSCheckerOutput(
                abs_flag=False, abs_detail=None, citations=[], similarity_score=0.1
            ),
        ),
        patch(
            "src.pipeline.confidence_gate.ConfidenceGate.evaluate",
            return_value=ConfidenceGateOutput(
                decision="abstain",
                max_score=0.1,
                mean_score=0.1,
                retrieved_count=0,
                chunks=[],
            ),
        ),
        patch(
            "src.pipeline.answer_generator.AnswerGenerator.generate_refusal",
            return_value="Mocked dynamic refusal message",
        ),
    ):
        res = asyncio.run(
            run_pipeline(
                query="Can I patent Ashwagandha extract?", session_id="test-session"
            )
        )
        assert res.status == "abstained"
        assert res.category == "Herbal Formulations"
        assert res.disclaimer == config.DISCLAIMER_TEXT
