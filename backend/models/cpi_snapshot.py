from __future__ import annotations
"""CPISnapshot ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class CpiSnapshot(Base):
    """Monthly Consumer Price Index snapshot."""

    __tablename__ = "cpi_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    country_code: Mapped[str] = mapped_column(String(5), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    cpi_value: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="bls")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
