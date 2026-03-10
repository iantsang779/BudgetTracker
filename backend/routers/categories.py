from __future__ import annotations

"""Categories API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.repositories.category_repository import CategoryRepository
from backend.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryRead])
async def list_categories(
    is_income: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[CategoryRead]:
    """List categories, optionally filtered by type."""
    repo = CategoryRepository(db)
    if is_income is not None:
        categories = await repo.list_by_type(is_income)
    else:
        categories = await repo.list()
    return [CategoryRead.model_validate(c) for c in categories]


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
) -> CategoryRead:
    """Create a new category."""
    repo = CategoryRepository(db)
    category = await repo.create(**payload.model_dump())
    return CategoryRead.model_validate(category)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)) -> CategoryRead:
    """Fetch a single category by ID."""
    repo = CategoryRepository(db)
    category = await repo.get(category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryRead.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
) -> CategoryRead:
    """Update a category."""
    repo = CategoryRepository(db)
    category = await repo.update(category_id, **payload.model_dump(exclude_none=True))
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryRead.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Soft-delete a category."""
    repo = CategoryRepository(db)
    deleted = await repo.soft_delete(category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
