from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.core.database import Base


class UserReference(Base):
    __tablename__ = "user_references"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False)
    authors = Column(String(500), nullable=True)
    source = Column(String(500), nullable=True)
    abstract = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    keywords = Column(String(300), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class PaperReference(Base):
    __tablename__ = "paper_references"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    reference_id = Column(Integer, ForeignKey("user_references.id", ondelete="CASCADE"), nullable=False)
