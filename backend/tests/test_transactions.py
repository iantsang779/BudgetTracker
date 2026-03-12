from __future__ import annotations

"""Tests for the transactions API."""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.currency_rate import CurrencyRate


async def _create_account(client: AsyncClient, name: str = "Test") -> int:
    """Helper to create an account and return its ID."""
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
async def test_create_transaction(client: AsyncClient) -> None:
    """Test creating a transaction."""
    acc_id = await _create_account(client)
    response = await client.post(
        "/api/v1/transactions/",
        json={
            "account_id": acc_id,
            "amount_local": 50.0,
            "amount_base": 50.0,
            "transaction_date": "2024-01-15T12:00:00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount_local"] == 50.0
    assert data["account_id"] == acc_id


@pytest.mark.asyncio
async def test_list_transactions_filter_by_account(client: AsyncClient) -> None:
    """Test filtering transactions by account."""
    acc1 = await _create_account(client, "Acc1")
    acc2 = await _create_account(client, "Acc2")
    await client.post(
        "/api/v1/transactions/",
        json={
            "account_id": acc1,
            "amount_local": 10.0,
            "amount_base": 10.0,
            "transaction_date": "2024-01-01T00:00:00",
        },
    )
    await client.post(
        "/api/v1/transactions/",
        json={
            "account_id": acc2,
            "amount_local": 20.0,
            "amount_base": 20.0,
            "transaction_date": "2024-01-02T00:00:00",
        },
    )
    resp = await client.get(f"/api/v1/transactions/?account_id={acc1}")
    assert resp.status_code == 200
    txns = resp.json()
    assert len(txns) == 1
    assert txns[0]["account_id"] == acc1


@pytest.mark.asyncio
async def test_create_transaction_gbp_amount_base_converted_to_usd(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GBP transaction: server must convert amount_local to USD for amount_base.

    Regression test for bug where amount_base was stored verbatim from the client,
    causing display values to be wrong (e.g. 6000 GBP stored as 6000 "USD",
    then shown as ~4477 GBP after applying the USD→GBP display rate).
    """
    await _seed_rate(db_session, "GBP", "USD", 1.25)  # 1 GBP = 1.25 USD
    acc_id = await _create_account(client)
    response = await client.post(
        "/api/v1/transactions/",
        json={
            "account_id": acc_id,
            "amount_local": 6000.0,
            "currency_code": "GBP",
            "amount_base": 6000.0,  # intentionally wrong — server must override
            "transaction_date": "2024-03-01T12:00:00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    # Server converts 6000 GBP → USD using rate 1.25 → 7500 USD
    assert data["amount_local"] == pytest.approx(6000.0)
    assert data["currency_code"] == "GBP"
    assert data["amount_base"] == pytest.approx(7500.0)


@pytest.mark.asyncio
async def test_delete_transaction(client: AsyncClient) -> None:
    """Test soft-deleting a transaction."""
    acc_id = await _create_account(client)
    create = await client.post(
        "/api/v1/transactions/",
        json={
            "account_id": acc_id,
            "amount_local": 5.0,
            "amount_base": 5.0,
            "transaction_date": "2024-01-10T00:00:00",
        },
    )
    txn_id = create.json()["id"]
    assert (await client.delete(f"/api/v1/transactions/{txn_id}")).status_code == 204
    assert (await client.get(f"/api/v1/transactions/{txn_id}")).status_code == 404
