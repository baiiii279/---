from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class FeedbackRequest(BaseModel):
    task_id: int
    action: Literal["approve", "reject", "edit"]
    comment: str | None = None
    edited_content: str | None = None

class TaskResponse(BaseModel):
    id: int
    paper_id: int
    agent_type: str
    status: str
    output_data: str | None
    user_feedback: str
    feedback_comment: str | None
    started_at: datetime | None
    finished_at: datetime | None

    class Config:
        from_attributes = True
