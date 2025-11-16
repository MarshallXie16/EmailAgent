"""Settings endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_broker
from app.core.database import get_db
from app.models.broker import Broker, BrokerSettings
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Get broker settings.

    Args:
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Broker settings
    """
    result = await db.execute(
        select(BrokerSettings).where(BrokerSettings.broker_id == current_broker.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings if they don't exist
        settings = BrokerSettings(
            broker_id=current_broker.id,
            auto_send_enabled=False,
            batch_windows=[],
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    settings_update: SettingsUpdate,
    current_broker: Broker = Depends(get_current_broker),
    db: AsyncSession = Depends(get_db),
):
    """
    Update broker settings.

    Args:
        settings_update: Settings to update
        current_broker: Authenticated broker
        db: Database session

    Returns:
        Updated settings
    """
    result = await db.execute(
        select(BrokerSettings).where(BrokerSettings.broker_id == current_broker.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found",
        )

    # Update fields
    update_data = settings_update.model_dump(exclude_unset=True)

    # Convert batch_windows to dict if present
    if "batch_windows" in update_data:
        update_data["batch_windows"] = [
            {"start": w.start, "end": w.end} for w in update_data["batch_windows"]
        ]

    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    return settings
