# Backend Domain — Code Templates

## Model — `backend/models/{domain}.py`

```python
from __future__ import annotations

"""SQLAlchemy ORM model for {Domain}."""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)
```

Rules:
- Use `Mapped[T]` and `mapped_column()` — never legacy `Column()`
- Soft deletes via `deleted_at: Mapped[datetime | None]`
- Monetary amounts: `amount_local: Mapped[float]` + `amount_base: Mapped[float]` (USD)
- Add to `backend/models/__init__.py` so SQLAlchemy's `create_all` sees it

---

## Schema — `backend/schemas/{domain}.py`

```python
from __future__ import annotations

"""Pydantic v2 schemas for {Domain}."""

from pydantic import BaseModel, ConfigDict


class DomainCreate(BaseModel):
    name: str
    # NOTE: amount_base is NEVER in Create — computed server-side
    # Give server-computed fields a default so Pydantic doesn't 422:
    # amount_base: float = 0.0


class DomainUpdate(BaseModel):
    name: str | None = None


class DomainRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # required for SQLAlchemy → Pydantic

    id: int
    name: str
    deleted_at: str | None = None
```

Rules:
- `from_attributes=True` **only** on `Read` models
- Use `X | None` not `Optional[X]`
- `amount_base` is server-computed — never expose in Create/Update

---

## Repository — `backend/repositories/{domain}_repository.py`

```python
from __future__ import annotations

"""Data access for {Domain}. No business logic here."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.domain import Domain
from backend.repositories.base_repository import BaseRepository


class DomainRepository(BaseRepository[Domain]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Domain, db)
```

`BaseRepository` provides: `get(id)`, `list()`, `create(**kwargs)`, `update(id, **kwargs)`, `soft_delete(id)`.
Add custom query methods (`list_filtered`, `list_active`) only when base methods are insufficient.

---

## Router — `backend/routers/{domain}.py`

```python
from __future__ import annotations

"""FastAPI router for {Domain}."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.repositories.domain_repository import DomainRepository
from backend.routers.analytics import notify_clients
from backend.schemas.domain import DomainCreate, DomainRead, DomainUpdate

router = APIRouter(prefix="/domains", tags=["domains"])


@router.get("/", response_model=list[DomainRead])
async def list_domains(db: AsyncSession = Depends(get_db)) -> list[DomainRead]:
    """List all active domains."""
    repo = DomainRepository(db)
    items = await repo.list()
    return [DomainRead.model_validate(i) for i in items]


@router.post("/", response_model=DomainRead, status_code=status.HTTP_201_CREATED)
async def create_domain(
    payload: DomainCreate, db: AsyncSession = Depends(get_db)
) -> DomainRead:
    """Create a domain."""
    repo = DomainRepository(db)
    item = await repo.create(**payload.model_dump())
    await notify_clients(db)  # omit if domain doesn't affect metrics
    return DomainRead.model_validate(item)


@router.get("/{id}", response_model=DomainRead)
async def get_domain(id: int, db: AsyncSession = Depends(get_db)) -> DomainRead:
    """Get domain by ID."""
    repo = DomainRepository(db)
    item = await repo.get(id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return DomainRead.model_validate(item)


@router.patch("/{id}", response_model=DomainRead)
async def update_domain(
    id: int, payload: DomainUpdate, db: AsyncSession = Depends(get_db)
) -> DomainRead:
    """Update a domain."""
    repo = DomainRepository(db)
    item = await repo.update(id, **payload.model_dump(exclude_unset=True))
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return DomainRead.model_validate(item)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_domain(id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Soft-delete a domain."""
    repo = DomainRepository(db)
    await repo.soft_delete(id)
```

---

## Register in `backend/main.py`

```python
from backend.routers import domain
app.include_router(domain.router, prefix="/api/v1")
```

---

## Tests — `backend/tests/test_{domain}.py`

```python
from __future__ import annotations

"""Tests for the {domain} API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_domain(client: AsyncClient) -> None:
    """Create returns 201 with correct fields."""
    resp = await client.post("/api/v1/domains/", json={"name": "Test"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Test"


@pytest.mark.asyncio
async def test_list_domains(client: AsyncClient) -> None:
    """List returns all created domains."""
    await client.post("/api/v1/domains/", json={"name": "A"})
    await client.post("/api/v1/domains/", json={"name": "B"})
    resp = await client.get("/api/v1/domains/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_get_domain_not_found(client: AsyncClient) -> None:
    """Returns 404 for missing domain."""
    resp = await client.get("/api/v1/domains/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_domain(client: AsyncClient) -> None:
    """Patch updates only supplied fields."""
    create = await client.post("/api/v1/domains/", json={"name": "Old"})
    id_ = create.json()["id"]
    resp = await client.patch(f"/api/v1/domains/{id_}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


@pytest.mark.asyncio
async def test_delete_domain(client: AsyncClient) -> None:
    """Delete soft-deletes (item gone from list)."""
    create = await client.post("/api/v1/domains/", json={"name": "ToDelete"})
    id_ = create.json()["id"]
    assert (await client.delete(f"/api/v1/domains/{id_}")).status_code == 204
```

Test fixture is in `backend/tests/conftest.py` — in-memory SQLite, `AsyncClient`, dependency override for `get_db`.
