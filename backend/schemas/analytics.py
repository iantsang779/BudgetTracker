from __future__ import annotations

"""Analytics Pydantic schemas."""

from pydantic import BaseModel


class MetricsResponse(BaseModel):
    """Live KPI metrics."""

    total_spending_base: float
    savings_rate: float
    inflation_adjusted_spending: float
    monthly_income_base: float


class CumulativePoint(BaseModel):
    """A single month's spending in the cumulative chart."""

    period: str  # YYYY-MM
    monthly_total: float
    cumulative_total: float


class CumulativeSpendingResponse(BaseModel):
    """Cumulative spending data for a given year."""

    points: list[CumulativePoint]
    year: int


class CategorySpending(BaseModel):
    """Spending total for a single category."""

    category_id: int | None
    category_name: str
    color_hex: str
    total_base: float
    percentage: float


class SpendingByCategoryResponse(BaseModel):
    """Spending grouped by category."""

    items: list[CategorySpending]
    total_base: float


class SpendingOverTimePoint(BaseModel):
    """Monthly spending data point."""

    period: str  # YYYY-MM
    total_base: float


class SpendingOverTimeResponse(BaseModel):
    """Monthly spending timeseries."""

    points: list[SpendingOverTimePoint]
