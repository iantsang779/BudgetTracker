from __future__ import annotations

"""Income data access layer."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.income import IncomeEntry
from backend.repositories.base_repository import BaseRepository


class IncomeRepository(BaseRepository[IncomeEntry]):
    """Repository for IncomeEntry CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with IncomeEntry model."""
        super().__init__(IncomeEntry, session)

    async def list_active(self, as_of: datetime | None = None) -> list[IncomeEntry]:
        """List active income entries (not ended, not deleted)."""
        ref = as_of or datetime.utcnow()
        stmt = select(IncomeEntry).where(
            IncomeEntry.deleted_at.is_(None),
            IncomeEntry.effective_date <= ref,
            (IncomeEntry.end_date.is_(None)) | (IncomeEntry.end_date >= ref),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
