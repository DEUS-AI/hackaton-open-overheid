from pydantic import BaseModel, Field, HttpUrl


class QueryRequest(BaseModel):
    query: str


class Document(BaseModel):
    name: str
    id: str
    reasons: list[str]
    tags: list[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    link: HttpUrl


class SummaryResponse(BaseModel):
    summary: str
    documents: list[Document]
