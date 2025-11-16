"""Email thread and message models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ThreadStatus(str, enum.Enum):
    """Email thread status."""

    OPEN = "open"
    CLOSED = "closed"
    NEEDS_BROKER = "needs_broker"


class AgentAction(str, enum.Enum):
    """Last agent action on thread."""

    NONE = "none"
    AUTO_REPLY_SENT = "auto_reply_sent"
    DRAFT_CREATED = "draft_created"
    ESCALATED = "escalated"


class MessageDirection(str, enum.Enum):
    """Email message direction."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageSentBy(str, enum.Enum):
    """Who sent the message."""

    LEAD = "lead"
    BROKER = "broker"
    AGENT = "agent"


class EmailThread(Base):
    """Email conversation thread."""

    __tablename__ = "email_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broker_id = Column(UUID(as_uuid=True), ForeignKey("brokers.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="SET NULL"), nullable=True, index=True)
    external_thread_id = Column(String(255), nullable=False)  # Gmail thread ID
    status = Column(SQLEnum(ThreadStatus), default=ThreadStatus.OPEN, nullable=False, index=True)
    last_agent_action = Column(SQLEnum(AgentAction), default=AgentAction.NONE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    broker = relationship("Broker", back_populates="email_threads")
    lead = relationship("Lead", back_populates="email_threads")
    listing = relationship("Listing", back_populates="email_threads")
    messages = relationship("EmailMessage", back_populates="thread", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="thread", cascade="all, delete-orphan")


class EmailMessage(Base):
    """Individual email message in a thread."""

    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_thread_id = Column(UUID(as_uuid=True), ForeignKey("email_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(SQLEnum(MessageDirection), nullable=False)
    from_email = Column(String(255), nullable=False)
    to_email = Column(String(255), nullable=False)
    subject = Column(Text, nullable=True)
    body_text = Column(Text, nullable=False)
    sent_at = Column(DateTime, nullable=False, index=True)
    raw_metadata = Column(JSON, nullable=True)  # Store full Gmail message metadata
    sent_by = Column(SQLEnum(MessageSentBy), nullable=False)

    # Relationships
    thread = relationship("EmailThread", back_populates="messages")
