from __future__ import annotations

"""Currency API router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.currency import ConvertRequest, ConvertResponse, CurrencyRateRead
from backend.services.currency_service import CurrencyService

router = APIRouter(prefix="/currency", tags=["currency"])


@router.get("/rates", response_model=list[CurrencyRateRead])
async def list_rates(db: AsyncSession = Depends(get_db)) -> list[CurrencyRateRead]:
    """List all cached currency rates."""
    svc = CurrencyService(db)
    rates = await svc.list_cached_rates()
    return [CurrencyRateRead.model_validate(r) for r in rates]


@router.post("/rates/refresh", response_model=dict[str, int])
async def refresh_rates(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    """Force-refresh currency rates from the external API."""
    svc = CurrencyService(db)
    count = await svc.refresh_rates()
    return {"refreshed": count}


@router.post("/convert", response_model=ConvertResponse)
async def convert_currency(
    payload: ConvertRequest,
    db: AsyncSession = Depends(get_db),
) -> ConvertResponse:
    """Convert an amount from one currency to another."""
    svc = CurrencyService(db)
    rate, converted = await svc.convert(payload.amount, payload.from_code, payload.to_code)
    return ConvertResponse(
        amount=payload.amount,
        from_code=payload.from_code,
        to_code=payload.to_code,
        rate=rate,
        converted=converted,
    )
