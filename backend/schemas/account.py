from __future__ import annotations

"""Account Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    """Fields required to create an account."""

    name: str
    currency_code: str = "GBP"
    balance_initial: float = Field(default=0.0, ge=0)


class AccountUpdate(BaseModel):
    """Fields that can be updated on an account."""

    name: str | None = None
    currency_code: str | None = None
    balance_initial: float | None = None


class AccountRead(BaseModel):
    """Account response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    currency_code: str
    balance_initial: float
    created_at: datetime
