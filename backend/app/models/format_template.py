from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from app.core.database import Base


class FormatTemplate(Base):
    __tablename__ = "format_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(100), nullable=False)
    rules = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
