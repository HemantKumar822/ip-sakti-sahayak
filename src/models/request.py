from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query_text: str = Field(..., description="The intellectual property question from the user")
    session_id: str = Field(..., description="A unique identifier for the user's session")
