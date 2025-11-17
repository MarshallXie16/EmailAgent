"""Review queue schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentReasoningDetail(BaseModel):
    """Agent reasoning details for review."""

    why_flagged: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    concerns: List[str] = []
    tools_called: List[str] = []
    confidence_factors: Optional[Dict[str, Any]] = None


class ReviewQueueMessagePreview(BaseModel):
    """Preview of a message in the thread."""

    id: int
    direction: str  # "inbound" or "outbound"
    from_email: str
    to_email: str
    body_text: str
    sent_at: datetime
    sent_by: str


class ReviewQueueLeadInfo(BaseModel):
    """Lead information for review queue."""

    id: UUID
    name: str
    email: str
    type: str


class ReviewQueueListingInfo(BaseModel):
    """Listing information for review queue."""

    id: UUID
    code: str
    title: str
    asking_price: Optional[int]


class ReviewQueueItem(BaseModel):
    """Single item in review queue."""

    id: UUID  # thread_id
    lead: ReviewQueueLeadInfo
    listing: Optional[ReviewQueueListingInfo]
    status: str
    last_inbound_message: ReviewQueueMessagePreview
    proposed_response: str
    agent_reasoning: AgentReasoningDetail
    created_at: datetime
    priority_score: float
    message_count: int


class ReviewQueueResponse(BaseModel):
    """Review queue listing."""

    threads: List[ReviewQueueItem]
    total: int


class ApproveEmailRequest(BaseModel):
    """Request to approve and optionally edit an email."""

    edits: Optional[str] = Field(None, description="Optional edited response text")


class ManualReplyRequest(BaseModel):
    """Request to send manual reply."""

    body_text: str = Field(..., min_length=1, description="Manual response text")
