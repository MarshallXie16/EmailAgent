"""API dependencies for authentication and authorization."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.broker import Broker

security = HTTPBearer()


async def get_current_broker(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Broker:
    """
    Get the current authenticated broker from JWT token.

    Args:
        credentials: HTTP bearer token credentials
        db: Database session

    Returns:
        Authenticated broker

    Raises:
        HTTPException: If token is invalid or broker not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = decode_token(token)

        # Check token type
        if payload.get("type") != "access":
            raise credentials_exception

        broker_id: Optional[str] = payload.get("sub")
        if broker_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get broker from database
    result = await db.execute(select(Broker).where(Broker.id == broker_id))
    broker = result.scalar_one_or_none()

    if broker is None:
        raise credentials_exception

    return broker
