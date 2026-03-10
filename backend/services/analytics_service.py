from __future__ import annotations

"""Analytics service for KPI computation and regression-based spending projections."""

import logging
from datetime import UTC, date, datetime, time
from typing import NamedTuple

import numpy as np
from sklearn.linear_model import LinearRegression  # type: ignore[import-untyped]
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.category import Category
from backend.models.transaction import Transaction
from backend.repositories.income_repository import IncomeRepository
from backend.schemas.analytics import (
    CategorySpending,
    MetricsResponse,
    ProjectionPoint,
    SavingsProjectionResponse,
    SpendingByCategoryResponse,
    SpendingOverTimePoint,
    SpendingOverTimeResponse,
)
from backend.services.income_helpers import monthly_base
from backend.services.inflation_service import InflationService

logger = logging.getLogger(__name__)


class _RegResult(NamedTuple):
    """Internal result from the regression helper."""

    slope: float
    intercept: float
    r2: float
    error_std: float
    predicted_next: float  # prediction for the next month (index n)


class AnalyticsService:
    """Provides spending KPI metrics and regression-based projections.

    Args:
        session: Async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialise with a database session."""
        self.session = session

    async def get_metrics(self) -> MetricsResponse:
        """Compute live KPI metrics.

        Returns:
            MetricsResponse with spending totals, regression stats, savings rate,
            and inflation-adjusted current-month spending.
        """
        # All-time total spending
        total_result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount_base), 0.0)).where(
                Transaction.deleted_at.is_(None)
            )
        )
        total_spending: float = float(total_result.scalar_one())

        # Current calendar-month spending
        now = datetime.now(UTC)
        current_month = f"{now.year}-{now.month:02d}"
        month_result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount_base), 0.0)).where(
                Transaction.deleted_at.is_(None),
                func.strftime("%Y-%m", Transaction.transaction_date) == current_month,
            )
        )
        spending_current_month: float = float(month_result.scalar_one())

        # Monthly income from active entries
        income_repo = IncomeRepository(self.session)
        income_entries = await income_repo.list_active()
        monthly_income: float = sum(
            monthly_base(e.amount_base, e.recurrence) for e in income_entries
        )

        # Savings rate clamped to [0, 1]
        savings_rate = (
            max(0.0, min(1.0, (monthly_income - spending_current_month) / monthly_income))
            if monthly_income > 0
            else 0.0
        )

        # Inflation-adjusted current-month spending (real dollars vs. last year)
        inflation_svc = InflationService(self.session)
        inflation_rate = await inflation_svc.get_annual_rate()
        inflation_adjusted = spending_current_month / (1.0 + inflation_rate)

        # Regression for slope, R², and next-month prediction
        monthly_totals = await self._monthly_spend_totals()
        reg = self._fit_regression(monthly_totals)

        return MetricsResponse(
            total_spending_base=total_spending,
            predicted_monthly_base=reg.predicted_next,
            savings_rate=savings_rate,
            inflation_adjusted_spending=inflation_adjusted,
            monthly_income_base=monthly_income,
            regression_slope=reg.slope,
            regression_r2=reg.r2,
        )

    async def get_savings_projection(self, months_ahead: int = 6) -> SavingsProjectionResponse:
        """Build historical + projected spending chart data.

        For historical months both the actual total and regression-line value are
        returned. Future months have ``actual=None``. Every point includes ±1σ
        error bands derived from regression residuals.

        Args:
            months_ahead: Number of future months to forecast.

        Returns:
            SavingsProjectionResponse with all chart points and regression stats.
        """
        monthly_totals = await self._monthly_spend_totals()
        n = len(monthly_totals)
        reg = self._fit_regression(monthly_totals)

        points: list[ProjectionPoint] = []

        # Historical: actual + regression line
        for i, (period, actual) in enumerate(monthly_totals):
            predicted = max(0.0, reg.slope * i + reg.intercept)
            points.append(
                ProjectionPoint(
                    period=period,
                    actual=actual,
                    predicted=predicted,
                    upper_band=predicted + reg.error_std,
                    lower_band=max(0.0, predicted - reg.error_std),
                )
            )

        # Projected future months
        last_period = monthly_totals[-1][0] if monthly_totals else self._current_period()
        for i in range(months_ahead):
            idx = n + i
            predicted = max(0.0, reg.slope * idx + reg.intercept)
            points.append(
                ProjectionPoint(
                    period=self._add_months(last_period, i + 1),
                    actual=None,
                    predicted=predicted,
                    upper_band=predicted + reg.error_std,
                    lower_band=max(0.0, predicted - reg.error_std),
                )
            )

        return SavingsProjectionResponse(
            points=points,
            slope=reg.slope,
            r2_score=reg.r2,
            error_std=reg.error_std,
        )

    async def get_spending_by_category(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> SpendingByCategoryResponse:
        """Aggregate non-deleted spending grouped by category.

        Transactions without a category appear as "Uncategorized".

        Args:
            start_date: Optional inclusive start of date range.
            end_date: Optional inclusive end of date range.

        Returns:
            SpendingByCategoryResponse with per-category totals and percentages.
        """
        stmt = (
            select(
                Transaction.category_id,
                func.coalesce(Category.name, "Uncategorized").label("name"),
                func.coalesce(Category.color_hex, "#9ca3af").label("color_hex"),
                func.sum(Transaction.amount_base).label("total"),
            )
            .outerjoin(Category, Transaction.category_id == Category.id)
            .where(Transaction.deleted_at.is_(None))
        )
        if start_date is not None:
            stmt = stmt.where(
                Transaction.transaction_date >= datetime.combine(start_date, time.min)
            )
        if end_date is not None:
            stmt = stmt.where(Transaction.transaction_date <= datetime.combine(end_date, time.max))
        stmt = stmt.group_by(Transaction.category_id)

        result = await self.session.execute(stmt)
        rows = result.mappings().all()

        total_base = float(sum(float(r["total"] or 0) for r in rows))
        items = [
            CategorySpending(
                category_id=r["category_id"],
                category_name=str(r["name"]),
                color_hex=str(r["color_hex"]),
                total_base=float(r["total"] or 0),
                percentage=(float(r["total"] or 0) / total_base * 100 if total_base > 0 else 0.0),
            )
            for r in rows
        ]
        return SpendingByCategoryResponse(items=items, total_base=total_base)

    async def get_spending_over_time(self) -> SpendingOverTimeResponse:
        """Compute monthly spending timeseries.

        Returns:
            SpendingOverTimeResponse with chronologically ordered monthly points.
        """
        result = await self.session.execute(
            select(
                func.strftime("%Y-%m", Transaction.transaction_date).label("period"),
                func.sum(Transaction.amount_base).label("total"),
            )
            .where(Transaction.deleted_at.is_(None))
            .group_by(func.strftime("%Y-%m", Transaction.transaction_date))
            .order_by(func.strftime("%Y-%m", Transaction.transaction_date))
        )
        rows = result.mappings().all()
        return SpendingOverTimeResponse(
            points=[
                SpendingOverTimePoint(
                    period=str(r["period"]),
                    total_base=float(r["total"] or 0),
                )
                for r in rows
            ]
        )

    async def _monthly_spend_totals(self) -> list[tuple[str, float]]:
        """Fetch per-month spending totals ordered chronologically.

        Returns:
            List of ``(YYYY-MM, total_amount_base)`` tuples.
        """
        result = await self.session.execute(
            select(
                func.strftime("%Y-%m", Transaction.transaction_date).label("period"),
                func.sum(Transaction.amount_base).label("total"),
            )
            .where(Transaction.deleted_at.is_(None))
            .group_by(func.strftime("%Y-%m", Transaction.transaction_date))
            .order_by(func.strftime("%Y-%m", Transaction.transaction_date))
        )
        return [(str(r["period"]), float(r["total"] or 0)) for r in result.mappings().all()]

    def _fit_regression(self, monthly_totals: list[tuple[str, float]]) -> _RegResult:
        """Fit a linear regression over monthly spending data.

        Falls back to a zero-slope average-based result when fewer than 3 data
        points are available.

        Args:
            monthly_totals: Chronologically ordered list of ``(period, total)`` tuples.

        Returns:
            _RegResult with slope, intercept, r², error_std, and next-month prediction.
        """
        n = len(monthly_totals)

        if n == 0:
            return _RegResult(slope=0.0, intercept=0.0, r2=0.0, error_std=0.0, predicted_next=0.0)

        values = [t[1] for t in monthly_totals]
        avg = float(np.mean(values))

        if n < 3:
            return _RegResult(slope=0.0, intercept=avg, r2=0.0, error_std=0.0, predicted_next=avg)

        X = np.array(range(n), dtype=float).reshape(-1, 1)
        y = np.array(values, dtype=float)
        model = LinearRegression().fit(X, y)
        r2 = float(model.score(X, y))
        y_pred = np.array(model.predict(X), dtype=float)
        error_std = float(np.std(y - y_pred))
        slope = float(model.coef_[0])
        intercept = float(model.intercept_)
        predicted_next = max(0.0, slope * n + intercept)

        return _RegResult(
            slope=slope,
            intercept=intercept,
            r2=r2,
            error_std=error_std,
            predicted_next=predicted_next,
        )

    @staticmethod
    def _add_months(period: str, months: int) -> str:
        """Add N months to a YYYY-MM period string.

        Args:
            period: Source period in ``YYYY-MM`` format.
            months: Number of months to add.

        Returns:
            Resulting period string in ``YYYY-MM`` format.
        """
        year, month = int(period[:4]), int(period[5:7])
        total = year * 12 + (month - 1) + months
        return f"{total // 12}-{(total % 12) + 1:02d}"

    @staticmethod
    def _current_period() -> str:
        """Return the current month as a YYYY-MM string."""
        now = datetime.now(UTC)
        return f"{now.year}-{now.month:02d}"
