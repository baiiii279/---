from pydantic import BaseModel
from datetime import datetime

class ReferenceRequest(BaseModel):
    title: str
    authors: str | None = None
    source: str | None = None
    abstract: str | None = None
    url: str | None = None
    keywords: str | None = None

class ReferenceResponse(BaseModel):
    id: int
    user_id: int
    title: str
    authors: str | None
    source: str | None
    abstract: str | None
    full_text: str | None = None
    url: str | None
    keywords: str | None
    created_at: datetime

    class Config:
        from_attributes = True
