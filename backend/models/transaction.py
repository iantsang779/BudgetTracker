from __future__ import annotations
"""Transaction ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.account import Account
    from backend.models.category import Category


class Transaction(Base):
    """A single financial transaction (expense or income record)."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    amount_local: Mapped[float] = mapped_column(Float, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    amount_base: Mapped[float] = mapped_column(Float, nullable=False)  # USD
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    merchant: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    transaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")  # manual | voice
    voice_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    account: Mapped[Account] = relationship("Account", back_populates="transactions")
    category: Mapped[Category | None] = relationship("Category", back_populates="transactions")
