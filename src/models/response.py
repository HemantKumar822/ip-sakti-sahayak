from pydantic import BaseModel

class Citation(BaseModel):
    document_id: str
    snippet: str
    relevance_score: float

class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    requires_abs_compliance: bool = False
    confidence_score: float | None = None
