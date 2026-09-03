"""Bilingual Normalizer and Terminology Bridge for IP-SAKTI Sahayak.

Detects Devanagari Hindi queries and expands them with canonical English
statutory and botanical terminology, enabling seamless hybrid retrieval against
the English statutory corpus (Patents Act, BDA 2002/2023, TKDL) while
preserving user language intent. Operates 100% offline with zero latency.
"""

import re
from dataclasses import dataclass

# Devanagari Unicode block: U+0900 to U+097F
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")

# Curated Ayurvedic botanical and Indian statutory terminology dictionary
AYURVEDA_STATUTORY_LEXICON: dict[str, str] = {
    # Classical formulations & medicinal plants
    "अश्वगंधा": "Ashwagandha Withania somnifera biological resource",
    "त्रिफला": "Triphala classical formulation Section 3(p)",
    "त्रिकटु": "Trikatu Churna classical formulation traditional recipe",
    "च्यवनप्राश": "Chyawanprash classical formulation generic trademark",
    "शीतोपलादि": "Sitopaladi Churna traditional powder formulation",
    "हल्दी": "Turmeric Curcuma longa CSIR prior art revocation",
    "नीम": "Neem Azadirachta indica traditional knowledge revocation",
    "सर्पगंधा": "Sarpagandha Rauvolfia serpentina biological diversity",
    "गिलोय": "Giloy Tinospora cordifolia Ayurvedic extract",
    "तुलसी": "Tulsi Ocimum sanctum biological resource",
    # IPR & statutory provisions
    "पेटेंट": "patent patentable Section 3(p) Section 3(d)",
    "पारंपरिक ज्ञान": "traditional knowledge TKDL prior art Section 3(p)",
    "जैव विविधता": "Biological Diversity Act NBA SBB Access and Benefit Sharing ABS",
    "लाभ साझाकरण": "Access and Benefit Sharing ABS National Biodiversity Authority",
    "पूर्व कला": "prior art novelty anticipation",
    "ट्रेडमार्क": "trademark Trade Marks Act 1999 branding genericness",
    "अधिकार": "intellectual property rights commercialization",
    "धारा": "Section statutory provision",
    "नियम": "rules guidelines AYUSH examination",
    "नवीनता": "novelty inventive step non-obviousness",
    "प्रभावकारिता": "therapeutic efficacy Section 3(d) Novartis precedent",
    "वाणिज्यिक": "commercial utilization commercial exploitation approval",
    "दवा": "Ayurvedic ASU medicine drug formulation",
    "अनुसंधान": "research commercial utilization Section 6 approval",
}


@dataclass
class BilingualQueryResult:
    """Result of bilingual query normalization."""

    is_hindi: bool
    original_query: str
    expanded_search_query: str
    matched_terms: list[str]


class BilingualNormalizer:
    """Bilingual query normalization and lexical expansion engine."""

    @staticmethod
    def is_hindi(text: str) -> bool:
        """Determines whether the query contains Devanagari Hindi characters."""
        return bool(DEVANAGARI_REGEX.search(text))

    @classmethod
    def expand_query(cls, query: str) -> BilingualQueryResult:
        """Analyzes the query and augments Hindi queries with English statutory tokens.

        Args:
            query: User's raw or PII-cleaned query string.

        Returns:
            BilingualQueryResult with expansion metadata.
        """
        clean_query = query.strip()
        if not cls.is_hindi(clean_query):
            return BilingualQueryResult(
                is_hindi=False,
                original_query=clean_query,
                expanded_search_query=clean_query,
                matched_terms=[],
            )

        matched_terms: list[str] = []
        english_statutory_tokens: list[str] = []

        for hindi_term, english_expansion in AYURVEDA_STATUTORY_LEXICON.items():
            if hindi_term in clean_query:
                matched_terms.append(hindi_term)
                english_statutory_tokens.append(english_expansion)

        # Extract any English words/numbers already in the query (e.g. brand names)
        english_words = re.findall(r"[A-Za-z0-9]+", clean_query)
        combined_tokens = english_words + english_statutory_tokens

        if combined_tokens:
            expanded_search_query = " ".join(combined_tokens).strip()
        else:
            # General fallback if no specific terms matched
            expanded_search_query = (
                "Indian Patent Law Patents Act 1970 Ayurveda Traditional Knowledge ABS"
            )

        return BilingualQueryResult(
            is_hindi=True,
            original_query=clean_query,
            expanded_search_query=expanded_search_query,
            matched_terms=matched_terms,
        )
