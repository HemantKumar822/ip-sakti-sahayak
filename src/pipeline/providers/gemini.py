"""Google Gemini implementation of BaseLLMClient."""

import logging
from typing import TypeVar

import google.generativeai as genai
from pydantic import BaseModel

from src.config import config
from src.pipeline.providers.base import BaseLLMClient

logger = logging.getLogger("ip_sakti.pipeline.providers.gemini")

T = TypeVar("T", bound=BaseModel)


class GeminiProvider(BaseLLMClient):
    """LLM client implementation backed by Google Gemini SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        timeout: float | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else config.GEMINI_API_KEY
        self.model_name = model_name if model_name is not None else config.GEMINI_MODEL
        self.temperature = (
            temperature if temperature is not None else config.GEMINI_TEMPERATURE
        )
        self.max_output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else config.GEMINI_MAX_OUTPUT_TOKENS
        )
        if (
            self.model_name
            and "2.5" in self.model_name
            and self.max_output_tokens <= 2048
        ):
            self.max_output_tokens = 8192

        self.timeout = timeout if timeout is not None else config.GEMINI_REQUEST_TIMEOUT

        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def generate_text(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> str:
        """Generates plain text response using Gemini."""
        gen_config = genai.GenerationConfig(
            temperature=temperature if temperature is not None else self.temperature,
            max_output_tokens=(
                max_tokens if max_tokens is not None else self.max_output_tokens
            ),
        )
        req_timeout = timeout if timeout is not None else self.timeout
        response = self.model.generate_content(
            prompt,
            generation_config=gen_config,
            request_options={"timeout": req_timeout},
        )
        if response and getattr(response, "text", None):
            return response.text.strip()
        return ""

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> T:
        """Generates structured output constrained to response_schema."""
        gen_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=temperature if temperature is not None else self.temperature,
            max_output_tokens=(
                max_tokens if max_tokens is not None else self.max_output_tokens
            ),
        )
        req_timeout = timeout if timeout is not None else self.timeout
        response = self.model.generate_content(
            prompt,
            generation_config=gen_config,
            request_options={"timeout": req_timeout},
        )
        if not response or not getattr(response, "text", None):
            raise RuntimeError("Gemini returned empty structured response.")
        return response_schema.model_validate_json(response.text)

    def generate_chat(
        self,
        prompt: str,
        conversation_history: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        response_schema: type[T] | None = None,
    ) -> str | T:
        """Generates chat completion with conversation history."""
        gen_config_kwargs: dict[str, object] = {
            "temperature": temperature if temperature is not None else self.temperature,
            "max_output_tokens": (
                max_tokens if max_tokens is not None else self.max_output_tokens
            ),
        }
        if response_schema is not None:
            gen_config_kwargs["response_mime_type"] = "application/json"
            gen_config_kwargs["response_schema"] = response_schema

        gen_config = genai.GenerationConfig(**gen_config_kwargs)
        req_timeout = timeout if timeout is not None else self.timeout

        if conversation_history:
            chat_history = []
            for turn in conversation_history:
                role = "user" if turn.get("role") == "user" else "model"
                parts = turn.get("parts") or [turn.get("content", "")]
                chat_history.append({"role": role, "parts": parts})
            chat = self.model.start_chat(history=chat_history)
            response = chat.send_message(
                prompt,
                generation_config=gen_config,
                request_options={"timeout": req_timeout},
            )
        else:
            response = self.model.generate_content(
                prompt,
                generation_config=gen_config,
                request_options={"timeout": req_timeout},
            )

        if not response or not getattr(response, "text", None):
            if response_schema is not None:
                raise RuntimeError("Gemini returned empty structured chat response.")
            return ""

        if response_schema is not None:
            return response_schema.model_validate_json(response.text)
        return response.text.strip()
