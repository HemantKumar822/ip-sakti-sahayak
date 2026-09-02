import logging

import google.generativeai as genai
from pydantic import BaseModel

from src.config import config
from src.utils.resilience import retry_with_backoff

logger = logging.getLogger(__name__)

CLASSIFIER_PROMPT = """You are an expert Intellectual Property and Ayurveda classifier for the IP-SAKTI Sahayak system.
Your task is to analyze the user's question and determine which Ayurveda product category it belongs to.

Categories:
1. "Classical Ayurveda": Formulations described in ancient texts (e.g. Charaka Samhita) and based on traditional recipes.
2. "Proprietary Ayurveda": Modern Ayurveda products with unique formulas not in classical texts (e.g., Dabur Chyawanprash).
3. "Conversational": A general greeting, pleasantry, or follow-up that does not ask a specific legal or factual question (e.g., "hi", "thank you", "okay").
4. "Unclassifiable": The query is not related to Ayurveda products, or lacks enough context to decide.

Analyze the question carefully and return a JSON object containing:
- "category": Must be exactly one of "Classical Ayurveda", "Proprietary Ayurveda", "Conversational", or "Unclassifiable".
- "confidence": A float between 0.0 and 1.0 indicating your confidence.
- "reason": A one-sentence explanation for your classification.
"""


class ClassifierOutput(BaseModel):
    category: str
    confidence: float
    reason: str


class Classifier:
    def __init__(self):
        """Initializes the Classifier and configures the Gemini API."""
        genai.configure(api_key=config.GEMINI_API_KEY)
        model_name = config.GEMINI_MODEL
        self.model = genai.GenerativeModel(model_name)

    @retry_with_backoff(max_retries=2, initial_delay=1.0)
    def _generate_with_retry(self, prompt: str) -> str:
        """Invokes Gemini API with exponential backoff retry on rate limits."""
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ClassifierOutput,
                temperature=config.GEMINI_TEMPERATURE,
            ),
        )
        return response.text

    @staticmethod
    def fallback_classify(query: str) -> ClassifierOutput:
        """Deterministic rule-based classification fallback when LLM API is exhausted or unavailable."""
        q = query.strip().lower()
        if not q or q in {
            "hi",
            "hello",
            "hey",
            "thanks",
            "thank you",
            "okay",
            "ok",
            "good morning",
        }:
            return ClassifierOutput(
                category="Conversational",
                confidence=0.90,
                reason="Identified conversational greeting or pleasantry via fallback heuristic.",
            )

        # Classical Ayurveda indicators
        classical_terms = [
            "charaka",
            "samhita",
            "sushruta",
            "ashtanga",
            "triphala",
            "chyawanprash",
            "trikatu",
            "sitopaladi",
            "churna",
            "bhasma",
            "taila",
            "ghrita",
            "ancient",
            "traditional formulation",
            "classical formulation",
            "neem and turmeric",
            "section 3(p)",
            "section 3p",
            "tkdl",
            "traditional knowledge",
        ]
        if any(term in q for term in classical_terms):
            return ClassifierOutput(
                category="Classical Ayurveda",
                confidence=0.85,
                reason="Identified classical formulation or traditional knowledge reference via heuristic.",
            )

        # Proprietary Ayurveda indicators
        proprietary_terms = [
            "patent",
            "proprietary",
            "extract",
            "extraction",
            "formulation",
            "bioavailability",
            "synergistic",
            "curcumin",
            "ashwagandha",
            "branding",
            "trademark",
            "packaging",
            "syrup",
            "cosmetic",
            "derivative",
            "synthetic",
            "commercial",
            "dabur",
            "himalaya",
        ]
        if any(term in q for term in proprietary_terms):
            return ClassifierOutput(
                category="Proprietary Ayurveda",
                confidence=0.80,
                reason="Identified proprietary formulation, extraction, or commercial IP inquiry via heuristic.",
            )

        # Default to Unclassifiable
        return ClassifierOutput(
            category="Unclassifiable",
            confidence=0.0,
            reason="System encountered an error during classification (fallback heuristic applied).",
        )

    def classify(self, query: str) -> ClassifierOutput:
        """Classifies a user query into an Ayurveda product category with resilience fallback.

        Args:
            query (str): The user's question.

        Returns:
            ClassifierOutput: A structured response with category, confidence, and reason.
        """
        try:
            raw_text = self._generate_with_retry(
                f"{CLASSIFIER_PROMPT}\n\nUser Question: {query}"
            )
            return ClassifierOutput.model_validate_json(raw_text)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Classifier LLM API failed (%s); switching to deterministic fallback heuristic.",
                e,
            )
            return self.fallback_classify(query)
