from __future__ import annotations

"""WebSocket connection manager for live analytics broadcasts."""

import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts JSON messages.

    Connections are stored in memory. Dead connections are pruned automatically
    on the next broadcast.
    """

    def __init__(self) -> None:
        """Initialize with an empty connection pool."""
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: The incoming WebSocket connection.
        """
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the pool.

        Args:
            websocket: The connection to remove.
        """
        self._connections.remove(websocket)

    async def broadcast(self, message: dict[str, object]) -> None:
        """Send a JSON message to all connected clients.

        Dead connections are silently removed.

        Args:
            message: JSON-serialisable payload to broadcast.
        """
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.remove(ws)


manager = ConnectionManager()
