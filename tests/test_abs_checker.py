from typing import Any
from unittest.mock import MagicMock

import pytest

from src.pipeline.abs_tkdl_checker import (
    ABSChecker,
    ABSCheckerOutput,
    ABSTKDLChecker,
)
from src.vector_store.base import VectorStore


class DummyVectorStore(VectorStore):
    """Test vector store supporting customizable search results and count."""

    def __init__(
        self,
        results: list[dict[str, Any]] | None = None,
        item_count: int = 5,
    ) -> None:
        self._results = results or []
        self._count = item_count

    def add(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        self._count += len(documents)

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self._results[:n_results]

    def count(self) -> int:
        return self._count


def test_abs_checker_output_model_defaults():
    """Verify ABSCheckerOutput default values and field assignment."""
    output = ABSCheckerOutput()
    assert output.abs_flag is False
    assert output.abs_detail is None
    assert output.citations == []
    assert output.similarity_score == 0.0

    custom = ABSCheckerOutput(
        abs_flag=True,
        abs_detail="BDA 2002 clearance required.",
        citations=[{"doc_id": "bda-2002"}],
        similarity_score=0.88,
    )
    assert custom.abs_flag is True
    assert "BDA 2002" in custom.abs_detail
    assert len(custom.citations) == 1
    assert custom.similarity_score == 0.88


def test_abs_checker_positive_biological_resource():
    """Verify that a biological resource query triggers ABS flag with full statutory citation."""
    mock_results = [
        {
            "id": "bda-2002#chunk_1",
            "doc_id": "bda-2002",
            "snippet": "Section 6: Prior approval of NBA required for application for intellectual property rights.",
            "similarity_score": 0.82,
            "metadata": {
                "doc_id": "bda-2002",
                "doc_type": "statute",
                "title": "Biological Diversity Act, 2002",
                "section_heading": "Section 6 - Application for IPR",
                "source_url": "https://indiacode.nic.in/handle/123456789/2046",
            },
        }
    ]
    store = DummyVectorStore(results=mock_results, item_count=1)
    checker = ABSTKDLChecker(vector_store=store, threshold=0.55)

    result = checker.check(
        "I want to patent a formulation with Ashwagandha root extract"
    )

    assert result.abs_flag is True
    assert result.abs_detail is not None
    assert "Biological Diversity Act, 2002" in result.abs_detail
    assert "Section 6" in result.abs_detail
    assert "https://indiacode.nic.in/handle/123456789/2046" in result.abs_detail
    assert len(result.citations) == 1
    assert result.similarity_score == pytest.approx(0.82)


def test_abs_checker_negative_non_biological_resource():
    """Verify that non-biological queries do not trigger ABS flag."""
    mock_results = [
        {
            "id": "tm-1999#chunk_2",
            "doc_id": "trademarks-act-1999",
            "snippet": "Section 9: Absolute grounds for refusal of registration.",
            "similarity_score": 0.75,
            "metadata": {
                "doc_id": "trademarks-act-1999",
                "doc_type": "statute",
                "title": "Trade Marks Act, 1999",
                "section_heading": "Section 9",
                "source_url": "https://indiacode.nic.in/handle/123456789/1993",
            },
        }
    ]
    store = DummyVectorStore(results=mock_results, item_count=1)
    checker = ABSTKDLChecker(vector_store=store, threshold=0.55)

    result = checker.check("Can I register a trademark for my software brand logo?")

    assert result.abs_flag is False
    assert result.abs_detail is None
    assert result.citations == []
    assert result.similarity_score == 0.0


def test_abs_checker_score_below_threshold():
    """Verify that an ABS match below threshold does not trigger abs_flag."""
    mock_results = [
        {
            "id": "bda-2002#chunk_1",
            "doc_id": "bda-2002",
            "snippet": "Section 3: Certain persons not to undertake Biodiversity related activities without approval.",
            "similarity_score": 0.42,
            "metadata": {
                "doc_id": "bda-2002",
                "doc_type": "statute",
                "title": "Biological Diversity Act, 2002",
                "section_heading": "Section 3",
                "source_url": "https://indiacode.nic.in/handle/123456789/2046",
            },
        }
    ]
    store = DummyVectorStore(results=mock_results, item_count=1)
    checker = ABSTKDLChecker(vector_store=store, threshold=0.55)

    result = checker.check("General query mentioning herbs vaguely")

    assert result.abs_flag is False
    assert result.abs_detail is None
    assert len(result.citations) == 1
    assert result.similarity_score == pytest.approx(0.42)


def test_abs_checker_empty_and_whitespace_queries():
    """Verify that empty or whitespace strings return safe default outputs."""
    checker = ABSTKDLChecker(vector_store=DummyVectorStore())

    for empty_input in ["", "   ", "\t\n"]:
        res = checker.check(empty_input)
        assert res.abs_flag is False
        assert res.abs_detail is None
        assert res.citations == []
        assert res.similarity_score == 0.0


def test_abs_checker_empty_vector_store():
    """Verify behavior when vector store has 0 documents."""
    store = DummyVectorStore(results=[], item_count=0)
    checker = ABSTKDLChecker(vector_store=store)

    res = checker.check("Ashwagandha commercial extract")
    assert res.abs_flag is False
    assert res.abs_detail is None
    assert res.citations == []
    assert res.similarity_score == 0.0


def test_abs_checker_top_k_limits():
    """Verify top_k parameter overrides."""
    store = DummyVectorStore(results=[], item_count=5)
    checker = ABSTKDLChecker(vector_store=store, top_k=3)
    assert checker.top_k == 3

    # If limit <= 0, returns early safely
    res = checker.check("Ashwagandha", top_k=0)
    assert res.abs_flag is False
    assert res.abs_detail is None


def test_abs_checker_vector_store_exceptions():
    """Verify resilience when vector store raises unexpected exceptions."""
    mock_store = MagicMock(spec=VectorStore)
    mock_store.count.side_effect = RuntimeError("Chroma connection lost")

    checker = ABSTKDLChecker(vector_store=mock_store)
    res = checker.check("Neem and Turmeric formulation")
    assert res.abs_flag is False
    assert res.abs_detail is None

    # Error during search
    mock_store.count.side_effect = None
    mock_store.count.return_value = 10
    mock_store.search.side_effect = ValueError("Query embedding failed")

    res2 = checker.check("Neem and Turmeric formulation")
    assert res2.abs_flag is False
    assert res2.abs_detail is None


def test_is_abs_document_identification():
    """Verify metadata and identifier inspection rules in is_abs_document."""
    checker = ABSTKDLChecker(vector_store=DummyVectorStore())

    # Direct identifier in doc_id
    assert checker.is_abs_document({"doc_id": "bda-2002"}) is True
    assert checker.is_abs_document({"doc_id": "tkdl-prior-art-01"}) is True
    assert checker.is_abs_document({"doc_id": "patents-act-1970-s3p"}) is True

    # Identifier in doc_type
    assert checker.is_abs_document({"doc_type": "abs"}) is True
    assert checker.is_abs_document({"document_type": "tkdl"}) is True

    # Identifier in title or source_url
    assert (
        checker.is_abs_document(
            {"title": "National Biodiversity Authority (NBA) Guidelines"}
        )
        is True
    )
    assert (
        checker.is_abs_document({"source_url": "https://nbaindia.org/guidelines"})
        is True
    )

    # Identifier in section heading
    assert (
        checker.is_abs_document(
            {
                "doc_id": "generic-law",
                "section_heading": "Biological Diversity Act Section 6",
            }
        )
        is True
    )

    # Non-ABS document
    assert (
        checker.is_abs_document(
            {
                "doc_id": "designs-act-2000",
                "doc_type": "statute",
                "title": "Designs Act, 2000",
                "source_url": "https://ipindia.gov.in",
            }
        )
        is False
    )


def test_abs_checker_alias_and_custom_threshold():
    """Verify ABSChecker alias and dynamic threshold override."""
    mock_results = [
        {
            "id": "tkdl-1",
            "doc_id": "tkdl-excerpt",
            "snippet": "Traditional medicinal knowledge formulation for skin ailments.",
            "score": 0.48,
            "metadata": {
                "doc_id": "tkdl-excerpt",
                "title": "TKDL Classical Archive",
                "section": "Ayurveda Formulation",
            },
        }
    ]
    store = DummyVectorStore(results=mock_results, item_count=1)

    # With high threshold (0.60), should not trigger
    checker_high = ABSChecker(vector_store=store, threshold=0.60)
    assert checker_high.check("Traditional oil").abs_flag is False

    # With lower threshold (0.45), should trigger
    checker_low = ABSChecker(vector_store=store, threshold=0.45)
    res_low = checker_low.check("Traditional oil")
    assert res_low.abs_flag is True
    assert "TKDL Classical Archive" in res_low.abs_detail
    assert res_low.similarity_score == pytest.approx(0.48)


def test_abs_checker_score_fallbacks():
    """Verify score resolution when similarity_score is absent and relevance_score or default is used."""
    # Test relevance_score fallback
    results_with_relevance = [
        {
            "id": "bda-chunk-1",
            "metadata": {"doc_id": "bda-2002", "title": "Biological Diversity Act"},
            "relevance_score": 0.77,
        }
    ]
    store1 = DummyVectorStore(results=results_with_relevance, item_count=1)
    checker1 = ABSTKDLChecker(vector_store=store1)
    res1 = checker1.check("Biodiversity query")
    assert res1.abs_flag is True
    assert res1.similarity_score == pytest.approx(0.77)

    # Test default fallback score (1.0)
    results_without_score = [
        {
            "id": "bda-chunk-2",
            "metadata": {"doc_id": "bda-2002"},
        }
    ]
    store2 = DummyVectorStore(results=results_without_score, item_count=1)
    checker2 = ABSTKDLChecker(vector_store=store2)
    res2 = checker2.check("Biodiversity query")
    assert res2.abs_flag is True
    assert res2.similarity_score == pytest.approx(1.0)
