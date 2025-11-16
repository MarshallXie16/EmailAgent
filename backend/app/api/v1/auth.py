"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.broker import Broker
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login endpoint to authenticate broker and return JWT tokens.

    Args:
        credentials: Email and password
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    # Get broker by email
    result = await db.execute(
        select(Broker).where(Broker.email == credentials.email)
    )
    broker = result.scalar_one_or_none()

    # Verify broker exists and password is correct
    if not broker or not verify_password(credentials.password, broker.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(broker.id)})
    refresh_token = create_refresh_token(data={"sub": str(broker.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Args:
        request: Refresh token
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        payload = decode_token(request.refresh_token)

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        broker_id = payload.get("sub")
        if not broker_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Verify broker still exists
        result = await db.execute(
            select(Broker).where(Broker.id == broker_id)
        )
        broker = result.scalar_one_or_none()

        if not broker:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Broker not found",
            )

        # Create new tokens
        access_token = create_access_token(data={"sub": str(broker.id)})
        refresh_token = create_refresh_token(data={"sub": str(broker.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )
