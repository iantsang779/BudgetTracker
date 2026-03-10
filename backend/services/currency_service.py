from __future__ import annotations

"""Currency exchange rate service."""

import logging
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.currency_rate import CurrencyRate

logger = logging.getLogger(__name__)

RATE_TTL_HOURS = 24
EXCHANGERATE_API_URL = "https://api.exchangerate-host.com/live"


class CurrencyService:
    """Handles fetching, caching, and converting currency rates.

    Args:
        session: Async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with a database session."""
        self.session = session

    async def get_rate(self, base_code: str, target_code: str) -> float:
        """Get the exchange rate from base to target currency.

        Checks the local cache first. If stale or missing, fetches from API.
        Falls back to 1.0 on errors (for USD-to-USD or API unavailability).

        Args:
            base_code: ISO 4217 source currency code (e.g., "USD").
            target_code: ISO 4217 target currency code (e.g., "EUR").

        Returns:
            Exchange rate as a float.
        """
        if base_code == target_code:
            return 1.0

        # Check cache
        cached = await self._get_cached_rate(base_code, target_code)
        if cached is not None:
            return cached

        # Fetch from API
        rate = await self._fetch_rate(base_code, target_code)
        if rate is not None:
            await self._cache_rate(base_code, target_code, rate)
            return rate

        logger.warning("Could not fetch rate %s->%s, returning 1.0", base_code, target_code)
        return 1.0

    async def convert(self, amount: float, from_code: str, to_code: str) -> tuple[float, float]:
        """Convert an amount from one currency to another.

        Args:
            amount: The amount to convert.
            from_code: Source currency code.
            to_code: Target currency code.

        Returns:
            Tuple of (rate, converted_amount).
        """
        rate = await self.get_rate(from_code, to_code)
        return rate, amount * rate

    async def list_cached_rates(self) -> list[CurrencyRate]:
        """Return all cached currency rates."""
        result = await self.session.execute(
            select(CurrencyRate).order_by(CurrencyRate.fetched_at.desc())
        )
        return list(result.scalars().all())

    async def refresh_rates(self, currencies: list[str] | None = None) -> int:
        """Force-refresh rates for a set of currencies from the API.

        Args:
            currencies: List of target currency codes to refresh (default: common currencies).

        Returns:
            Number of rates successfully refreshed.
        """
        targets = currencies or [
            "EUR",
            "GBP",
            "JPY",
            "CAD",
            "AUD",
            "CHF",
            "CNY",
            "INR",
            "MXN",
            "BRL",
        ]
        count = 0
        for target in targets:
            rate = await self._fetch_rate("USD", target)
            if rate is not None:
                await self._cache_rate("USD", target, rate)
                count += 1
        return count

    async def _get_cached_rate(self, base_code: str, target_code: str) -> float | None:
        """Return a cached rate if it's not stale."""
        cutoff = datetime.now(UTC) - timedelta(hours=RATE_TTL_HOURS)
        result = await self.session.execute(
            select(CurrencyRate)
            .where(
                CurrencyRate.base_code == base_code,
                CurrencyRate.target_code == target_code,
                CurrencyRate.fetched_at >= cutoff,
            )
            .order_by(CurrencyRate.fetched_at.desc())
            .limit(1)
        )
        cached = result.scalar_one_or_none()
        return cached.rate if cached is not None else None

    async def _fetch_rate(self, base_code: str, target_code: str) -> float | None:
        """Fetch a live rate from the exchangerate.host API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    EXCHANGERATE_API_URL,
                    params={"source": base_code, "currencies": target_code},
                )
                resp.raise_for_status()
                data = resp.json()
                key = f"{base_code}{target_code}"
                quotes = data.get("quotes", {})
                if key in quotes:
                    return float(quotes[key])
        except Exception as e:
            logger.warning("Failed to fetch currency rate: %s", e)
        return None

    async def _cache_rate(self, base_code: str, target_code: str, rate: float) -> None:
        """Insert a new rate record into the cache."""
        obj = CurrencyRate(base_code=base_code, target_code=target_code, rate=rate)
        self.session.add(obj)
        await self.session.flush()
