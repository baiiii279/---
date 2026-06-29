from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, Enum, ForeignKey, func
from app.core.database import Base


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    step = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(Enum("info", "warn", "error"), default="info")
    created_at = Column(DateTime, server_default=func.now())
