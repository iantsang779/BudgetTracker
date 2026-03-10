from __future__ import annotations

"""Tests for the income API."""

import pytest
from httpx import AsyncClient


async def _create_account(client: AsyncClient, name: str = "Test") -> int:
    resp = await client.post("/api/v1/accounts/", json={"name": name})
    return int(resp.json()["id"])


@pytest.mark.asyncio
async def test_create_income(client: AsyncClient) -> None:
    """Test creating an income entry."""
    acc_id = await _create_account(client)
    response = await client.post(
        "/api/v1/income/",
        json={
            "account_id": acc_id,
            "amount_local": 5000.0,
            "amount_base": 5000.0,
            "recurrence": "monthly",
            "description": "Salary",
            "effective_date": "2024-01-01T00:00:00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount_base"] == 5000.0
    assert data["recurrence"] == "monthly"


@pytest.mark.asyncio
async def test_income_summary(client: AsyncClient) -> None:
    """Test income summary aggregation."""
    acc_id = await _create_account(client)
    await client.post(
        "/api/v1/income/",
        json={
            "account_id": acc_id,
            "amount_local": 3000.0,
            "amount_base": 3000.0,
            "recurrence": "monthly",
            "effective_date": "2024-01-01T00:00:00",
        },
    )
    await client.post(
        "/api/v1/income/",
        json={
            "account_id": acc_id,
            "amount_local": 12000.0,
            "amount_base": 12000.0,
            "recurrence": "yearly",
            "effective_date": "2024-01-01T00:00:00",
        },
    )
    resp = await client.get("/api/v1/income/summary")
    assert resp.status_code == 200
    data = resp.json()
    # 3000/month + 12000/12=1000/month = 4000/month
    assert data["monthly_total_base"] == pytest.approx(4000.0)
    assert data["active_sources"] == 2


@pytest.mark.asyncio
async def test_delete_income(client: AsyncClient) -> None:
    """Test soft-deleting an income entry."""
    acc_id = await _create_account(client)
    create = await client.post(
        "/api/v1/income/",
        json={
            "account_id": acc_id,
            "amount_local": 1000.0,
            "amount_base": 1000.0,
            "recurrence": "one_off",
            "effective_date": "2024-06-01T00:00:00",
        },
    )
    entry_id = create.json()["id"]
    assert (await client.delete(f"/api/v1/income/{entry_id}")).status_code == 204
    assert (await client.get(f"/api/v1/income/{entry_id}")).status_code == 404
