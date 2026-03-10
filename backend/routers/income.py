from __future__ import annotations

"""Income API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.repositories.income_repository import IncomeRepository
from backend.routers.analytics import notify_clients
from backend.schemas.income import IncomeCreate, IncomeRead, IncomeSummary, IncomeUpdate
from backend.services.income_helpers import monthly_base

router = APIRouter(prefix="/income", tags=["income"])


@router.get("/", response_model=list[IncomeRead])
async def list_income(db: AsyncSession = Depends(get_db)) -> list[IncomeRead]:
    """List all active income entries."""
    repo = IncomeRepository(db)
    entries = await repo.list()
    return [IncomeRead.model_validate(e) for e in entries]


@router.post("/", response_model=IncomeRead, status_code=status.HTTP_201_CREATED)
async def create_income(
    payload: IncomeCreate,
    db: AsyncSession = Depends(get_db),
) -> IncomeRead:
    """Create a new income entry."""
    repo = IncomeRepository(db)
    entry = await repo.create(**payload.model_dump())
    await notify_clients(db)
    return IncomeRead.model_validate(entry)


@router.get("/summary", response_model=IncomeSummary)
async def income_summary(db: AsyncSession = Depends(get_db)) -> IncomeSummary:
    """Return aggregated monthly and yearly income totals."""
    repo = IncomeRepository(db)
    entries = await repo.list_active()
    monthly = sum(monthly_base(e.amount_base, e.recurrence) for e in entries)
    one_offs = sum(e.amount_base for e in entries if e.recurrence == "one_off")
    return IncomeSummary(
        monthly_total_base=monthly,
        yearly_total_base=monthly * 12 + one_offs,
        active_sources=len(entries),
    )


@router.get("/{income_id}", response_model=IncomeRead)
async def get_income(income_id: int, db: AsyncSession = Depends(get_db)) -> IncomeRead:
    """Fetch a single income entry by ID."""
    repo = IncomeRepository(db)
    entry = await repo.get(income_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Income entry not found")
    return IncomeRead.model_validate(entry)


@router.patch("/{income_id}", response_model=IncomeRead)
async def update_income(
    income_id: int,
    payload: IncomeUpdate,
    db: AsyncSession = Depends(get_db),
) -> IncomeRead:
    """Update an income entry."""
    repo = IncomeRepository(db)
    entry = await repo.update(income_id, **payload.model_dump(exclude_none=True))
    if entry is None:
        raise HTTPException(status_code=404, detail="Income entry not found")
    await notify_clients(db)
    return IncomeRead.model_validate(entry)


@router.delete("/{income_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def delete_income(income_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Soft-delete an income entry."""
    repo = IncomeRepository(db)
    deleted = await repo.soft_delete(income_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Income entry not found")
    await notify_clients(db)
