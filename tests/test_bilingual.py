"""Unit and integration test suite for the Bilingual Normalizer and Terminology Bridge.

Executes 100% offline without invoking external LLMs or consuming API quota.
"""

from src.pipeline.bilingual import BilingualNormalizer
from src.pipeline.hybrid_retriever import HybridRetriever
from src.vector_store.chroma_store import ChromaStore


def test_is_hindi_detection():
    # Pure Devanagari Hindi
    assert BilingualNormalizer.is_hindi("क्या अश्वगंधा पर पेटेंट मिल सकता है?") is True
    assert BilingualNormalizer.is_hindi("त्रिफला चूर्ण") is True

    # Mixed Hinglish / Devanagari
    assert BilingualNormalizer.is_hindi("Ashwagandha का पेटेंट") is True

    # Pure English
    assert (
        BilingualNormalizer.is_hindi("Can Ashwagandha be patented in India?") is False
    )
    assert BilingualNormalizer.is_hindi("Biological Diversity Act Section 6") is False


def test_bilingual_expansion_ayurveda_terms():
    query = "क्या अश्वगंधा और त्रिफला पर पेटेंट और जैव विविधता नियम लागू होते हैं?"
    result = BilingualNormalizer.expand_query(query)

    assert result.is_hindi is True
    assert "अश्वगंधा" in result.matched_terms
    assert "त्रिफला" in result.matched_terms
    assert "पेटेंट" in result.matched_terms
    assert "जैव विविधता" in result.matched_terms

    expanded = result.expanded_search_query
    assert "Ashwagandha" in expanded
    assert "Triphala" in expanded
    assert "patent" in expanded
    assert "Biological Diversity" in expanded


def test_bilingual_expansion_english_unchanged():
    query = "Is Chyawanprash eligible for patent protection in India?"
    result = BilingualNormalizer.expand_query(query)

    assert result.is_hindi is False
    assert result.expanded_search_query == query
    assert result.matched_terms == []


import os

import pytest


def test_bilingual_retrieval_parity_offline():
    """Verifies that paired English and Hindi queries retrieve the same statutory citations offline."""
    if not os.path.exists("corpus/embeddings"):
        pytest.skip("Requires local vector DB (corpus/embeddings)")

    retriever = HybridRetriever(vector_store=ChromaStore())

    en_query = "Can Triphala be patented under Indian patent law?"
    hi_query = "क्या त्रिफला पर भारतीय कानून के तहत पेटेंट मिल सकता है?"

    # Expand Hindi query
    hi_expanded = BilingualNormalizer.expand_query(hi_query)
    assert hi_expanded.is_hindi is True

    # Retrieve top chunks for both
    en_chunks = retriever.retrieve(en_query, top_k=5)
    hi_chunks = retriever.retrieve(hi_expanded.expanded_search_query, top_k=5)

    assert len(en_chunks) > 0
    assert len(hi_chunks) > 0

    # Both must identify relevant statutory and guideline publications
    en_docs = {
        c.get("metadata", {}).get("doc_id") or c.get("doc_id") for c in en_chunks
    }
    hi_docs = {
        c.get("metadata", {}).get("doc_id") or c.get("doc_id") for c in hi_chunks
    }

    # Verify significant statutory corpus intersection
    common_docs = en_docs.intersection(hi_docs)
    assert (
        len(common_docs) > 0
    ), f"Expected common documents between EN and HI, got {en_docs} and {hi_docs}"

    # Verify that the Hindi query identifies Indian patent examination guidance or Patents Act
    assert any("patent" in str(d) or "guidelines" in str(d) for d in hi_docs)

    # Max score for Hindi query should cross the 0.65 confidence threshold
    hi_max_score = max(c.get("similarity_score", 0.0) for c in hi_chunks)
    assert (
        hi_max_score >= 0.65
    ), f"Expected Hindi retrieval score >= 0.65, got {hi_max_score}"
