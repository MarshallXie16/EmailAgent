"""Email thread schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.email import ThreadStatus, AgentAction, MessageDirection, MessageSentBy


class MessageResponse(BaseModel):
    """Email message response."""

    id: int
    direction: MessageDirection
    from_email: str
    to_email: str
    subject: Optional[str]
    body_text: str
    sent_at: datetime
    sent_by: MessageSentBy

    class Config:
        from_attributes = True


class ThreadResponse(BaseModel):
    """Email thread response."""

    id: UUID
    broker_id: UUID
    lead_id: UUID
    listing_id: Optional[UUID]
    external_thread_id: str
    status: ThreadStatus
    last_agent_action: AgentAction
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ThreadListResponse(BaseModel):
    """Email thread list response."""

    threads: List[ThreadResponse]
    total: int


class OverrideReplyRequest(BaseModel):
    """Override agent reply request."""

    body_text: str
