"""Listing schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel

from app.models.listing import ListingStatus, ConfidentialityLevel


class ListingBase(BaseModel):
    """Base listing schema."""

    code: str
    title: str
    status: ListingStatus = ListingStatus.ACTIVE
    asking_price: Optional[Decimal] = None
    revenue: Optional[Decimal] = None
    sde: Optional[Decimal] = None
    location_region: Optional[str] = None
    confidentiality_level: ConfidentialityLevel = ConfidentialityLevel.MEDIUM
    short_description: Optional[str] = None
    notes: Optional[str] = None


class ListingCreate(ListingBase):
    """Listing creation schema."""

    pass


class ListingUpdate(BaseModel):
    """Listing update schema (all fields optional)."""

    code: Optional[str] = None
    title: Optional[str] = None
    status: Optional[ListingStatus] = None
    asking_price: Optional[Decimal] = None
    revenue: Optional[Decimal] = None
    sde: Optional[Decimal] = None
    location_region: Optional[str] = None
    confidentiality_level: Optional[ConfidentialityLevel] = None
    short_description: Optional[str] = None
    notes: Optional[str] = None


class ListingResponse(ListingBase):
    """Listing response schema."""

    id: UUID
    broker_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ListingListResponse(BaseModel):
    """Listing list response."""

    listings: List[ListingResponse]
    total: int
