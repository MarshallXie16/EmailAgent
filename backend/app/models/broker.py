"""Broker models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Broker(Base):
    """Broker user account."""

    __tablename__ = "brokers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    timezone = Column(String(50), default="UTC")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    settings = relationship("BrokerSettings", back_populates="broker", uselist=False, cascade="all, delete-orphan")
    listings = relationship("Listing", back_populates="broker", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="broker", cascade="all, delete-orphan")
    email_threads = relationship("EmailThread", back_populates="broker", cascade="all, delete-orphan")


class BrokerSettings(Base):
    """Broker configuration settings."""

    __tablename__ = "broker_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    broker_id = Column(UUID(as_uuid=True), ForeignKey("brokers.id", ondelete="CASCADE"), nullable=False, index=True)
    auto_send_enabled = Column(Boolean, default=False, nullable=False)
    batch_windows = Column(JSON, default=list, nullable=False)  # [{start: "09:00", end: "09:30"}, ...]
    calendly_link = Column(Text, nullable=True)
    default_nda_url = Column(Text, nullable=True)
    llm_model = Column(String(100), nullable=True)

    # Relationships
    broker = relationship("Broker", back_populates="settings")
