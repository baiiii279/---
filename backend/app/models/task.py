from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    agent_type = Column(Enum("parse", "outline", "write", "polish", "cite_check"), nullable=False)
    status = Column(Enum("pending", "running", "success", "failed"), default="pending")
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    user_feedback = Column(Enum("pending", "approve", "reject", "edit"), default="pending")
    feedback_comment = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
