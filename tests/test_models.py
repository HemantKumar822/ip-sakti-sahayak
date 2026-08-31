from src.models.request import QueryRequest
from src.models.response import Citation, QueryResponse


def test_query_request():
    req = QueryRequest(
        query_text="Can I patent my herbal formula?", session_id="test-session-123"
    )
    assert req.query_text == "Can I patent my herbal formula?"
    assert req.session_id == "test-session-123"


def test_citation_model():
    cit = Citation(
        doc_id="patents-act-1970-s3p",
        source_url="https://indiacode.nic.in/handle/123456789/1392",
        doc_type="statute",
        section="Section 3(p)",
        date_retrieved="2026-08-20",
        snippet="Section 3(p) details traditional knowledge...",
        relevance_score=0.89,
    )
    assert cit.doc_id == "patents-act-1970-s3p"
    assert cit.source_url == "https://indiacode.nic.in/handle/123456789/1392"
    assert cit.doc_type == "statute"
    assert cit.section == "Section 3(p)"
    assert cit.date_retrieved == "2026-08-20"
    assert cit.snippet == "Section 3(p) details traditional knowledge..."
    assert cit.relevance_score == 0.89


def test_query_response():
    cit = Citation(
        doc_id="patents-act-1970-s3p",
        snippet="Section 3(p) details...",
        relevance_score=0.89,
    )
    res = QueryResponse(
        status="answered",
        category="Proprietary Ayurveda",
        jurisdiction="India (MVP)",
        answer="Classical formulations are not patentable under Section 3(p).",
        citations=[cit],
        abs_flag=True,
        abs_detail="ABS clearance required.",
        confidence_score=0.92,
        abstention_message=None,
        disclaimer="This is for awareness only. Not legal advice.",
        response_time_ms=150,
    )
    assert res.status == "answered"
    assert res.category == "Proprietary Ayurveda"
    assert res.jurisdiction == "India (MVP)"
    assert res.answer.startswith("Classical formulations")
    assert len(res.citations) == 1
    assert res.abs_flag is True
    assert res.abs_detail == "ABS clearance required."
    assert res.confidence_score == 0.92
    assert res.abstention_message is None
    assert res.response_time_ms == 150


def test_query_response_defaults():
    res = QueryResponse()
    assert res.status == "answered"
    assert res.category is None
    assert res.jurisdiction == "India (MVP)"
    assert res.answer is None
    assert res.citations == []
    assert res.abs_flag is False
    assert res.abs_detail is None
    assert res.confidence_score is None
    assert res.abstention_message is None
    assert "awareness" in res.disclaimer
    assert res.response_time_ms == 0
