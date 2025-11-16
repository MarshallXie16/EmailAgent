"""Listing endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_broker
from app.core.database import get_db
from app.models.broker import Broker
from app.models.listing import Listing, ListingStatus
from app.schemas.listing import (
    ListingResponse,
    ListingCreate,
    ListingUpdate,
    ListingListResponse,
)

router = APIRouter()


@router.get("", response_model=ListingListResponse)
async def get_listings(
    status: Optional[ListingStatus] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Get broker's listings.

    Args:
        status: Filter by status
        search: Search in code, title, description
        skip: Offset
        limit: Limit
        current_broker: Authenticated broker
        db: Database session

    Returns:
        List of listings
    """
    query = select(Listing).where(Listing.broker_id == current_broker.id)

    # Apply filters
    if status:
        query = query.where(Listing.status == status)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Listing.code.ilike(search_pattern))
            | (Listing.title.ilike(search_pattern))
            | (Listing.short_description.ilike(search_pattern))
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Listing.created_at.desc())

    result = await db.execute(query)
    listings = result.scalars().all()

    return ListingListResponse(listings=listings, total=total)


@router.post("", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    listing_data: ListingCreate,
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new listing.

    Args:
        listing_data: Listing data
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Created listing
    """
    # Check if code already exists for this broker
    result = await db.execute(
        select(Listing).where(
            Listing.broker_id == current_broker.id,
            Listing.code == listing_data.code,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Listing with code '{listing_data.code}' already exists",
        )

    # Create listing
    listing = Listing(
        broker_id=current_broker.id,
        **listing_data.model_dump(),
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)

    return listing


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: UUID,
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a listing by ID.

    Args:
        listing_id: Listing UUID
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Listing details
    """
    result = await db.execute(
        select(Listing).where(
            Listing.id == listing_id,
            Listing.broker_id == current_broker.id,
        )
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    return listing


@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: UUID,
    listing_update: ListingUpdate,
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a listing.

    Args:
        listing_id: Listing UUID
        listing_update: Fields to update
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Updated listing
    """
    result = await db.execute(
        select(Listing).where(
            Listing.id == listing_id,
            Listing.broker_id == current_broker.id,
        )
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    # Update fields
    update_data = listing_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(listing, field, value)

    await db.commit()
    await db.refresh(listing)

    return listing


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: UUID,
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a listing (set status to archived).

    Args:
        listing_id: Listing UUID
        current_broker: Authenticated broker
        db: Database session
    """
    result = await db.execute(
        select(Listing).where(
            Listing.id == listing_id,
            Listing.broker_id == current_broker.id,
        )
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    listing.status = ListingStatus.ARCHIVED
    await db.commit()
