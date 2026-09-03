from unittest.mock import patch

from src.models.query_context import QueryContext
from src.pipeline.classifier import ClassifierOutput
from src.pipeline.jurisdiction_router import JurisdictionRouter, RouterOutput


def test_default_routing_standard_ayurveda_query():
    """Verifies that standard Indian domestic queries route to India with status 'routed'."""
    router = JurisdictionRouter()
    queries = [
        "Can I patent a Classical Ayurveda formulation of Chyawanprash?",
        "What are the requirements under the Biological Diversity Act 2002?",
        "Section 3(p) of the Patents Act 1970 and traditional knowledge",
        "How do I register a trademark for herbal cosmetics in India?",
    ]

    for q in queries:
        ctx = QueryContext(raw_query=q, english_keywords="", is_hindi=False)
        result = router.route(ctx)
        assert isinstance(result, RouterOutput)
        assert result.jurisdiction == "India"
        assert result.corpus_tag == "india"
        assert result.status == "routed"
        assert result.message is None


def test_international_scope_detection():
    """Verifies that queries mentioning international treaties or frameworks are flagged."""
    router = JurisdictionRouter()
    international_queries = [
        "How do I file a PCT patent application for an Ayurvedic medicine?",
        "Does the Patent Cooperation Treaty apply to biological resources?",
        "What does TRIPS agreement say about traditional knowledge protection?",
        "Can I file a trademark under the Madrid Protocol for my herbal brand?",
        "What are the WIPO guidelines for genetic resources?",
        "Is my patent application eligible at USPTO?",
        "How does the EPO examine biotechnology inventions?",
        "Does the Paris Convention grant priority rights for Indian patents?",
    ]

    for q in international_queries:
        ctx = QueryContext(raw_query=q, english_keywords="", is_hindi=False)
        result = router.route(ctx)
        assert isinstance(result, RouterOutput)
        assert result.jurisdiction == "India"
        assert result.corpus_tag == "india"
        assert result.status == "out_of_scope_international"
        assert result.message is not None
        assert "international IP frameworks" in result.message


def test_no_false_positives_for_substrings():
    """Ensures word-boundary matching does not falsely flag regular words containing acronyms."""
    router = JurisdictionRouter()
    benign_queries = [
        "I took a picture of the plant for the application.",
        "We are planning an inspection trip to the laboratory.",
        "Epoxy resins in herbal packaging materials.",
    ]

    for q in benign_queries:
        ctx = QueryContext(raw_query=q, english_keywords="", is_hindi=False)
        result = router.route(ctx)
        assert result.status == "routed"
        assert result.message is None


def test_empty_and_whitespace_query():
    """Verifies empty or whitespace queries default to routed without international flag."""
    router = JurisdictionRouter()
    for empty_q in ["", "   ", "\n\t"]:
        ctx = QueryContext(raw_query=empty_q, english_keywords="", is_hindi=False)
        result = router.route(ctx)
        assert result.status == "routed"
        assert result.jurisdiction == "India"
        assert result.corpus_tag == "india"


def test_classifier_output_passthrough():
    """Verifies that route accepts classifier_output without error."""
    router = JurisdictionRouter()
    classifier_output = ClassifierOutput(
        category="Classical Ayurveda",
        confidence=0.95,
        reason="Ancient formulation from Charaka Samhita.",
    )
    ctx = QueryContext(
        raw_query="Is Triphala patentable in India?",
        english_keywords="",
        is_hindi=False,
    )
    result = router.route(
        ctx,
        classifier_output=classifier_output,
    )
    assert result.status == "routed"
    assert result.jurisdiction == "India"


def test_custom_default_jurisdiction():
    """Verifies that a custom default jurisdiction can be injected at initialization."""
    router = JurisdictionRouter(default_jurisdiction="Singapore")
    ctx = QueryContext(
        raw_query="How to file herbal patents?", english_keywords="", is_hindi=False
    )
    result = router.route(ctx)
    assert result.jurisdiction == "Singapore"
    assert result.status == "routed"


def test_config_default_jurisdiction_injection():
    """Verifies that config.DEFAULT_JURISDICTION is respected when not explicitly passed."""
    with patch("src.pipeline.jurisdiction_router.config.DEFAULT_JURISDICTION", "US"):
        router = JurisdictionRouter()
        ctx = QueryContext(
            raw_query="How to file herbal patents?", english_keywords="", is_hindi=False
        )
        result = router.route(ctx)
        assert result.jurisdiction == "US"
        assert result.status == "routed"
