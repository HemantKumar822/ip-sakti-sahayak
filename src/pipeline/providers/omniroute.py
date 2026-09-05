"""OmniRoute implementation of BaseLLMClient via OpenAI-compatible endpoint."""

import json
import logging
from typing import TypeVar

from openai import APIConnectionError, OpenAI, OpenAIError
from pydantic import BaseModel

from src.config import config
from src.pipeline.providers.base import BaseLLMClient
from src.pipeline.providers.openrouter import _extract_json_text

logger = logging.getLogger("ip_sakti.pipeline.providers.omniroute")

T = TypeVar("T", bound=BaseModel)


class OmniRouteProvider(BaseLLMClient):
    """LLM client implementation backed by local OmniRoute gateway (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        timeout: float | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else config.OMNIROUTE_API_KEY
        self.model_name = (
            model_name if model_name is not None else config.OMNIROUTE_MODEL
        )
        self.base_url = base_url if base_url is not None else config.OMNIROUTE_BASE_URL
        self.temperature = (
            temperature if temperature is not None else config.GEMINI_TEMPERATURE
        )
        self.max_output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else config.GEMINI_MAX_OUTPUT_TOKENS
        )
        self.timeout = timeout if timeout is not None else config.GEMINI_REQUEST_TIMEOUT

        self.client = OpenAI(
            api_key=self.api_key or "omniroute-local",
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def _handle_connection_error(self, err: OpenAIError) -> None:
        """Helper to log and raise actionable error on connection refusal."""
        if isinstance(err, APIConnectionError):
            msg = (
                f"Cannot connect to the OpenAI-compatible gateway at '{self.base_url}'. "
                "Start a local gateway (e.g. Ollama with `ollama serve`, LM Studio, or vLLM) "
                "and point OMNIROUTE_BASE_URL at its /v1 endpoint, "
                "or switch LLM_PROVIDER=gemini in your .env file. "
                "Verify with: python run.py --provider-check"
            )
            logger.error(msg)
            raise ConnectionError(msg) from err
        raise err

    def generate_text(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> str:
        """Generates plain text completion via OmniRoute gateway."""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=(
                    temperature if temperature is not None else self.temperature
                ),
                max_tokens=(
                    max_tokens if max_tokens is not None else self.max_output_tokens
                ),
                timeout=timeout if timeout is not None else self.timeout,
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            return ""
        except OpenAIError as e:
            self._handle_connection_error(e)
            return ""

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> T:
        """Generates structured output conforming to response_schema via OmniRoute."""
        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        system_instruction = (
            "You are an expert AI assistant that responds ONLY with valid JSON conforming to the following JSON Schema:\n"
            f"{schema_json}\n\n"
            "Do not include any commentary, explanations, or markdown formatting outside the valid JSON object."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=(
                    temperature if temperature is not None else self.temperature
                ),
                max_tokens=(
                    max_tokens if max_tokens is not None else self.max_output_tokens
                ),
                response_format={"type": "json_object"},
                timeout=timeout if timeout is not None else self.timeout,
            )

            if not response.choices or not response.choices[0].message.content:
                raise RuntimeError(
                    "OmniRoute returned empty response for structured generation."
                )

            raw_text = response.choices[0].message.content
            cleaned_json = _extract_json_text(raw_text)
            return response_schema.model_validate_json(cleaned_json)
        except OpenAIError as e:
            self._handle_connection_error(e)
            raise

    def generate_chat(
        self,
        prompt: str,
        conversation_history: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        response_schema: type[T] | None = None,
    ) -> str | T:
        """Generates chat completion with history via OmniRoute."""
        messages: list[dict[str, str]] = []

        if response_schema is not None:
            schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "You are an expert AI assistant that responds ONLY with valid JSON conforming to the following JSON Schema:\n"
                        f"{schema_json}\n\n"
                        "Do not include any commentary outside the valid JSON object."
                    ),
                }
            )

        if conversation_history:
            for turn in conversation_history:
                raw_role = turn.get("role", "user")
                role = "assistant" if raw_role in ("model", "assistant") else "user"
                content = turn.get("content") or ""
                if not content and "parts" in turn:
                    parts = turn["parts"]
                    content = " ".join(parts) if isinstance(parts, list) else str(parts)
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": prompt})

        create_kwargs: dict[str, object] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": (
                max_tokens if max_tokens is not None else self.max_output_tokens
            ),
            "timeout": timeout if timeout is not None else self.timeout,
        }
        if response_schema is not None:
            create_kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**create_kwargs)

            if not response.choices or not response.choices[0].message.content:
                if response_schema is not None:
                    raise RuntimeError(
                        "OmniRoute returned empty chat structured response."
                    )
                return ""

            raw_text = response.choices[0].message.content.strip()
            if response_schema is not None:
                cleaned_json = _extract_json_text(raw_text)
                return response_schema.model_validate_json(cleaned_json)
            return raw_text
        except OpenAIError as e:
            self._handle_connection_error(e)
            raise
