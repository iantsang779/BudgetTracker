from __future__ import annotations

"""Tests for the voice NLP parser and POST /voice/parse endpoint."""

from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from backend.services.voice_service import parse_transcript

# ── Unit tests: parse_transcript ──────────────────────────────────────────────


def test_basic_usd_with_merchant() -> None:
    """Full transcript: amount + USD + description + merchant."""
    result = parse_transcript("spent 42 dollars on coffee at Starbucks")
    assert result.amount == 42.0
    assert result.currency_code == "USD"
    assert result.description == "coffee"
    assert result.merchant == "Starbucks"
    assert result.confidence >= 0.7


def test_decimal_amount() -> None:
    """Decimal amounts should be parsed correctly."""
    result = parse_transcript("spent 15.50 EUR on lunch at McDonald's")
    assert result.amount == 15.50
    assert result.currency_code == "EUR"
    assert result.merchant == "McDonald's"


def test_no_merchant() -> None:
    """Transcript without a merchant still parses amount and description."""
    result = parse_transcript("spent 20 on groceries")
    assert result.amount == 20.0
    assert result.merchant is None
    assert result.description == "groceries"


def test_no_currency_defaults_none() -> None:
    """When no currency keyword is present, currency_code is None."""
    result = parse_transcript("spent 100 on gas")
    assert result.amount == 100.0
    assert result.currency_code is None


def test_gbp_keyword() -> None:
    """GBP currency keyword maps correctly."""
    result = parse_transcript("spent 30 pounds on dinner at Nando's")
    assert result.currency_code == "GBP"
    assert result.amount == 30.0
    assert result.merchant == "Nando's"


def test_date_today() -> None:
    """'today' should map to today's ISO date."""
    result = parse_transcript("spent 10 on books today")
    assert result.transaction_date == date.today().isoformat()


def test_date_yesterday() -> None:
    """'yesterday' should map to yesterday's ISO date."""
    result = parse_transcript("spent 5 on tea yesterday")
    expected = (date.today() - timedelta(days=1)).isoformat()
    assert result.transaction_date == expected


def test_category_hint_coffee() -> None:
    """'coffee' description maps to 'Eating Out' category hint."""
    result = parse_transcript("spent 4 on coffee")
    assert result.category_hint == "Eating Out"


def test_category_hint_groceries() -> None:
    """'groceries' description maps to 'Groceries' category hint."""
    result = parse_transcript("spent 50 on groceries at Tesco")
    assert result.category_hint == "Groceries"


def test_category_hint_transport() -> None:
    """'uber' merchant maps to 'Transport' category hint."""
    result = parse_transcript("spent 12 on ride at Uber")
    assert result.category_hint == "Transport"


def test_minimal_amount_only() -> None:
    """A near-minimal transcript with just an amount and noun has low-ish confidence."""
    result = parse_transcript("42 coffee")
    assert result.amount == 42.0
    assert result.confidence < 0.7


def test_garbage_input() -> None:
    """Unrecognizable transcript yields near-zero confidence and no fields."""
    result = parse_transcript("hello world goodbye")
    assert result.amount is None
    assert result.confidence < 0.2


def test_large_amount() -> None:
    """Large amounts such as rent are parsed correctly."""
    result = parse_transcript("spent 1500 on rent")
    assert result.amount == 1500.0


def test_raw_transcript_preserved() -> None:
    """raw_transcript always echoes the original input."""
    transcript = "spent 99 on stuff"
    result = parse_transcript(transcript)
    assert result.raw_transcript == transcript


def test_case_insensitive() -> None:
    """Parser is case-insensitive."""
    result = parse_transcript("SPENT 20 DOLLARS ON LUNCH AT SUBWAY")
    assert result.amount == 20.0
    assert result.currency_code == "USD"
    assert result.merchant == "SUBWAY"


def test_extra_whitespace() -> None:
    """Extra whitespace is handled gracefully."""
    result = parse_transcript("  spent  10  on   snacks  ")
    assert result.amount == 10.0
    assert result.description == "snacks"


# ── Integration tests: POST /api/v1/voice/parse ───────────────────────────────


@pytest.mark.asyncio
async def test_endpoint_valid_transcript(client: AsyncClient) -> None:
    """Valid transcript returns 200 with expected JSON shape."""
    resp = await client.post(
        "/api/v1/voice/parse",
        json={"transcript": "spent 42 dollars on coffee at Starbucks"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["amount"] == 42.0
    assert body["currency_code"] == "USD"
    assert "confidence" in body
    assert "raw_transcript" in body


@pytest.mark.asyncio
async def test_endpoint_empty_body(client: AsyncClient) -> None:
    """Missing transcript key returns 422."""
    resp = await client.post("/api/v1/voice/parse", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_endpoint_empty_transcript_string(client: AsyncClient) -> None:
    """Empty transcript string returns 422 (min_length=1 validation)."""
    resp = await client.post("/api/v1/voice/parse", json={"transcript": ""})
    assert resp.status_code == 422
