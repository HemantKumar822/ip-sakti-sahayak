"""Session response models for IP-SAKTI Sahayak conversation persistence."""

from typing import Any

from pydantic import BaseModel, Field


class SessionTurnResponse(BaseModel):
    """Represents a single persisted conversation turn."""

    id: int = Field(..., description="Unique auto-incrementing turn identifier")
    role: str = Field(..., description="Message author role: 'user' or 'assistant'")
    content: str = Field(..., description="Content text of the turn")
    citations: list[dict[str, Any]] | None = Field(
        default=None,
        description="Structured citations associated with assistant response",
    )
    response_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Full response metadata (flags, latency, confidence, etc.)",
    )
    created_at: str | None = Field(
        default=None,
        description="ISO 8601 timestamp when turn was recorded",
    )


class SessionDetailResponse(BaseModel):
    """Detailed response containing complete session history and metadata."""

    session_id: str = Field(..., description="Unique anonymous session identifier")
    turns: list[SessionTurnResponse] = Field(
        default_factory=list,
        description="Chronological list of conversation turns for the session",
    )
    total_turns: int = Field(
        ...,
        description="Total number of conversation turns recorded in the session",
    )
    created_at: str | None = Field(
        default=None,
        description="Timestamp when session was created",
    )
    updated_at: str | None = Field(
        default=None,
        description="Timestamp of most recent activity in session",
    )


class SessionSummaryResponse(BaseModel):
    """Summary of a stored session for history navigation."""

    session_id: str = Field(..., description="Unique anonymous session identifier")
    preview: str | None = Field(
        default=None,
        description="Text preview snippet of the first user inquiry",
    )
    total_turns: int = Field(
        ...,
        description="Total number of conversation turns recorded in the session",
    )
    created_at: str | None = Field(
        default=None,
        description="Timestamp when session was created",
    )
    updated_at: str | None = Field(
        default=None,
        description="Timestamp of most recent activity in session",
    )
