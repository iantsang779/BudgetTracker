from __future__ import annotations
"""Accounts API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.repositories.account_repository import AccountRepository
from backend.schemas.account import AccountCreate, AccountRead, AccountUpdate

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/", response_model=list[AccountRead])
async def list_accounts(db: AsyncSession = Depends(get_db)) -> list[AccountRead]:
    """List all accounts."""
    repo = AccountRepository(db)
    accounts = await repo.list()
    return [AccountRead.model_validate(a) for a in accounts]


@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    db: AsyncSession = Depends(get_db),
) -> AccountRead:
    """Create a new account."""
    repo = AccountRepository(db)
    account = await repo.create(**payload.model_dump())
    return AccountRead.model_validate(account)


@router.get("/{account_id}", response_model=AccountRead)
async def get_account(account_id: int, db: AsyncSession = Depends(get_db)) -> AccountRead:
    """Fetch a single account by ID."""
    repo = AccountRepository(db)
    account = await repo.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountRead.model_validate(account)


@router.patch("/{account_id}", response_model=AccountRead)
async def update_account(
    account_id: int,
    payload: AccountUpdate,
    db: AsyncSession = Depends(get_db),
) -> AccountRead:
    """Update an account."""
    repo = AccountRepository(db)
    account = await repo.update(account_id, **payload.model_dump(exclude_none=True))
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountRead.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Soft-delete an account."""
    repo = AccountRepository(db)
    deleted = await repo.soft_delete(account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")
