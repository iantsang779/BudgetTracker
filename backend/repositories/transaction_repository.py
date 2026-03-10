from __future__ import annotations
"""Transaction data access layer."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.transaction import Transaction
from backend.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    """Repository for Transaction CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with Transaction model."""
        super().__init__(Transaction, session)

    async def list_filtered(
        self,
        *,
        account_id: int | None = None,
        category_id: int | None = None,
        currency_code: str | None = None,
        source: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Transaction]:
        """List transactions with optional filters."""
        stmt = select(Transaction).where(Transaction.deleted_at.is_(None))
        if account_id is not None:
            stmt = stmt.where(Transaction.account_id == account_id)
        if category_id is not None:
            stmt = stmt.where(Transaction.category_id == category_id)
        if currency_code is not None:
            stmt = stmt.where(Transaction.currency_code == currency_code)
        if source is not None:
            stmt = stmt.where(Transaction.source == source)
        if date_from is not None:
            stmt = stmt.where(Transaction.transaction_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Transaction.transaction_date <= date_to)
        stmt = stmt.order_by(Transaction.transaction_date.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
