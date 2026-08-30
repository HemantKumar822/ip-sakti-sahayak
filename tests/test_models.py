from src.models.request import QueryRequest
from src.models.response import Citation, QueryResponse


def test_query_request():
    req = QueryRequest(query_text="Can I patent my herbal formula?", session_id="test-session-123")
    assert req.query_text == "Can I patent my herbal formula?"
    assert req.session_id == "test-session-123"


def test_citation_model():
    cit = Citation(document_id="doc-001", snippet="Section 3(p) details...", relevance_score=0.89)
    assert cit.document_id == "doc-001"
    assert cit.snippet == "Section 3(p) details..."
    assert cit.relevance_score == 0.89


def test_query_response():
    cit = Citation(document_id="doc-001", snippet="Section 3(p) details...", relevance_score=0.89)
    res = QueryResponse(
        answer="Classical formulations are not patentable under Section 3(p).",
        citations=[cit],
        requires_abs_compliance=True,
        confidence_score=0.92,
    )
    assert res.answer.startswith("Classical formulations")
    assert len(res.citations) == 1
    assert res.requires_abs_compliance is True
    assert res.confidence_score == 0.92
