from __future__ import annotations
"""Account ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.income import IncomeEntry
    from backend.models.transaction import Transaction


class Account(Base):
    """Financial account (bank, cash, credit card, etc.)."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    balance_initial: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    transactions: Mapped[list[Transaction]] = relationship("Transaction", back_populates="account")
    income_entries: Mapped[list[IncomeEntry]] = relationship("IncomeEntry", back_populates="account")
