"""Lead and NDA models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class LeadType(str, enum.Enum):
    """Lead type enum."""

    BUYER = "buyer"
    SELLER = "seller"
    OTHER = "other"


class NDAStatus(str, enum.Enum):
    """NDA status enum."""

    SENT = "sent"
    SIGNED = "signed"
    REJECTED = "rejected"
    REVOKED = "revoked"


class Lead(Base):
    """Lead/prospect contact information."""

    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broker_id = Column(UUID(as_uuid=True), ForeignKey("brokers.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    type = Column(SQLEnum(LeadType), default=LeadType.OTHER, nullable=False)
    lead_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    broker = relationship("Broker", back_populates="leads")
    ndas = relationship("NDA", back_populates="lead", cascade="all, delete-orphan")
    email_threads = relationship("EmailThread", back_populates="lead", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("broker_id", "email", name="uq_broker_lead_email"),
    )


class NDA(Base):
    """NDA (Non-Disclosure Agreement) tracking."""

    __tablename__ = "ndas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SQLEnum(NDAStatus), default=NDAStatus.SENT, nullable=False)
    nda_url = Column(String(1000), nullable=True)
    signed_at = Column(DateTime, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="ndas")
    listing = relationship("Listing", back_populates="ndas")

    __table_args__ = (
        UniqueConstraint("lead_id", "listing_id", name="uq_lead_listing_nda"),
    )
