from __future__ import annotations

"""IncomeEntry ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.account import Account


class IncomeEntry(Base):
    """Recurring or one-off income entry."""

    __tablename__ = "income_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    amount_local: Mapped[float] = mapped_column(Float, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")
    amount_base: Mapped[float] = mapped_column(Float, nullable=False)  # USD
    recurrence: Mapped[str] = mapped_column(  # monthly | yearly | one_off
        String(20), nullable=False, default="monthly"
    )
    description: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    effective_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    account: Mapped[Account] = relationship("Account", back_populates="income_entries")
