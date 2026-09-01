from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    """A single turn in the conversation history."""

    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: str = Field(..., description="The text of the message")


class QueryRequest(BaseModel):
    query_text: str = Field(
        ..., description="The intellectual property question from the user"
    )
    session_id: str = Field(
        ..., description="A unique identifier for the user's session"
    )
    conversation_history: list[ConversationTurn] = Field(
        default_factory=list,
        description="Prior turns in the conversation, oldest first. Max 6 turns.",
    )
