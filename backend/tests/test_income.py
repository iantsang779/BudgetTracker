from __future__ import annotations

"""Tests for the income API."""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.currency_rate import CurrencyRate


async def _create_account(client: AsyncClient, name: str = "Test") -> int:
    resp = await client.post("/api/v1/accounts/", json={"name": name})
    return int(resp.json()["id"])


async def _seed_rate(db: AsyncSession, base: str, target: str, rate: float) -> None:
    """Insert a fresh currency rate so CurrencyService finds it without a live API call."""
    db.add(
        CurrencyRate(
            base_code=base,
            target_code=target,
            rate=rate,
            fetched_at=datetime.now(UTC).replace(tzinfo=None),
        )
    )
    await db.flush()


@pytest.mark.asyncio
async def test_create_income_usd(client: AsyncClient) -> None:
    """USD income: amount_base equals amount_local (rate 1.0)."""
    acc_id = await _create_account(client)
    response = await client.post(
        "/api/v1/income/",
        json={
            "account_id": acc_id,
            "amount_local": 5000.0,
            "currency_code": "USD",
            "amount_base": 5000.0,
            "recurrence": "monthly",
            "description": "Salary",
            "effective_date": "2024-01-01T00:00:00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount_base"] == pytest.approx(5000.0)
    assert data["recurrence"] == "monthly"


@pytest.mark.asyncio
async def test_create_income_gbp_amount_base_converted_to_usd(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GBP income: server must convert amount_local to USD for amount_base.

    Regression test for bug where amount_base was stored as-is from the client,
    causing the display value (amount_base * USD→GBP rate) to be wrong.
    Example: 6000 GBP stored as 6000 "USD" → displayed as ~4477 GBP.
    """
    await _seed_rate(db_session, "GBP", "USD", 1.25)  # 1 GBP = 1.25 USD
    acc_id = await _create_account(client)
    response = await client.post(
        "/api/v1/income/",
        json={
            "account_id": acc_id,
            "amount_local": 6000.0,
            "currency_code": "GBP",
            "amount_base": 6000.0,  # intentionally wrong — server must override
            "recurrence": "monthly",
            "description": "Salary GBP",
            "effective_date": "2024-01-01T00:00:00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    # Server converts 6000 GBP → USD using rate 1.25 → 7500 USD
    assert data["amount_local"] == pytest.approx(6000.0)
    assert data["currency_code"] == "GBP"
    assert data["amount_base"] == pytest.approx(7500.0)


@pytest.mark.asyncio
async def test_update_income_gbp_recomputes_amount_base(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Updating amount_local on a GBP income entry recomputes amount_base."""
    await _seed_rate(db_session, "GBP", "USD", 1.25)
    acc_id = await _create_account(client)
    create = await client.post(
        "/api/v1/income/",
        json={
            "account_id": acc_id,
            "amount_local": 3000.0,
            "currency_code": "GBP",
            "amount_base": 3000.0,
            "recurrence": "monthly",
            "effective_date": "2024-01-01T00:00:00",
        },
    )
    entry_id = create.json()["id"]
    patch = await client.patch(
        f"/api/v1/income/{entry_id}",
        json={"amount_local": 4000.0},
    )
    assert patch.status_code == 200
    # 4000 GBP * 1.25 = 5000 USD
    assert patch.json()["amount_base"] == pytest.approx(5000.0)


@pytest.mark.asyncio
async def test_income_summary(client: AsyncClient) -> None:
    """Test income summary aggregation (USD so amount_base == amount_local)."""
    acc_id = await _create_account(client)
    await client.post(
        "/api/v1/income/",
        json={
            "account_id": acc_id,
            "amount_local": 3000.0,
            "currency_code": "USD",
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
            "currency_code": "USD",
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
            "currency_code": "USD",
            "amount_base": 1000.0,
            "recurrence": "monthly",
            "effective_date": "2024-06-01T00:00:00",
        },
    )
    assert create.status_code == 201, create.text
    entry_id = create.json()["id"]
    assert (await client.delete(f"/api/v1/income/{entry_id}")).status_code == 204
    assert (await client.get(f"/api/v1/income/{entry_id}")).status_code == 404
