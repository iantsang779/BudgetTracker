from __future__ import annotations

"""Tests for the currency API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_rates_empty(client: AsyncClient) -> None:
    """Test listing rates when cache is empty."""
    response = await client.get("/api/v1/currency/rates")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_convert_same_currency(client: AsyncClient) -> None:
    """Test converting USD to USD returns same amount."""
    response = await client.post(
        "/api/v1/currency/convert",
        json={"amount": 100.0, "from_code": "USD", "to_code": "USD"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["converted"] == pytest.approx(100.0)
    assert data["rate"] == pytest.approx(1.0)
