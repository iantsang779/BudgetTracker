from __future__ import annotations

"""Inflation adjustment service using CPI data."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.cpi_snapshot import CpiSnapshot

logger = logging.getLogger(__name__)

FALLBACK_JSON_PATH = Path(__file__).parent.parent / "data" / "cpi_fallback.json"
BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
BLS_SERIES_CPI_U = "CUUR0000SA0"  # CPI-U, All items, US city average


class InflationService:
    """Provides CPI-based inflation adjustments and projections.

    Args:
        session: Async database session.
        annual_inflation_override: Optional manual inflation rate override (0.035 = 3.5%).
    """

    def __init__(
        self, session: AsyncSession, annual_inflation_override: float | None = None
    ) -> None:
        """Initialize with a database session and optional rate override."""
        self.session = session
        self._override = annual_inflation_override

    async def get_annual_rate(self) -> float:
        """Return the best available annual inflation rate.

        Priority: user override → trailing 12-month CPI CAGR → hardcoded 3.5%.

        Returns:
            Annual inflation rate as a decimal (e.g., 0.035 for 3.5%).
        """
        if self._override is not None:
            return self._override

        rate = await self._compute_trailing_cagr()
        if rate is not None:
            return rate

        return 0.035  # fallback

    async def adjust_for_inflation(self, nominal: float, years: float) -> float:
        """Convert a nominal amount to today's real dollars.

        Args:
            nominal: Amount in nominal dollars.
            years: Number of years to adjust for.

        Returns:
            Inflation-adjusted (real) value.
        """
        rate = await self.get_annual_rate()
        return float(nominal / ((1 + rate) ** years))

    async def project_inflation_adjusted(self, nominal: float, future_years: float) -> float:
        """Project a nominal value forward accounting for inflation.

        Args:
            nominal: Current nominal amount.
            future_years: Years into the future.

        Returns:
            Future value in real dollars.
        """
        rate = await self.get_annual_rate()
        return float(nominal * ((1 + rate) ** future_years))

    async def ensure_cpi_loaded(self) -> int:
        """Load CPI data from fallback JSON if the DB has no snapshots.

        Returns:
            Number of records loaded (0 if already populated).
        """
        result = await self.session.execute(select(CpiSnapshot).limit(1))
        if result.scalar_one_or_none() is not None:
            return 0

        data = json.loads(FALLBACK_JSON_PATH.read_text())
        count = 0
        for entry in data["data"]:
            snap = CpiSnapshot(
                country_code=data["country_code"],
                period=entry["period"],
                cpi_value=entry["cpi_value"],
                source=data["source"],
            )
            self.session.add(snap)
            count += 1
        await self.session.flush()
        logger.info("Loaded %d CPI fallback records", count)
        return count

    async def fetch_latest_bls(self, api_key: str = "") -> int:
        """Fetch the latest CPI data from the BLS API.

        Args:
            api_key: Optional BLS API key for higher rate limits.

        Returns:
            Number of new records inserted.
        """
        payload: dict[str, object] = {
            "seriesid": [BLS_SERIES_CPI_U],
            "startyear": str(datetime.now(UTC).year - 2),
            "endyear": str(datetime.now(UTC).year),
        }
        if api_key:
            payload["registrationkey"] = api_key

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(BLS_API_URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning("BLS API fetch failed: %s", e)
            return 0

        series = data.get("Results", {}).get("series", [])
        if not series:
            return 0

        count = 0
        for item in series[0].get("data", []):
            period_str = f"{item['year']}-{item['period'].replace('M', '').zfill(2)}"
            # Check for existing record
            exists = await self.session.execute(
                select(CpiSnapshot).where(
                    CpiSnapshot.country_code == "US",
                    CpiSnapshot.period == period_str,
                )
            )
            if exists.scalar_one_or_none() is not None:
                continue
            snap = CpiSnapshot(
                country_code="US",
                period=period_str,
                cpi_value=float(item["value"]),
                source="bls",
            )
            self.session.add(snap)
            count += 1
        await self.session.flush()
        return count

    async def _compute_trailing_cagr(self) -> float | None:
        """Compute the trailing 12-month CPI compound annual growth rate."""
        result = await self.session.execute(
            select(CpiSnapshot)
            .where(CpiSnapshot.country_code == "US")
            .order_by(CpiSnapshot.period.desc())
            .limit(13)
        )
        snapshots = list(result.scalars().all())
        if len(snapshots) < 13:
            return None
        latest = snapshots[0].cpi_value
        year_ago = snapshots[12].cpi_value
        if year_ago == 0:
            return None
        return (latest / year_ago) - 1
