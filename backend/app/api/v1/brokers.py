"""Broker endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_broker
from app.models.broker import Broker
from app.schemas.broker import BrokerResponse

router = APIRouter()


@router.get("/me", response_model=BrokerResponse)
async def get_current_broker_info(
    current_broker: Broker = Depends(get_current_broker),
):
    """
    Get current authenticated broker's information.

    Args:
        current_broker: Authenticated broker from JWT

    Returns:
        Broker information
    """
    return current_broker
