from __future__ import annotations

"""Transaction Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    """Fields required to create a transaction."""

    account_id: int
    category_id: int | None = None
    amount_local: float = Field(gt=0)
    currency_code: str = "GBP"
    amount_base: float = Field(gt=0)
    description: str = ""
    merchant: str = ""
    transaction_date: datetime
    source: Literal["manual", "voice"] = "manual"
    recurrence: Literal["monthly", "yearly"] | None = None
    voice_transcript: str | None = None


class TransactionUpdate(BaseModel):
    """Fields that can be updated on a transaction."""

    category_id: int | None = None
    amount_local: float | None = None
    currency_code: str | None = None
    amount_base: float | None = None
    description: str | None = None
    merchant: str | None = None
    transaction_date: datetime | None = None
    recurrence: Literal["monthly", "yearly"] | None = None


class TransactionRead(BaseModel):
    """Transaction response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    category_id: int | None
    amount_local: float
    currency_code: str
    amount_base: float
    description: str
    merchant: str
    transaction_date: datetime
    source: str
    recurrence: str | None
    voice_transcript: str | None
    created_at: datetime
