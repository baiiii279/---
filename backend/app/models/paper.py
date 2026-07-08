from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func
from app.core.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)
    topic = Column(String(500), nullable=False)
    template = Column(Enum("course", "journal"), nullable=False, default="course")
    status = Column(Enum("draft", "parsing", "outlining", "writing", "polishing", "checking", "formatting", "complete"),
                    nullable=False, default="draft")
    outline = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    target_words = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
