"""Agent run tracking models."""

from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, Numeric, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class FinalAction(str, enum.Enum):
    """Final action taken by agent."""

    ANSWER = "answer"
    ASK_NDA = "ask_nda"
    BOOK_MEETING = "book_meeting"
    ESCALATE = "escalate"


class AgentRun(Base):
    """Record of an agent execution on an email thread."""

    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_thread_id = Column(UUID(as_uuid=True), ForeignKey("email_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    llm_model = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    tools_called = Column(JSON, nullable=True)  # Array of tool names and args
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    final_action = Column(SQLEnum(FinalAction), nullable=False)
    error_flag = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    thread = relationship("EmailThread", back_populates="agent_runs")
