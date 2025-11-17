"""Analytics response schemas."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnalyticsOverviewResponse(BaseModel):
    """Analytics overview KPIs."""

    period: str = Field(..., description="Time period (7d, 30d, 90d, all)")
    total_emails: int = Field(..., description="Total emails processed in period")
    auto_reply_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage auto-replied (0-1)")
    escalation_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage escalated (0-1)")
    avg_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence score (0-1)")
    nda_request_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage NDA requested (0-1)")


class EmailActivityItem(BaseModel):
    """Single email activity record."""

    id: int
    thread_id: UUID
    lead_name: str
    lead_email: str
    listing_code: Optional[str] = None
    listing_title: Optional[str] = None
    subject: str
    sent_at: datetime
    status: str  # "sent" or "draft"
    sent_by: str  # "agent", "broker", or "lead"
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    final_action: Optional[str] = None
    tools_called: Optional[List[str]] = None

    class Config:
        from_attributes = True


class EmailActivityResponse(BaseModel):
    """Paginated email activity log."""

    emails: List[EmailActivityItem]
    total: int
    skip: int
    limit: int


class DailyCount(BaseModel):
    """Daily email count."""

    date: str  # ISO date format
    count: int


class ListingCount(BaseModel):
    """Email count by listing."""

    listing_code: str
    listing_title: str
    count: int


class ActionBreakdown(BaseModel):
    """Email count by final action."""

    answered: int = 0
    escalated: int = 0
    nda_requested: int = 0
    meeting_booked: int = 0


class AnalyticsTrendsResponse(BaseModel):
    """Analytics trends and breakdowns."""

    daily_counts: List[DailyCount]
    by_listing: List[ListingCount]
    by_action: ActionBreakdown
