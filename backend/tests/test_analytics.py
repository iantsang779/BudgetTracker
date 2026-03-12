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
    assert data["savings_rate"] == 0.0
    assert data["monthly_income_base"] == 0.0


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
async def test_cumulative_spending_empty(client: AsyncClient) -> None:
    """Cumulative spending returns empty points on empty database."""
    resp = await client.get("/api/v1/analytics/spending-cumulative")
    assert resp.status_code == 200
    data = resp.json()
    assert data["points"] == []


@pytest.mark.asyncio
async def test_cumulative_spending_groups_by_month(client: AsyncClient) -> None:
    """Cumulative spending accumulates across months within the year."""
    acc_id = await _create_account(client)
    cat_id = await _create_category(client)
    await _create_transaction(client, acc_id, cat_id, 100.0, "2026-01-05")
    await _create_transaction(client, acc_id, cat_id, 50.0, "2026-01-20")
    await _create_transaction(client, acc_id, cat_id, 200.0, "2026-02-10")

    resp = await client.get("/api/v1/analytics/spending-cumulative?year=2026")
    assert resp.status_code == 200
    data = resp.json()
    assert data["year"] == 2026
    assert len(data["points"]) == 2
    assert data["points"][0]["period"] == "2026-01"
    assert data["points"][0]["monthly_total"] == pytest.approx(150.0)
    assert data["points"][0]["cumulative_total"] == pytest.approx(150.0)
    assert data["points"][1]["period"] == "2026-02"
    assert data["points"][1]["monthly_total"] == pytest.approx(200.0)
    assert data["points"][1]["cumulative_total"] == pytest.approx(350.0)


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


# ---------------------------------------------------------------------------
# Year query-parameter validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_spending_cumulative_year_below_minimum_rejected(client: AsyncClient) -> None:
    """year=1999 is below ge=2000 and must return 422."""
    resp = await client.get("/api/v1/analytics/spending-cumulative?year=1999")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_spending_cumulative_year_above_maximum_rejected(client: AsyncClient) -> None:
    """year=2101 is above le=2100 and must return 422."""
    resp = await client.get("/api/v1/analytics/spending-cumulative?year=2101")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_savings_cumulative_year_below_minimum_rejected(client: AsyncClient) -> None:
    """year=1999 is below ge=2000 and must return 422."""
    resp = await client.get("/api/v1/analytics/savings-cumulative?year=1999")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_savings_cumulative_year_above_maximum_rejected(client: AsyncClient) -> None:
    """year=2101 is above le=2100 and must return 422."""
    resp = await client.get("/api/v1/analytics/savings-cumulative?year=2101")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Savings-cumulative endpoint
# ---------------------------------------------------------------------------


async def _create_income(
    client: AsyncClient,
    account_id: int,
    amount: float,
    recurrence: str = "monthly",
    effective_date: str = "2024-01-01T00:00:00",
) -> None:
    resp = await client.post(
        "/api/v1/income/",
        json={
            "account_id": account_id,
            "amount_local": amount,
            "currency_code": "USD",
            "amount_base": amount,
            "recurrence": recurrence,
            "effective_date": effective_date,
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_savings_cumulative_empty(client: AsyncClient) -> None:
    """No transactions → empty points list."""
    resp = await client.get("/api/v1/analytics/savings-cumulative")
    assert resp.status_code == 200
    data = resp.json()
    assert data["points"] == []


@pytest.mark.asyncio
async def test_savings_cumulative_positive_savings(client: AsyncClient) -> None:
    """Income 1000/month from Jan 2026, spending 400 in Jan.

    Jan has spending; subsequent months (up to current) are included because
    income is still active even with zero spending.
    """
    acc_id = await _create_account(client)
    cat_id = await _create_category(client)
    await _create_income(client, acc_id, 1000.0, effective_date="2026-01-01T00:00:00")
    await _create_transaction(client, acc_id, cat_id, 400.0, "2026-01-15")

    resp = await client.get("/api/v1/analytics/savings-cumulative?year=2026")
    assert resp.status_code == 200
    data = resp.json()
    assert data["year"] == 2026
    # At least January; subsequent months with active income are also included
    assert len(data["points"]) >= 1
    pt = data["points"][0]
    assert pt["period"] == "2026-01"
    assert pt["monthly_income"] == pytest.approx(1000.0)
    assert pt["monthly_spending"] == pytest.approx(400.0)
    assert pt["monthly_saving"] == pytest.approx(600.0)
    assert pt["cumulative_saving"] == pytest.approx(600.0)


@pytest.mark.asyncio
async def test_savings_cumulative_accumulates_across_months(client: AsyncClient) -> None:
    """Running cumulative saving adds up correctly across multiple months.

    Income-only months (no spending) after Feb are also included because
    the income entry is still active.
    """
    acc_id = await _create_account(client)
    cat_id = await _create_category(client)
    await _create_income(client, acc_id, 1000.0, effective_date="2026-01-01T00:00:00")
    await _create_transaction(client, acc_id, cat_id, 300.0, "2026-01-10")
    await _create_transaction(client, acc_id, cat_id, 500.0, "2026-02-10")

    resp = await client.get("/api/v1/analytics/savings-cumulative?year=2026")
    assert resp.status_code == 200
    pts = resp.json()["points"]
    # At least Jan + Feb; subsequent income-only months also included
    assert len(pts) >= 2
    # Jan: income 1000 - spending 300 = saving 700, cumulative 700
    assert pts[0]["period"] == "2026-01"
    assert pts[0]["monthly_saving"] == pytest.approx(700.0)
    assert pts[0]["cumulative_saving"] == pytest.approx(700.0)
    # Feb: income 1000 - spending 500 = saving 500, cumulative 1200
    assert pts[1]["period"] == "2026-02"
    assert pts[1]["monthly_saving"] == pytest.approx(500.0)
    assert pts[1]["cumulative_saving"] == pytest.approx(1200.0)


@pytest.mark.asyncio
async def test_savings_cumulative_year_filter_excludes_other_years(
    client: AsyncClient,
) -> None:
    """Transactions from a different year are excluded when year= is specified.

    The income entry started in 2025 but is still active in 2026, so all
    months in 2026 up to the current month are included.
    """
    acc_id = await _create_account(client)
    cat_id = await _create_category(client)
    await _create_income(client, acc_id, 1000.0, effective_date="2025-01-01T00:00:00")
    await _create_transaction(client, acc_id, cat_id, 200.0, "2025-06-01")
    await _create_transaction(client, acc_id, cat_id, 300.0, "2026-01-15")

    resp = await client.get("/api/v1/analytics/savings-cumulative?year=2026")
    assert resp.status_code == 200
    pts = resp.json()["points"]
    # No 2025 periods in the result
    assert all(p["period"].startswith("2026-") for p in pts)
    # The first point is January 2026 with the correct spending
    assert pts[0]["period"] == "2026-01"
    assert pts[0]["monthly_spending"] == pytest.approx(300.0)


@pytest.mark.asyncio
async def test_savings_cumulative_income_not_yet_active_excluded(
    client: AsyncClient,
) -> None:
    """Income whose effective_date is after the transaction month is not counted.

    January has spending but no active income (income starts March).
    February has neither spending nor active income — excluded.
    March has active income but no spending — included as an income-only month.
    """
    acc_id = await _create_account(client)
    cat_id = await _create_category(client)
    # Income starts in March — should not count for January spending
    await _create_income(client, acc_id, 2000.0, effective_date="2026-03-01T00:00:00")
    await _create_transaction(client, acc_id, cat_id, 100.0, "2026-01-10")

    resp = await client.get("/api/v1/analytics/savings-cumulative?year=2026")
    assert resp.status_code == 200
    pts = resp.json()["points"]
    # Jan (spending only) and Mar (income active, zero spending) are included
    jan = next(p for p in pts if p["period"] == "2026-01")
    assert jan["monthly_income"] == pytest.approx(0.0)
    assert jan["monthly_saving"] == pytest.approx(-100.0)
    # March is also present with income active
    mar = next(p for p in pts if p["period"] == "2026-03")
    assert mar["monthly_income"] == pytest.approx(2000.0)
    assert mar["monthly_spending"] == pytest.approx(0.0)
