from pydantic import BaseModel
from typing import List, Optional

class Citation(BaseModel):
    document_id: str
    snippet: str
    relevance_score: float

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    requires_abs_compliance: bool = False
    confidence_score: Optional[float] = None
