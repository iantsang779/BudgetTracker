from __future__ import annotations

"""Currency exchange rate service."""

import logging
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.currency_rate import CurrencyRate

logger = logging.getLogger(__name__)

RATE_TTL_HOURS = 24
# exchangerate-api.com v6 endpoint — API key embedded in path.
# Returns: {"result": "success", "base_code": "USD", "conversion_rates": {"GBP": 0.79, ...}}
EXCHANGERATE_API_BASE = "https://v6.exchangerate-api.com/v6"


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
        """Return a cached rate if it's not stale.

        Comparison uses a naive UTC cutoff to match the naive datetimes stored
        by SQLite when fetched_at is set as datetime.now(UTC).replace(tzinfo=None).
        """
        cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=RATE_TTL_HOURS)
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
        """Fetch a live rate from the exchangerate-api.com v6 API.

        The API returns: {"result": "success", "base_code": "<base>",
        "conversion_rates": {"<target>": <rate>}}
        API key is embedded in the URL path when EXCHANGERATE_API_KEY is configured.
        """
        if not settings.exchangerate_api_key:
            logger.warning("EXCHANGERATE_API_KEY not set; cannot fetch live rates")
            return None

        url = f"{EXCHANGERATE_API_BASE}/{settings.exchangerate_api_key}/latest/{base_code}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                resp = await http.get(url)
                resp.raise_for_status()
                data = resp.json()
                if data.get("result") != "success":
                    logger.warning(
                        "API error for %s->%s: %s", base_code, target_code, data.get("error-type")
                    )
                    return None
                rates = data.get("conversion_rates", {})
                if target_code in rates:
                    return float(rates[target_code])
                logger.warning(
                    "Rate key %s not found in response for %s->%s",
                    target_code,
                    base_code,
                    target_code,
                )
        except httpx.HTTPError as e:
            logger.warning(
                "HTTP error fetching currency rate %s->%s: %s", base_code, target_code, e
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning("Unexpected response format for %s->%s: %s", base_code, target_code, e)
        return None

    async def _cache_rate(self, base_code: str, target_code: str, rate: float) -> None:
        """Upsert a rate record: remove stale entries then insert the fresh one.

        Using application-set UTC datetime ensures timezone-aware comparisons
        in _get_cached_rate work correctly regardless of DB server_default behaviour.
        """
        await self.session.execute(
            delete(CurrencyRate).where(
                CurrencyRate.base_code == base_code,
                CurrencyRate.target_code == target_code,
            )
        )
        obj = CurrencyRate(
            base_code=base_code,
            target_code=target_code,
            rate=rate,
            fetched_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self.session.add(obj)
        await self.session.flush()
