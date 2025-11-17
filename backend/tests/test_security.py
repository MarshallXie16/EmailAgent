"""Tests for security utilities."""

import pytest
from datetime import timedelta

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "testpassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_create_access_token():
    """Test creating access token."""
    data = {"sub": "user123"}
    token = create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    payload = decode_token(token)
    assert payload["sub"] == "user123"
    assert payload["type"] == "access"


def test_create_refresh_token():
    """Test creating refresh token."""
    data = {"sub": "user123"}
    token = create_refresh_token(data)

    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    payload = decode_token(token)
    assert payload["sub"] == "user123"
    assert payload["type"] == "refresh"


def test_token_with_custom_expiration():
    """Test creating token with custom expiration."""
    data = {"sub": "user123"}
    token = create_access_token(data, expires_delta=timedelta(minutes=5))

    payload = decode_token(token)
    assert "exp" in payload


def test_decode_invalid_token():
    """Test decoding invalid token."""
    from jose import JWTError

    with pytest.raises(JWTError):
        decode_token("invalid.token.here")
