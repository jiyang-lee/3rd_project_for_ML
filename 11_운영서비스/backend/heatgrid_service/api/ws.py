"""인프로세스 WebSocket 브로드캐스터 — 단일 프로세스라 외부 브로커 불필요."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket


def _json_default(obj: Any):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


class Broadcaster:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)

    async def publish(self, event_type: str, payload: dict) -> None:
        message = json.dumps({"type": event_type, "payload": payload}, default=_json_default)
        async with self._lock:
            clients = list(self._clients)
        for ws in clients:
            try:
                await ws.send_text(message)
            except Exception:
                await self.disconnect(ws)


broadcaster = Broadcaster()
