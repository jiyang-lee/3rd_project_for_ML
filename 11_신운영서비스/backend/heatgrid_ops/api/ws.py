from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from fastapi import WebSocket


def json_default(value: object) -> str | int | float | bool | None:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if value is None or isinstance(value, str | int | float | bool):
        return value
    return str(value)


@dataclass
class Broadcaster:
    sockets: set[WebSocket] = field(default_factory=set)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.sockets.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.sockets.discard(websocket)

    async def publish(self, event_type: str, payload: dict[str, object]) -> None:
        message = json.dumps({"type": event_type, "payload": payload}, ensure_ascii=False, default=json_default)
        stale: list[WebSocket] = []
        for websocket in self.sockets:
            try:
                await websocket.send_text(message)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)


broadcaster = Broadcaster()
