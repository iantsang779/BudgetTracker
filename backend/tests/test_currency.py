from __future__ import annotations

"""Tests for the currency API."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import AsyncClient

# Sentinel API key used in all tests that exercise the HTTP path.
_FAKE_KEY = "test_api_key"
_PATCH_SETTINGS = patch(
    "backend.services.currency_service.settings",
    MagicMock(exchangerate_api_key=_FAKE_KEY),
)


def _mock_http_client(rates: dict[str, float], base: str = "USD") -> MagicMock:
    """Build a mock httpx.AsyncClient context manager that returns a given rates payload."""
    response = MagicMock()
    response.raise_for_status = MagicMock(return_value=None)
    response.json.return_value = {
        "result": "success",
        "base_code": base,
        "conversion_rates": rates,
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    return MagicMock(return_value=mock_client)


@pytest.mark.asyncio
async def test_list_rates_empty(client: AsyncClient) -> None:
    """Listing rates returns an empty list when the cache is empty."""
    response = await client.get("/api/v1/currency/rates")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_convert_same_currency(client: AsyncClient) -> None:
    """Converting USD to USD returns rate=1.0 and the same amount."""
    response = await client.post(
        "/api/v1/currency/convert",
        json={"amount": 100.0, "from_code": "USD", "to_code": "USD"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["converted"] == pytest.approx(100.0)
    assert data["rate"] == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_convert_cross_currency_uses_api(client: AsyncClient) -> None:
    """Cross-currency conversion fetches a live rate and converts correctly.

    e.g. 100 USD at 0.7439 GBP/USD = 74.39 GBP.
    """
    with (
        _PATCH_SETTINGS,
        patch(
            "backend.services.currency_service.httpx.AsyncClient",
            _mock_http_client({"GBP": 0.7439}),
        ),
    ):
        response = await client.post(
            "/api/v1/currency/convert",
            json={"amount": 100.0, "from_code": "USD", "to_code": "GBP"},
        )

    assert response.status_code == 200
    data = response.json()
    print(f"\n[live rate log] USD -> GBP: rate={data['rate']}, 100 USD = {data['converted']} GBP")
    assert data["rate"] == pytest.approx(0.7439)
    assert data["converted"] == pytest.approx(74.39)


@pytest.mark.asyncio
async def test_convert_uses_cached_rate(client: AsyncClient) -> None:
    """Second conversion for the same pair uses the cached rate without calling the API."""
    mock_class = _mock_http_client({"EUR": 0.92})

    with _PATCH_SETTINGS, patch("backend.services.currency_service.httpx.AsyncClient", mock_class):
        await client.post(
            "/api/v1/currency/convert",
            json={"amount": 1.0, "from_code": "USD", "to_code": "EUR"},
        )
        await client.post(
            "/api/v1/currency/convert",
            json={"amount": 50.0, "from_code": "USD", "to_code": "EUR"},
        )

    # The underlying GET should have been called exactly once (cache hit on second call)
    mock_instance = mock_class.return_value
    assert mock_instance.get.call_count == 1


@pytest.mark.asyncio
async def test_convert_api_failure_falls_back_to_one(client: AsyncClient) -> None:
    """When the external API fails, conversion falls back to rate=1.0."""
    failing_client = AsyncMock()
    failing_client.get = AsyncMock(side_effect=httpx.ConnectError("network error"))
    failing_client.__aenter__ = AsyncMock(return_value=failing_client)
    failing_client.__aexit__ = AsyncMock(return_value=None)

    with (
        _PATCH_SETTINGS,
        patch(
            "backend.services.currency_service.httpx.AsyncClient",
            MagicMock(return_value=failing_client),
        ),
    ):
        response = await client.post(
            "/api/v1/currency/convert",
            json={"amount": 100.0, "from_code": "USD", "to_code": "JPY"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["rate"] == pytest.approx(1.0)
    assert data["converted"] == pytest.approx(100.0)


@pytest.mark.asyncio
async def test_refresh_rates_stores_and_returns_count(client: AsyncClient) -> None:
    """POST /rates/refresh calls the API for each currency and returns the count refreshed."""
    with (
        _PATCH_SETTINGS,
        patch(
            "backend.services.currency_service.httpx.AsyncClient",
            _mock_http_client({"EUR": 0.92, "GBP": 0.74, "JPY": 149.5}),
        ),
    ):
        response = await client.post("/api/v1/currency/rates/refresh")

    assert response.status_code == 200
    data = response.json()
    print(f"\n[refresh log] currencies refreshed: {data['refreshed']}")
    assert data["refreshed"] > 0

    rates_resp = await client.get("/api/v1/currency/rates")
    assert rates_resp.status_code == 200
    assert len(rates_resp.json()) > 0
