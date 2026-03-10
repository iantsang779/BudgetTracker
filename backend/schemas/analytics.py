from __future__ import annotations

"""Analytics Pydantic schemas."""

from pydantic import BaseModel


class MetricsResponse(BaseModel):
    """Live KPI metrics."""

    total_spending_base: float
    predicted_monthly_base: float
    savings_rate: float
    inflation_adjusted_spending: float
    monthly_income_base: float
    regression_slope: float
    regression_r2: float


class ProjectionPoint(BaseModel):
    """A single point in the savings projection chart."""

    period: str  # YYYY-MM
    actual: float | None
    predicted: float
    upper_band: float
    lower_band: float


class SavingsProjectionResponse(BaseModel):
    """Savings projection data for charting."""

    points: list[ProjectionPoint]
    slope: float
    r2_score: float
    error_std: float


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
