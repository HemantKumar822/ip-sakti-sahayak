"""OpenRouter implementation of BaseLLMClient via OpenAI SDK."""

import json
import logging
import re
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel

from src.config import config
from src.pipeline.providers.base import BaseLLMClient

logger = logging.getLogger("ip_sakti.pipeline.providers.openrouter")

T = TypeVar("T", bound=BaseModel)


def _extract_json_text(text: str) -> str:
    """Extracts raw JSON payload from string, handling markdown code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        # Match ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return text


class OpenRouterProvider(BaseLLMClient):
    """LLM client implementation backed by OpenRouter (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        timeout: float | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else config.OPENROUTER_API_KEY
        self.model_name = (
            model_name if model_name is not None else config.OPENROUTER_MODEL
        )
        self.base_url = base_url if base_url is not None else config.OPENROUTER_BASE_URL
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
            api_key=self.api_key or "sk-dummy-key-for-init",
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def generate_text(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> str:
        """Generates plain text completion via OpenRouter."""
        messages = [{"role": "user", "content": prompt}]
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens if max_tokens is not None else self.max_output_tokens,
            timeout=timeout if timeout is not None else self.timeout,
        )
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        return ""

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> T:
        """Generates structured output parsed into response_schema."""
        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        system_instruction = (
            "You are an expert AI assistant that responds ONLY with valid JSON conforming to the following JSON Schema:\n"
            f"{schema_json}\n\n"
            "Do not include any commentary, explanations, or text outside the valid JSON object."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens if max_tokens is not None else self.max_output_tokens,
            response_format={"type": "json_object"},
            timeout=timeout if timeout is not None else self.timeout,
        )

        if not response.choices or not response.choices[0].message.content:
            raise RuntimeError(
                "OpenRouter returned empty response for structured generation."
            )

        raw_text = response.choices[0].message.content
        cleaned_json = _extract_json_text(raw_text)
        return response_schema.model_validate_json(cleaned_json)

    def generate_chat(
        self,
        prompt: str,
        conversation_history: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        response_schema: type[T] | None = None,
    ) -> str | T:
        """Generates chat completion with history via OpenRouter."""
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

        response = self.client.chat.completions.create(**create_kwargs)

        if not response.choices or not response.choices[0].message.content:
            if response_schema is not None:
                raise RuntimeError(
                    "OpenRouter returned empty chat structured response."
                )
            return ""

        raw_text = response.choices[0].message.content.strip()
        if response_schema is not None:
            cleaned_json = _extract_json_text(raw_text)
            return response_schema.model_validate_json(cleaned_json)
        return raw_text
