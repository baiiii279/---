from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class CreatePaperRequest(BaseModel):
    topic: str
    template: Literal["course", "journal"] = "course"
    reference_ids: list[int] = []

class PaperResponse(BaseModel):
    id: int
    user_id: int
    title: str | None
    topic: str
    template: str
    status: str
    outline: str | None
    content: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UpdatePaperRequest(BaseModel):
    title: str | None = None
    outline: str | None = None
    content: str | None = None
