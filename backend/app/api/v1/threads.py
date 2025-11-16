"""Email thread endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_broker
from app.core.database import get_db
from app.models.broker import Broker
from app.models.email import EmailThread, ThreadStatus
from app.schemas.thread import ThreadResponse, ThreadListResponse

router = APIRouter()


@router.get("", response_model=ThreadListResponse)
async def get_threads(
    status: Optional[ThreadStatus] = Query(None),
    listing_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Get broker's email threads.

    Args:
        status: Filter by status
        listing_id: Filter by listing
        skip: Offset
        limit: Limit
        current_broker: Authenticated broker
        db: Database session

    Returns:
        List of threads
    """
    query = select(EmailThread).where(EmailThread.broker_id == current_broker.id)

    # Apply filters
    if status:
        query = query.where(EmailThread.status == status)

    if listing_id:
        query = query.where(EmailThread.listing_id == listing_id)

    # Eagerly load messages
    query = query.options(selectinload(EmailThread.messages))

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(EmailThread.updated_at.desc())

    result = await db.execute(query)
    threads = result.scalars().all()

    # Get total count
    count_query = select(EmailThread).where(EmailThread.broker_id == current_broker.id)
    if status:
        count_query = count_query.where(EmailThread.status == status)
    if listing_id:
        count_query = count_query.where(EmailThread.listing_id == listing_id)

    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return ThreadListResponse(threads=threads, total=total)


@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: UUID,
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a thread by ID with all messages.

    Args:
        thread_id: Thread UUID
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Thread details with messages
    """
    result = await db.execute(
        select(EmailThread)
        .where(
            EmailThread.id == thread_id,
            EmailThread.broker_id == current_broker.id,
        )
        .options(selectinload(EmailThread.messages))
    )
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    return thread
