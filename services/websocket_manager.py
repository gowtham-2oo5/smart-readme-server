"""
WebSocketManager
================
In-memory connection pool for the chat article WebSocket pipeline.

Keeps track of active ``{session_id: WebSocket}`` connections and exposes
helpers to send JSON events.  No Redis or external broker needed for v1.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

log = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections keyed by session_id."""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id] = websocket
        log.info("WS connected: session %s (total: %d)", session_id, len(self._connections))

    def disconnect(self, session_id: str) -> None:
        self._connections.pop(session_id, None)
        log.info("WS disconnected: session %s (remaining: %d)", session_id, len(self._connections))

    # ── Sending ───────────────────────────────────────────────────────────────

    async def send(self, session_id: str, event_type: str, data: Any = None) -> bool:
        """
        Send a typed JSON event to the client identified by ``session_id``.
        Returns ``True`` on success, ``False`` if the connection is gone.
        """
        ws = self._connections.get(session_id)
        if ws is None:
            log.warning("send() called for unknown session %s", session_id)
            return False
        try:
            await ws.send_json({"type": event_type, "data": data})
            return True
        except (WebSocketDisconnect, RuntimeError) as exc:
            log.warning("WS send failed for session %s: %s", session_id, exc)
            self.disconnect(session_id)
            return False

    async def send_progress(self, session_id: str, msg: str) -> None:
        await self.send(session_id, "progress", msg)

    async def send_features(self, session_id: str, features: list[str]) -> None:
        await self.send(session_id, "features_identified", features)

    async def send_question(self, session_id: str, question: str) -> None:
        await self.send(session_id, "question", question)

    async def send_article_chunk(self, session_id: str, chunk: str) -> None:
        await self.send(session_id, "article_chunk", chunk)

    async def send_article_done(self, session_id: str, word_count: int) -> None:
        await self.send(session_id, "article_done", {"word_count": word_count})

    async def send_error(self, session_id: str, msg: str) -> None:
        await self.send(session_id, "error", msg)

    # ── Introspection ─────────────────────────────────────────────────────────

    @property
    def active_count(self) -> int:
        return len(self._connections)

    def is_connected(self, session_id: str) -> bool:
        return session_id in self._connections


# Module-level singleton — import this in main.py
manager = ConnectionManager()
