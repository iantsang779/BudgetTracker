from __future__ import annotations

"""Voice input Pydantic schemas."""

from pydantic import BaseModel, Field


class VoiceParseRequest(BaseModel):
    """Request body for the voice parse endpoint."""

    transcript: str = Field(min_length=1)


class VoiceParseResponse(BaseModel):
    """Structured fields extracted from a voice transcript."""

    amount: float | None = None
    currency_code: str | None = None
    description: str | None = None
    merchant: str | None = None
    transaction_date: str | None = None
    category_hint: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    raw_transcript: str
