from __future__ import annotations
"""Income Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncomeCreate(BaseModel):
    """Fields required to create an income entry."""

    account_id: int
    amount_local: float
    currency_code: str = "USD"
    amount_base: float
    recurrence: str = "monthly"
    description: str = ""
    effective_date: datetime
    end_date: datetime | None = None


class IncomeUpdate(BaseModel):
    """Fields that can be updated on an income entry."""

    amount_local: float | None = None
    currency_code: str | None = None
    amount_base: float | None = None
    recurrence: str | None = None
    description: str | None = None
    effective_date: datetime | None = None
    end_date: datetime | None = None


class IncomeRead(BaseModel):
    """Income entry response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    amount_local: float
    currency_code: str
    amount_base: float
    recurrence: str
    description: str
    effective_date: datetime
    end_date: datetime | None
    created_at: datetime


class IncomeSummary(BaseModel):
    """Aggregated income summary."""

    monthly_total_base: float
    yearly_total_base: float
    active_sources: int
