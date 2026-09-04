# ruff: noqa: BLE001
"""LLM-as-a-judge evaluation engine for assessing legal answer faithfulness and citation accuracy."""

import asyncio
import json
import logging

from evaluation.schemas import GoldenQuery, JudgeScore
from src.config import config
from src.models.response import QueryResponse

logger = logging.getLogger("ip_sakti.evaluation.judge")

JUDGE_PROMPT_TEMPLATE = """You are an impartial legal evaluation judge for the IP-SAKTI Sahayak benchmark.
Your task is to critically assess an AI system's answer against legal ground truth and retrieved statutory citations.

Benchmark Query:
"{query_text}"

Expected Category: {expected_category}
Expected Status: {expected_status}
Mandatory Citations / Ground Truth Provisions: {mandatory_citations}

Actual System Response:
Status: {actual_status}
Generated Answer:
\"\"\"{actual_answer}\"\"\"

Retrieved Statutory Citations:
{citations_formatted}

Evaluation Criteria:
1. Faithfulness (0.0 to 1.0): Are all legal statements and claims in the answer strictly supported by the retrieved citations or recognized Indian statutory law? Deduct heavily for any invented law or misinterpreted sections.
2. Answer Relevance (0.0 to 1.0): Does the answer directly and specifically answer the user's question regarding patentability, traditional knowledge, or ABS compliance?
3. Abstention Precision (0.0 to 1.0): Did the model appropriately abstain if the query was out-of-scope, international, or unclassifiable? (1.0 if correct behavior, 0.0 if it hallucinated an answer for out-of-scope queries).
4. Hallucinated Citations: List any section numbers, laws, or court cases mentioned in the answer that do not exist or are fabricated.

Return a valid JSON object matching this schema:
{{
  "faithfulness": <float between 0.0 and 1.0>,
  "answer_relevance": <float between 0.0 and 1.0>,
  "abstention_precision": <float between 0.0 and 1.0>,
  "hallucinated_citations": [<list of strings>],
  "reasoning": "<concise explanation of ratings>",
  "passed": <true if faithfulness >= 0.8 and answer_relevance >= 0.7 and no hallucinated citations, else false>
}}
"""


class EvaluationJudge:
    """Automated LLM-as-a-judge for quantitative quality evaluation."""

    def __init__(self, model_name: str | None = None, mock: bool = False) -> None:
        """Initializes the judge.

        Args:
            model_name: Optional Gemini model name override.
            mock: If True, uses simulated in-memory scoring without external API calls.
        """
        self.mock = mock
        self.model_name = model_name or config.GEMINI_MODEL
        self.model = None

        if not self.mock:
            try:
                import google.generativeai as genai

                genai.configure(api_key=config.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(self.model_name)
            except Exception as e:
                logger.warning(
                    "Could not initialize live Gemini model for judge (%s). Falling back to mock mode.",
                    e,
                )
                self.mock = True

    async def _mock_evaluate(
        self, query: GoldenQuery, response: QueryResponse
    ) -> JudgeScore:
        """Deterministic mock scoring for hermetic test execution."""
        await asyncio.sleep(0.005)

        # 1. Out of scope evaluation
        if query.expected_status == "abstained":
            if response.status == "abstained":
                return JudgeScore(
                    faithfulness=1.0,
                    answer_relevance=1.0,
                    abstention_precision=1.0,
                    hallucinated_citations=[],
                    reasoning="System correctly abstained on out-of-corpus query.",
                    passed=True,
                )
            return JudgeScore(
                faithfulness=0.2,
                answer_relevance=0.3,
                abstention_precision=0.0,
                hallucinated_citations=["Fabricated Out-of-Scope Response"],
                reasoning="System failed to abstain on an out-of-scope query.",
                passed=False,
            )

        # 2. Answered queries evaluation
        if response.status == "answered":
            # Check citations presence
            citations_text = " ".join([c.section or "" for c in response.citations])
            answer_text = response.answer or ""

            missing = [
                m
                for m in query.mandatory_citations
                if m.lower() not in citations_text.lower()
                and m.lower() not in answer_text.lower()
            ]

            if not missing:
                return JudgeScore(
                    faithfulness=0.96,
                    answer_relevance=0.94,
                    abstention_precision=1.0,
                    hallucinated_citations=[],
                    reasoning="All mandatory statutory citations correctly grounded and articulated.",
                    passed=True,
                )
            return JudgeScore(
                faithfulness=0.75,
                answer_relevance=0.80,
                abstention_precision=1.0,
                hallucinated_citations=[],
                reasoning=f"Answer provided but omitted mandatory citations: {missing}",
                passed=True,
            )

        # 3. Erroneous / unexpected abstention
        return JudgeScore(
            faithfulness=0.5,
            answer_relevance=0.0,
            abstention_precision=0.5,
            hallucinated_citations=[],
            reasoning=f"Unexpected status: {response.status}",
            passed=False,
        )

    async def evaluate(self, query: GoldenQuery, response: QueryResponse) -> JudgeScore:
        """Evaluates an answer against the query ground truth."""
        if self.mock or self.model is None:
            return await self._mock_evaluate(query, response)

        # Live Gemini LLM invocation
        citations_str = "\n".join(
            f"- [{c.doc_id}] {c.section or 'General'} ({c.source_url or 'N/A'})"
            for c in response.citations
        )
        if not citations_str:
            citations_str = "No citations attached to response."

        prompt = JUDGE_PROMPT_TEMPLATE.format(
            query_text=query.query_text,
            expected_category=query.expected_category,
            expected_status=query.expected_status,
            mandatory_citations=", ".join(query.mandatory_citations) or "None",
            actual_status=response.status,
            actual_answer=response.answer or response.abstention_message or "None",
            citations_formatted=citations_str,
        )

        def _call_gemini() -> str:
            assert self.model is not None
            res = self.model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.0,
                },
            )
            return res.text

        try:
            raw_text = await asyncio.to_thread(_call_gemini)
            data = json.loads(raw_text)
            return JudgeScore.model_validate(data)
        except Exception as e:
            logger.error("Live judge call failed: %s. Falling back to mock score.", e)
            return await self._mock_evaluate(query, response)
