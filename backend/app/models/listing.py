"""Listing models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, Numeric, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import enum

from app.core.database import Base


class ListingStatus(str, enum.Enum):
    """Listing status enum."""

    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    ARCHIVED = "archived"


class ConfidentialityLevel(str, enum.Enum):
    """Confidentiality level enum."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DocumentType(str, enum.Enum):
    """Document type enum."""

    TEASER = "teaser"
    CIM_EXCERPT = "cim_excerpt"
    FAQ = "faq"
    INTERNAL_NOTES = "internal_notes"


class Listing(Base):
    """Business listing."""

    __tablename__ = "listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broker_id = Column(UUID(as_uuid=True), ForeignKey("brokers.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)  # Unique per broker
    title = Column(String(500), nullable=False)
    status = Column(SQLEnum(ListingStatus), default=ListingStatus.ACTIVE, nullable=False, index=True)
    asking_price = Column(Numeric(15, 2), nullable=True)
    revenue = Column(Numeric(15, 2), nullable=True)
    sde = Column(Numeric(15, 2), nullable=True)  # Seller's Discretionary Earnings
    location_region = Column(Text, nullable=True)
    confidentiality_level = Column(SQLEnum(ConfidentialityLevel), default=ConfidentialityLevel.MEDIUM, nullable=False)
    short_description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)  # Internal broker notes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    broker = relationship("Broker", back_populates="listings")
    documents = relationship("ListingDocument", back_populates="listing", cascade="all, delete-orphan")
    ndas = relationship("NDA", back_populates="listing", cascade="all, delete-orphan")
    email_threads = relationship("EmailThread", back_populates="listing")

    __table_args__ = (
        # Composite index for common queries
        {"schema": None},
    )


class ListingDocument(Base):
    """Document attached to a listing."""

    __tablename__ = "listing_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    file_url = Column(Text, nullable=False)  # S3 path
    type = Column(SQLEnum(DocumentType), nullable=False)
    title = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    listing = relationship("Listing", back_populates="documents")
    chunks = relationship("ListingDocumentChunk", back_populates="document", cascade="all, delete-orphan")


class ListingDocumentChunk(Base):
    """Text chunk from a listing document with embedding."""

    __tablename__ = "listing_document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_document_id = Column(Integer, ForeignKey("listing_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # OpenAI embedding dimension
    metadata = Column(Text, nullable=True)  # JSON: page number, section, etc.

    # Relationships
    document = relationship("ListingDocument", back_populates="chunks")
