from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    """A single turn in the conversation history."""

    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: str = Field(..., description="The text of the message")


class QueryRequest(BaseModel):
    query_text: str = Field(
        ...,
        max_length=4000,
        description="The intellectual property question from the user (max 4000 chars)",
    )
    session_id: str = Field(
        ..., description="A unique identifier for the user's session"
    )
    conversation_history: list[ConversationTurn] = Field(
        default_factory=list,
        max_length=6,
        description="Prior turns in the conversation, oldest first. Max 6 turns.",
    )
