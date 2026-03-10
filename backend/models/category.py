from __future__ import annotations
"""Category ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.transaction import Transaction


class Category(Base):
    """Expense/income category."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False, default="#6366f1")
    icon: Mapped[str] = mapped_column(String(50), nullable=False, default="tag")
    is_income: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    transactions: Mapped[list[Transaction]] = relationship("Transaction", back_populates="category")
