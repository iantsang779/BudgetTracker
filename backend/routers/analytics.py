from __future__ import annotations

"""Analytics API router."""

import logging
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.analytics import (
    MetricsResponse,
    SavingsProjectionResponse,
    SpendingByCategoryResponse,
    SpendingOverTimeResponse,
)
from backend.services.analytics_service import AnalyticsService
from backend.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def notify_clients(db: AsyncSession) -> None:
    """Recompute metrics and push a live update to all WebSocket clients.

    Errors are logged and swallowed so that write operations are never
    affected by a broadcast failure.

    Args:
        db: The active database session from the calling request.
    """
    try:
        data = await AnalyticsService(db).get_metrics()
        await manager.broadcast({"event": "metrics_updated", "data": data.model_dump()})
    except Exception:
        logger.warning("Failed to broadcast metrics update", exc_info=True)


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(db: AsyncSession = Depends(get_db)) -> MetricsResponse:
    """Return live KPI metrics."""
    return await AnalyticsService(db).get_metrics()


@router.get("/savings-projection", response_model=SavingsProjectionResponse)
async def savings_projection(
    months_ahead: int = 6,
    db: AsyncSession = Depends(get_db),
) -> SavingsProjectionResponse:
    """Return historical spending with a regression-based forward projection."""
    return await AnalyticsService(db).get_savings_projection(months_ahead)


@router.get("/spending-by-category", response_model=SpendingByCategoryResponse)
async def spending_by_category(
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> SpendingByCategoryResponse:
    """Return spending aggregated by category."""
    return await AnalyticsService(db).get_spending_by_category(start_date, end_date)


@router.get("/spending-over-time", response_model=SpendingOverTimeResponse)
async def spending_over_time(db: AsyncSession = Depends(get_db)) -> SpendingOverTimeResponse:
    """Return monthly spending as a timeseries."""
    return await AnalyticsService(db).get_spending_over_time()
