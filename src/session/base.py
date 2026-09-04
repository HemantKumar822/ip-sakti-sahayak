"""Abstract interface for IP-SAKTI Sahayak session persistence."""

from abc import ABC, abstractmethod
from typing import Any


class AbstractSessionStore(ABC):
    """Abstract interface defining operations for conversation session storage."""

    @abstractmethod
    def save_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: list[dict[str, Any]] | None = None,
        response_metadata: dict[str, Any] | None = None,
    ) -> int:
        """Persists a new turn for the given session.

        Args:
            session_id: The session identifier.
            role: The author role ('user' or 'assistant').
            content: The text message content.
            citations: Optional list of structured citations.
            response_metadata: Optional dict of telemetry / verification metadata.

        Returns:
            The unique integer ID of the persisted turn.
        """

    @abstractmethod
    def get_session_turns(
        self, session_id: str, limit: int = 6
    ) -> list[dict[str, Any]]:
        """Retrieves turns for a session in chronological order up to limit.

        Args:
            session_id: The session identifier.
            limit: Maximum number of recent turns to retrieve.

        Returns:
            List of turn dictionaries.
        """

    @abstractmethod
    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieves session metadata including timestamps and total turn count.

        Args:
            session_id: The session identifier.

        Returns:
            Session dictionary if found, or None.
        """

    @abstractmethod
    def count_turns(self, session_id: str, role: str | None = None) -> int:
        """Counts the number of turns recorded for a given session.

        Args:
            session_id: The session identifier.
            role: Optional filter by role (e.g. 'user').

        Returns:
            Integer count of turns.
        """

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Deletes a session and all its associated turns.

        Args:
            session_id: The session identifier.

        Returns:
            True if the session was found and deleted, False otherwise.
        """

    @abstractmethod
    def close(self) -> None:
        """Closes any underlying database connections or pools."""
