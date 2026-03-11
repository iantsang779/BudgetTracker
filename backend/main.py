from __future__ import annotations

"""FastAPI application entry point."""

import argparse
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import Base, engine, get_db
from backend.models.category import Category
from backend.routers import accounts, analytics, categories, currency, income, transactions
from backend.websocket_manager import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


_DEFAULT_EXPENSE_CATEGORIES = [
    {"name": "Groceries", "color_hex": "#a6e3a1", "icon": "cart"},
    {"name": "Eating Out", "color_hex": "#fab387", "icon": "utensils"},
    {"name": "Bills & Utilities", "color_hex": "#89b4fa", "icon": "bolt"},
    {"name": "Transport", "color_hex": "#cba6f7", "icon": "car"},
    {"name": "Health & Medical", "color_hex": "#f38ba8", "icon": "heart"},
    {"name": "Entertainment", "color_hex": "#f9e2af", "icon": "film"},
    {"name": "Shopping", "color_hex": "#94e2d5", "icon": "bag"},
    {"name": "Travel", "color_hex": "#89dceb", "icon": "plane"},
    {"name": "Education", "color_hex": "#b4befe", "icon": "book"},
    {"name": "Tax", "color_hex": "#f2cdcd", "icon": "landmark"},
    {"name": "Rent", "color_hex": "#cdd6f4", "icon": "house"},
    {"name": "Investments", "color_hex": "#a6e3a1", "icon": "trending-up"},
    {"name": "Other", "color_hex": "#6c7086", "icon": "tag"},
]


async def _seed_default_categories() -> None:
    """Insert default expense categories if they don't already exist."""
    from sqlalchemy import select

    async for db in get_db():
        result = await db.execute(
            select(Category.name).where(Category.is_income.is_(False), Category.deleted_at.is_(None))
        )
        existing_names = {row[0] for row in result.all()}
        added = 0
        for cat in _DEFAULT_EXPENSE_CATEGORIES:
            if cat["name"] not in existing_names:
                db.add(Category(is_income=False, **cat))
                added += 1
        if added:
            await db.commit()
            logger.info("Seeded %d default expense categories", added)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")
    await _seed_default_categories()
    yield
    await engine.dispose()


app = FastAPI(
    title="BudgetTracker API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(income.router, prefix="/api/v1")
app.include_router(currency.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.websocket("/ws/analytics")
async def websocket_analytics(websocket: WebSocket) -> None:
    """WebSocket endpoint for live analytics updates."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=settings.api_port)
    args = parser.parse_args()
    uvicorn.run("backend.main:app", host="0.0.0.0", port=args.port, reload=settings.debug)
