from __future__ import annotations

"""Account data access layer."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.account import Account
from backend.repositories.base_repository import BaseRepository


class AccountRepository(BaseRepository[Account]):
    """Repository for Account CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with Account model."""
        super().__init__(Account, session)
