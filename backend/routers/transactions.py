from __future__ import annotations

"""Transactions API router."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.repositories.transaction_repository import TransactionRepository
from backend.routers.analytics import notify_clients
from backend.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate
from backend.services.currency_service import CurrencyService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=list[TransactionRead])
async def list_transactions(
    account_id: int | None = Query(None),
    category_id: int | None = Query(None),
    currency_code: str | None = Query(None),
    source: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[TransactionRead]:
    """List transactions with optional filters."""
    repo = TransactionRepository(db)
    txns = await repo.list_filtered(
        account_id=account_id,
        category_id=category_id,
        currency_code=currency_code,
        source=source,
        date_from=date_from,
        date_to=date_to,
    )
    return [TransactionRead.model_validate(t) for t in txns]


@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
) -> TransactionRead:
    """Create a new transaction.

    amount_base is always computed server-side by converting amount_local from
    currency_code to USD, so clients must not set it.
    """
    _, amount_base = await CurrencyService(db).convert(
        payload.amount_local, payload.currency_code, "USD"
    )
    data = payload.model_dump()
    data["amount_base"] = amount_base
    repo = TransactionRepository(db)
    txn = await repo.create(**data)
    await notify_clients(db)
    return TransactionRead.model_validate(txn)


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
) -> TransactionRead:
    """Fetch a single transaction by ID."""
    repo = TransactionRepository(db)
    txn = await repo.get(transaction_id)
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionRead.model_validate(txn)


@router.patch("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
) -> TransactionRead:
    """Update a transaction.

    If amount_local or currency_code is being changed, amount_base is
    recomputed server-side from the effective (possibly updated) values.
    """
    repo = TransactionRepository(db)
    updates = payload.model_dump(exclude_none=True)
    if "amount_local" in updates or "currency_code" in updates:
        existing = await repo.get(transaction_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        local = updates.get("amount_local", existing.amount_local)
        code = updates.get("currency_code", existing.currency_code)
        _, updates["amount_base"] = await CurrencyService(db).convert(local, code, "USD")
    txn = await repo.update(transaction_id, **updates)
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    await notify_clients(db)
    return TransactionRead.model_validate(txn)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a transaction."""
    repo = TransactionRepository(db)
    deleted = await repo.soft_delete(transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
    await notify_clients(db)
