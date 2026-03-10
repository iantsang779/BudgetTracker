from __future__ import annotations
"""FastAPI application entry point."""

import argparse
import asyncio
import logging
import uvicorn

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import engine, Base
from backend.routers import accounts, categories, transactions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for live analytics updates."""

    def __init__(self) -> None:
        """Initialize with empty connection pool."""
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        self._connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:  # type: ignore[type-arg]
        """Send a message to all connected clients."""
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.remove(ws)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")
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
