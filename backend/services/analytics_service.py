from __future__ import annotations

"""Analytics service for KPI computation and spending charts."""

import logging
from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.category import Category
from backend.models.transaction import Transaction
from backend.repositories.income_repository import IncomeRepository
from backend.schemas.analytics import (
    CategorySpending,
    CumulativePoint,
    CumulativeSpendingResponse,
    MetricsResponse,
    SpendingByCategoryResponse,
    SpendingOverTimePoint,
    SpendingOverTimeResponse,
)
from backend.services.income_helpers import monthly_base
from backend.services.inflation_service import InflationService

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Provides spending KPI metrics and chart data.

    Args:
        session: Async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialise with a database session."""
        self.session = session

    async def get_metrics(self) -> MetricsResponse:
        """Compute live KPI metrics.

        Returns:
            MetricsResponse with spending totals, savings rate, and
            inflation-adjusted current-month spending.
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

        return MetricsResponse(
            total_spending_base=total_spending,
            savings_rate=savings_rate,
            inflation_adjusted_spending=inflation_adjusted,
            monthly_income_base=monthly_income,
        )

    async def get_cumulative_spending(self, year: int | None = None) -> CumulativeSpendingResponse:
        """Compute cumulative spending for a calendar year.

        Returns monthly totals and a running cumulative total for every month
        in the requested year that has at least one transaction.

        Args:
            year: Calendar year to aggregate. Defaults to the current year.

        Returns:
            CumulativeSpendingResponse with ordered points and the target year.
        """
        target_year = year if year is not None else datetime.now(UTC).year
        year_prefix = str(target_year)

        result = await self.session.execute(
            select(
                func.strftime("%Y-%m", Transaction.transaction_date).label("period"),
                func.sum(Transaction.amount_base).label("total"),
            )
            .where(
                Transaction.deleted_at.is_(None),
                func.strftime("%Y", Transaction.transaction_date) == year_prefix,
            )
            .group_by(func.strftime("%Y-%m", Transaction.transaction_date))
            .order_by(func.strftime("%Y-%m", Transaction.transaction_date))
        )
        rows = result.mappings().all()

        points: list[CumulativePoint] = []
        running_total = 0.0
        for row in rows:
            monthly = float(row["total"] or 0)
            running_total += monthly
            points.append(
                CumulativePoint(
                    period=str(row["period"]),
                    monthly_total=monthly,
                    cumulative_total=running_total,
                )
            )

        return CumulativeSpendingResponse(points=points, year=target_year)

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
