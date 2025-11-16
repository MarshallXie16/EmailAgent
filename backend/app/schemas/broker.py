"""Broker schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class BrokerBase(BaseModel):
    """Base broker schema."""

    name: str
    email: EmailStr
    timezone: str = "UTC"


class BrokerCreate(BrokerBase):
    """Broker creation schema."""

    password: str


class BrokerResponse(BrokerBase):
    """Broker response schema."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
