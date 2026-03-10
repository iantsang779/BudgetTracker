from __future__ import annotations

"""CurrencyRate ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class CurrencyRate(Base):
    """Cached currency exchange rate."""

    __tablename__ = "currency_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    base_code: Mapped[str] = mapped_column(String(3), nullable=False)
    target_code: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
