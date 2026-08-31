import logging

import google.generativeai as genai
from pydantic import BaseModel

from src.config import config

logger = logging.getLogger(__name__)

CLASSIFIER_PROMPT = """You are an expert Intellectual Property and Ayurveda classifier for the IP-SAKTI Sahayak system.
Your task is to analyze the user's question and determine which Ayurveda product category it belongs to.

Categories:
1. "Classical Ayurveda": Formulations described in ancient texts (e.g. Charaka Samhita) and based on traditional recipes.
2. "Proprietary Ayurveda": Modern Ayurveda products with unique formulas not in classical texts (e.g., Dabur Chyawanprash).
3. "Unclassifiable": The query is not related to Ayurveda products, or lacks enough context to decide.

Analyze the question carefully and return a JSON object containing:
- "category": Must be exactly one of "Classical Ayurveda", "Proprietary Ayurveda", or "Unclassifiable".
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
        model_name = getattr(config, "GEMINI_MODEL", "gemini-1.5-flash")
        self.model = genai.GenerativeModel(model_name)

    def classify(self, query: str) -> ClassifierOutput:
        """
        Classifies a user query into an Ayurveda product category.

        Args:
            query (str): The user's question.

        Returns:
            ClassifierOutput: A structured response with category, confidence, and reason.
        """
        try:
            response = self.model.generate_content(
                f"{CLASSIFIER_PROMPT}\n\nUser Question: {query}",
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=ClassifierOutput,
                    temperature=0.1,
                ),
            )
            return ClassifierOutput.model_validate_json(response.text)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Classifier API or parsing failed: {e}")
            return ClassifierOutput(
                category="Unclassifiable",
                confidence=0.0,
                reason="System encountered an error during classification.",
            )
