"""Lead schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.lead import LeadType


class LeadBase(BaseModel):
    """Base lead schema."""

    email: EmailStr
    name: Optional[str] = None
    type: LeadType = LeadType.OTHER
    lead_score: Optional[int] = None


class LeadCreate(LeadBase):
    """Lead creation schema."""

    pass


class LeadResponse(LeadBase):
    """Lead response schema."""

    id: UUID
    broker_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
