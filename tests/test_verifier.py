"""Unit test suite for the deterministic GroundingVerifier (VERIFY stage).

Executes 100% offline without invoking external LLMs or consuming API quota.
"""

from src.models.response import Citation
from src.pipeline.verifier import GroundingVerifier


def test_extract_inline_citation_indices():
    text = "Section 3(p) excludes traditional recipes [1]. ABS clearance is also needed [2, 3] under Section 6 [4]."
    indices = GroundingVerifier.extract_inline_citation_indices(text)
    assert indices == [1, 2, 3, 4]


def test_verifier_perfect_grounded_answer():
    verifier = GroundingVerifier()
    answer = "Under Section 3(p) of the Patents Act [1], traditional recipes are barred. Section 6 requires ABS [2]."
    citations = [
        Citation(
            doc_id="patents-act-1970",
            source_url="https://ipindia.gov.in",
            doc_type="statute",
            section="Section 3(p)",
            date_retrieved="2026-08-30",
        ),
        Citation(
            doc_id="bda-2002",
            source_url="https://nbaindia.org",
            doc_type="statute",
            section="Section 6",
            date_retrieved="2026-08-30",
        ),
    ]
    chunks = [
        {"doc_id": "patents-act-1970", "snippet": "Section 3(p) text..."},
        {"doc_id": "bda-2002", "snippet": "Section 6 text..."},
        {"doc_id": "novartis-2013", "snippet": "Novartis ruling..."},
    ]

    result = verifier.verify(answer, citations, chunks)
    assert result.is_verified is True
    assert result.grounding_score == 1.0
    assert result.status == "verified"
    assert any("PASSED" in note for note in result.audit_trail)


def test_verifier_catches_unmatched_inline_markers():
    verifier = GroundingVerifier()
    # Citation [3] is cited, but only 2 citations are provided
    answer = "Inventions are not patentable [1]. Furthermore, see case law [3]."
    citations = [
        Citation(
            doc_id="patents-act-1970",
            source_url="https://ipindia.gov.in",
            doc_type="statute",
            section="Section 3(p)",
            date_retrieved="2026-08-30",
        ),
        Citation(
            doc_id="bda-2002",
            source_url="https://nbaindia.org",
            doc_type="statute",
            section="Section 6",
            date_retrieved="2026-08-30",
        ),
    ]
    chunks = [
        {"doc_id": "patents-act-1970", "snippet": "Section 3(p) text..."},
        {"doc_id": "bda-2002", "snippet": "Section 6 text..."},
    ]

    result = verifier.verify(answer, citations, chunks)
    assert result.is_verified is False
    assert result.grounding_score == 0.0
    assert result.status == "unverified_citations"
    assert any("FAILED: Inline markers [3]" in note for note in result.audit_trail)


def test_verifier_catches_invented_or_unretrieved_doc_ids():
    verifier = GroundingVerifier()
    answer = "Under European Patent Convention Article 52 [1], rules apply."
    citations = [
        Citation(
            doc_id="epc-article-52-invented",
            source_url="https://epo.org",
            doc_type="statute",
            section="Article 52",
            date_retrieved="2026-08-30",
        )
    ]
    # Retrieved chunks only contained Indian Patents Act
    chunks = [
        {"doc_id": "patents-act-1970", "snippet": "Section 3(p) text..."},
    ]

    result = verifier.verify(answer, citations, chunks)
    assert result.is_verified is False
    assert result.grounding_score == 0.0
    assert result.status == "ungrounded"
    assert any(
        "FAILED: Citations reference unretrieved doc_ids" in note
        for note in result.audit_trail
    )


def test_verifier_empty_answer_handling():
    verifier = GroundingVerifier()
    result = verifier.verify("", [], [])
    assert result.is_verified is False
    assert result.grounding_score == 0.0
    assert result.status == "ungrounded"


def test_verifier_dict_input_compatibility():
    verifier = GroundingVerifier()
    answer = "Traditional medicine guidance applies [1]."
    citations_dict = [
        {
            "doc_id": "ayush-guidelines-2025",
            "source_url": "https://ayush.gov.in",
            "doc_type": "guideline",
            "section": "Guideline 4",
            "date_retrieved": "2026-08-30",
        }
    ]
    chunks = [
        {
            "metadata": {"doc_id": "ayush-guidelines-2025"},
            "chunk_text": "Ayush examination guideline 4...",
        }
    ]

    result = verifier.verify(answer, citations_dict, chunks)
    assert result.is_verified is True
    assert result.grounding_score == 1.0
    assert result.status == "verified"
