from __future__ import annotations

"""Tests for the analytics API endpoints."""

import pytest
from httpx import AsyncClient


async def _create_account(client: AsyncClient) -> int:
    resp = await client.post("/api/v1/accounts/", json={"name": "Test Account"})
    assert resp.status_code == 201
    return int(resp.json()["id"])


async def _create_category(client: AsyncClient, name: str = "Food") -> int:
    resp = await client.post(
        "/api/v1/categories/",
        json={"name": name, "color_hex": "#ff5733"},
    )
    assert resp.status_code == 201
    return int(resp.json()["id"])


async def _create_transaction(
    client: AsyncClient,
    account_id: int,
    category_id: int,
    amount: float,
    date: str,
) -> None:
    resp = await client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "amount_local": amount,
            "currency_code": "USD",
            "amount_base": amount,
            "description": "test",
            "transaction_date": f"{date}T12:00:00",
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_metrics_empty_db(client: AsyncClient) -> None:
    """Metrics endpoint returns zeros on an empty database."""
    resp = await client.get("/api/v1/analytics/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_spending_base"] == 0.0
    assert data["predicted_monthly_base"] == 0.0
    assert data["savings_rate"] == 0.0
    assert data["monthly_income_base"] == 0.0
    assert data["regression_slope"] == 0.0
    assert data["regression_r2"] == 0.0


@pytest.mark.asyncio
async def test_metrics_with_spending(client: AsyncClient) -> None:
    """Metrics reflects created transactions."""
    acc_id = await _create_account(client)
    cat_id = await _create_category(client)
    await _create_transaction(client, acc_id, cat_id, 200.0, "2026-03-05")

    resp = await client.get("/api/v1/analytics/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_spending_base"] == pytest.approx(200.0)


@pytest.mark.asyncio
async def test_spending_by_category_percentages(client: AsyncClient) -> None:
    """Category percentages sum to 100 when multiple categories are present."""
    acc_id = await _create_account(client)
    cat1 = await _create_category(client, "Food")
    cat2 = await _create_category(client, "Transport")
    await _create_transaction(client, acc_id, cat1, 75.0, "2026-01-10")
    await _create_transaction(client, acc_id, cat2, 25.0, "2026-01-15")

    resp = await client.get("/api/v1/analytics/spending-by-category")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_base"] == pytest.approx(100.0)
    total_pct = sum(item["percentage"] for item in data["items"])
    assert abs(total_pct - 100.0) < 0.01


@pytest.mark.asyncio
async def test_spending_by_category_empty(client: AsyncClient) -> None:
    """Spending by category returns empty list on empty database."""
    resp = await client.get("/api/v1/analytics/spending-by-category")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total_base"] == 0.0


@pytest.mark.asyncio
async def test_savings_projection_fallback(client: AsyncClient) -> None:
    """Projection falls back to average when fewer than 3 months of history."""
    acc_id = await _create_account(client)
    cat_id = await _create_category(client)
    await _create_transaction(client, acc_id, cat_id, 100.0, "2026-01-05")

    resp = await client.get("/api/v1/analytics/savings-projection")
    assert resp.status_code == 200
    data = resp.json()
    assert data["slope"] == 0.0
    assert data["r2_score"] == 0.0
    # 1 historical + 6 projected = 7 total points
    assert len(data["points"]) == 7
    # The first point is historical (has actual)
    assert data["points"][0]["actual"] == pytest.approx(100.0)
    # All projected points have actual=None
    for pt in data["points"][1:]:
        assert pt["actual"] is None


@pytest.mark.asyncio
async def test_savings_projection_regression(client: AsyncClient) -> None:
    """Projection runs regression for 4+ months of historical data."""
    acc_id = await _create_account(client)
    cat_id = await _create_category(client)
    for month, amount in [
        ("2025-09", 100.0),
        ("2025-10", 120.0),
        ("2025-11", 140.0),
        ("2025-12", 160.0),
    ]:
        await _create_transaction(client, acc_id, cat_id, amount, f"{month}-01")

    resp = await client.get("/api/v1/analytics/savings-projection")
    assert resp.status_code == 200
    data = resp.json()
    # 4 historical + 6 projected
    assert len(data["points"]) == 10
    assert data["r2_score"] > 0.99  # perfect linear trend → R²≈1
    assert data["slope"] > 0  # spending is increasing


@pytest.mark.asyncio
async def test_spending_over_time_groups_by_month(client: AsyncClient) -> None:
    """Two transactions in the same month produce one data point."""
    acc_id = await _create_account(client)
    cat_id = await _create_category(client)
    await _create_transaction(client, acc_id, cat_id, 50.0, "2026-02-01")
    await _create_transaction(client, acc_id, cat_id, 30.0, "2026-02-15")

    resp = await client.get("/api/v1/analytics/spending-over-time")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["points"]) == 1
    assert data["points"][0]["period"] == "2026-02"
    assert data["points"][0]["total_base"] == pytest.approx(80.0)


@pytest.mark.asyncio
async def test_spending_over_time_empty(client: AsyncClient) -> None:
    """Spending over time returns empty list on empty database."""
    resp = await client.get("/api/v1/analytics/spending-over-time")
    assert resp.status_code == 200
    assert resp.json()["points"] == []
