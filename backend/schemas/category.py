from __future__ import annotations

"""Category Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryCreate(BaseModel):
    """Fields required to create a category."""

    name: str
    color_hex: str = "#6366f1"
    icon: str = "tag"
    is_income: bool = False


class CategoryUpdate(BaseModel):
    """Fields that can be updated on a category."""

    name: str | None = None
    color_hex: str | None = None
    icon: str | None = None
    is_income: bool | None = None


class CategoryRead(BaseModel):
    """Category response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color_hex: str
    icon: str
    is_income: bool
    created_at: datetime
