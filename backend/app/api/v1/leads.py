"""Lead endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_broker
from app.core.database import get_db
from app.models.broker import Broker
from app.models.lead import Lead
from app.schemas.lead import LeadResponse

router = APIRouter()


@router.get("", response_model=list[LeadResponse])
async def get_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Get broker's leads.

    Args:
        skip: Offset
        limit: Limit
        current_broker: Authenticated broker
        db: Database session

    Returns:
        List of leads
    """
    query = (
        select(Lead)
        .where(Lead.broker_id == current_broker.id)
        .offset(skip)
        .limit(limit)
        .order_by(Lead.created_at.desc())
    )

    result = await db.execute(query)
    leads = result.scalars().all()

    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a lead by ID.

    Args:
        lead_id: Lead UUID
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Lead details
    """
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.broker_id == current_broker.id,
        )
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return lead
