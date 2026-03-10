from __future__ import annotations
"""Tests for the accounts API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_account(client: AsyncClient) -> None:
    """Test creating a new account."""
    response = await client.post(
        "/api/v1/accounts/",
        json={"name": "Checking", "currency_code": "USD", "balance_initial": 1000.0},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Checking"
    assert data["currency_code"] == "USD"
    assert data["balance_initial"] == 1000.0
    assert "id" in data


@pytest.mark.asyncio
async def test_list_accounts(client: AsyncClient) -> None:
    """Test listing accounts."""
    await client.post("/api/v1/accounts/", json={"name": "Savings"})
    await client.post("/api/v1/accounts/", json={"name": "Cash"})
    response = await client.get("/api/v1/accounts/")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_account_not_found(client: AsyncClient) -> None:
    """Test fetching a non-existent account returns 404."""
    response = await client.get("/api/v1/accounts/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_account(client: AsyncClient) -> None:
    """Test updating an account."""
    create_resp = await client.post("/api/v1/accounts/", json={"name": "Old Name"})
    account_id = create_resp.json()["id"]
    response = await client.patch(f"/api/v1/accounts/{account_id}", json={"name": "New Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_account(client: AsyncClient) -> None:
    """Test soft-deleting an account."""
    create_resp = await client.post("/api/v1/accounts/", json={"name": "ToDelete"})
    account_id = create_resp.json()["id"]
    delete_resp = await client.delete(f"/api/v1/accounts/{account_id}")
    assert delete_resp.status_code == 204
    get_resp = await client.get(f"/api/v1/accounts/{account_id}")
    assert get_resp.status_code == 404
