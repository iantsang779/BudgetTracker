from __future__ import annotations
"""Generic base repository with CRUD operations."""

from typing import Any, Generic, TypeVar

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic async CRUD repository.

    Args:
        model: The SQLAlchemy model class.
        session: The async database session.
    """

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        """Initialize the repository."""
        self.model = model
        self.session = session

    async def get(self, id: int) -> ModelT | None:
        """Fetch a single record by primary key."""
        result = await self.session.execute(
            select(self.model).where(
                self.model.id == id,  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
        )
        return result.scalar_one_or_none()

    async def list(self, **filters: Any) -> list[ModelT]:
        """List all non-deleted records, optionally filtered."""
        stmt = select(self.model).where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]
        for attr, value in filters.items():
            stmt = stmt.where(getattr(self.model, attr) == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **data: Any) -> ModelT:
        """Insert a new record."""
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: int, **data: Any) -> ModelT | None:
        """Update fields on an existing record."""
        await self.session.execute(
            update(self.model)
            .where(self.model.id == id)  # type: ignore[attr-defined]
            .values(**{k: v for k, v in data.items() if v is not None})
        )
        return await self.get(id)

    async def soft_delete(self, id: int) -> bool:
        """Soft-delete a record by setting deleted_at."""
        from datetime import datetime, timezone

        result = await self.session.execute(
            update(self.model)
            .where(self.model.id == id)  # type: ignore[attr-defined]
            .values(deleted_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0
