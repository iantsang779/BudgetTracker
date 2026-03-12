from __future__ import annotations

"""Live integration test for the exchangerate-api.com API key.

Run with:
    pytest backend/tests/test_currency_live.py -v -m integration

Requires EXCHANGERATE_API_KEY to be set in .env at the project root.
Raises exceptions (not soft failures) if the key is missing or the API call fails.
"""

import httpx
import pytest

from backend.config import settings
from backend.services.currency_service import EXCHANGERATE_API_BASE


@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_key_is_configured() -> None:
    """Raise if EXCHANGERATE_API_KEY is not set in .env."""
    if not settings.exchangerate_api_key:
        raise OSError(
            "EXCHANGERATE_API_KEY is not set. "
            "Add it to .env at the project root before running live tests."
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_api_call_succeeds() -> None:
    """Make a real HTTP request to exchangerate-api.com and assert it succeeds.

    Raises:
        EnvironmentError: if the API key is missing.
        AssertionError: if the API returns a non-success result or is missing expected fields.
        httpx.HTTPStatusError: if the HTTP response is a 4xx/5xx error.
    """
    if not settings.exchangerate_api_key:
        raise OSError("EXCHANGERATE_API_KEY is not set in .env — cannot run live API test.")

    url = f"{EXCHANGERATE_API_BASE}/{settings.exchangerate_api_key}/latest/USD"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)

    response.raise_for_status()  # raises httpx.HTTPStatusError on 4xx/5xx

    data = response.json()

    assert data.get("result") == "success", (
        f"API returned non-success result: {data.get('result')!r}. "
        f"Error type: {data.get('error-type')!r}. "
        "Check your API key is valid and not expired."
    )
    assert "conversion_rates" in data, "Response missing 'conversion_rates' field."
    assert "GBP" in data["conversion_rates"], "GBP not found in conversion rates."
    assert isinstance(data["conversion_rates"]["GBP"], float), "GBP rate is not a float."


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_gbp_rate_is_plausible() -> None:
    """Assert the live USD->GBP rate is within a plausible range (0.5 – 1.2).

    This catches cases where the API returns obviously wrong values.
    """
    if not settings.exchangerate_api_key:
        raise OSError("EXCHANGERATE_API_KEY is not set in .env — cannot run live API test.")

    url = f"{EXCHANGERATE_API_BASE}/{settings.exchangerate_api_key}/latest/USD"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)

    response.raise_for_status()
    data = response.json()

    gbp_rate = data["conversion_rates"]["GBP"]
    assert 0.5 <= gbp_rate <= 1.2, (
        f"USD->GBP rate {gbp_rate} is outside the expected range [0.5, 1.2]. "
        "Either the API returned bad data or the key is invalid."
    )
