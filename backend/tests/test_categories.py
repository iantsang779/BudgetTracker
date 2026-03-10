from __future__ import annotations

"""Tests for the categories API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient) -> None:
    """Test creating a category."""
    response = await client.post(
        "/api/v1/categories/",
        json={"name": "Groceries", "color_hex": "#ff0000", "is_income": False},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Groceries"
    assert data["is_income"] is False


@pytest.mark.asyncio
async def test_list_categories_filtered(client: AsyncClient) -> None:
    """Test listing categories filtered by type."""
    await client.post("/api/v1/categories/", json={"name": "Salary", "is_income": True})
    await client.post("/api/v1/categories/", json={"name": "Rent", "is_income": False})
    resp = await client.get("/api/v1/categories/?is_income=false")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "Rent" in names
    assert "Salary" not in names


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient) -> None:
    """Test soft-deleting a category."""
    create = await client.post("/api/v1/categories/", json={"name": "TempCat"})
    cat_id = create.json()["id"]
    assert (await client.delete(f"/api/v1/categories/{cat_id}")).status_code == 204
    assert (await client.get(f"/api/v1/categories/{cat_id}")).status_code == 404
