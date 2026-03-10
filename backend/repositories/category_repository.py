from __future__ import annotations
"""Category data access layer."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.category import Category
from backend.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository for Category CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with Category model."""
        super().__init__(Category, session)

    async def list_by_type(self, is_income: bool) -> list[Category]:
        """List categories filtered by income/expense type."""
        result = await self.session.execute(
            select(Category).where(
                Category.deleted_at.is_(None),
                Category.is_income == is_income,
            )
        )
        return list(result.scalars().all())
