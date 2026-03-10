from __future__ import annotations
"""Tests for the transactions API."""

import pytest
from httpx import AsyncClient


async def _create_account(client: AsyncClient, name: str = "Test") -> int:
    """Helper to create an account and return its ID."""
    resp = await client.post("/api/v1/accounts/", json={"name": name})
    return int(resp.json()["id"])


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
        json={"account_id": acc1, "amount_local": 10.0, "amount_base": 10.0, "transaction_date": "2024-01-01T00:00:00"},
    )
    await client.post(
        "/api/v1/transactions/",
        json={"account_id": acc2, "amount_local": 20.0, "amount_base": 20.0, "transaction_date": "2024-01-02T00:00:00"},
    )
    resp = await client.get(f"/api/v1/transactions/?account_id={acc1}")
    assert resp.status_code == 200
    txns = resp.json()
    assert len(txns) == 1
    assert txns[0]["account_id"] == acc1


@pytest.mark.asyncio
async def test_delete_transaction(client: AsyncClient) -> None:
    """Test soft-deleting a transaction."""
    acc_id = await _create_account(client)
    create = await client.post(
        "/api/v1/transactions/",
        json={"account_id": acc_id, "amount_local": 5.0, "amount_base": 5.0, "transaction_date": "2024-01-10T00:00:00"},
    )
    txn_id = create.json()["id"]
    assert (await client.delete(f"/api/v1/transactions/{txn_id}")).status_code == 204
    assert (await client.get(f"/api/v1/transactions/{txn_id}")).status_code == 404
