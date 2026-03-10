from __future__ import annotations

"""Currency Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CurrencyRateRead(BaseModel):
    """Currency rate response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    base_code: str
    target_code: str
    rate: float
    fetched_at: datetime


class ConvertRequest(BaseModel):
    """Currency conversion request."""

    amount: float = Field(gt=0)
    from_code: str
    to_code: str


class ConvertResponse(BaseModel):
    """Currency conversion response."""

    amount: float
    from_code: str
    to_code: str
    rate: float
    converted: float
