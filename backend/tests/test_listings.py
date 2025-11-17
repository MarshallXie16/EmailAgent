"""Tests for listings API endpoints."""

import pytest
from httpx import AsyncClient

from app.main import app
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_create_listing(test_broker):
    """Test creating a listing."""
    token = create_access_token(data={"sub": str(test_broker.id)})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/listings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "code": "NEW001",
                "title": "New Restaurant",
                "asking_price": 750000,
                "revenue": 1000000,
                "sde": 200000,
                "location_region": "Boston, MA",
                "short_description": "High-end Italian restaurant",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "NEW001"
    assert data["title"] == "New Restaurant"
    assert float(data["asking_price"]) == 750000


@pytest.mark.asyncio
async def test_get_listings(test_broker, test_listing):
    """Test getting all listings."""
    token = create_access_token(data={"sub": str(test_broker.id)})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/listings",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["listings"]) >= 1
    assert data["listings"][0]["code"] == "TEST001"


@pytest.mark.asyncio
async def test_get_listing_by_id(test_broker, test_listing):
    """Test getting a specific listing."""
    token = create_access_token(data={"sub": str(test_broker.id)})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/listings/{test_listing.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "TEST001"
    assert data["title"] == "Test Coffee Shop"


@pytest.mark.asyncio
async def test_update_listing(test_broker, test_listing):
    """Test updating a listing."""
    token = create_access_token(data={"sub": str(test_broker.id)})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.patch(
            f"/api/v1/listings/{test_listing.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"asking_price": 550000, "short_description": "Updated description"},
        )

    assert response.status_code == 200
    data = response.json()
    assert float(data["asking_price"]) == 550000
    assert data["short_description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_listing(test_broker, test_listing):
    """Test deleting (archiving) a listing."""
    token = create_access_token(data={"sub": str(test_broker.id)})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/listings/{test_listing.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 204

    # Verify it's archived
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/listings/{test_listing.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "archived"


@pytest.mark.asyncio
async def test_search_listings(test_broker, test_listing):
    """Test searching listings."""
    token = create_access_token(data={"sub": str(test_broker.id)})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/listings?search=coffee",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert "coffee" in data["listings"][0]["title"].lower()
