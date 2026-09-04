"""Base interface and abstractions for LLM providers."""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMClient(ABC):
    """Abstract base class defining the standard interface for LLM providers."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> str:
        """Generates plain text response from the LLM.

        Args:
            prompt: Text prompt sent to the LLM.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in generated completion.
            timeout: Request timeout in seconds.

        Returns:
            The generated response string.
        """

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> T:
        """Generates a structured output validated against a Pydantic model schema.

        Args:
            prompt: Text prompt with instructions and context.
            response_schema: Target Pydantic model class for validation.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in generated completion.
            timeout: Request timeout in seconds.

        Returns:
            An instance of response_schema parsed from the LLM completion.
        """

    @abstractmethod
    def generate_chat(
        self,
        prompt: str,
        conversation_history: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        response_schema: type[T] | None = None,
    ) -> str | T:
        """Generates completion given multi-turn message history.

        Args:
            prompt: User prompt for current turn.
            conversation_history: List of previous turns with 'role' and 'content'/'parts'.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in generated completion.
            timeout: Request timeout in seconds.
            response_schema: Optional Pydantic schema if structured chat output is required.

        Returns:
            Generated text string or parsed Pydantic schema instance.
        """
