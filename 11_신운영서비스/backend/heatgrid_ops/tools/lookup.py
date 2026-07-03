from __future__ import annotations

import json

import asyncpg


async def load_card(conn: asyncpg.Connection, card_id: int) -> dict[str, object]:
    row = await conn.fetchrow("SELECT * FROM agent_priority_card WHERE card_id = $1", card_id)
    if row is None:
        raise KeyError(card_id)
    card = dict(row)
    features = card.get("features")
    if isinstance(features, str):
        card["features"] = json.loads(features)
    return card


async def recent_timeseries_summary(conn: asyncpg.Connection, substation_id: str) -> str:
    count = await conn.fetchval("SELECT count(*) FROM sensor_readings WHERE substation_id = $1", substation_id)
    latest = await conn.fetchval("SELECT max(ts) FROM sensor_readings WHERE substation_id = $1", substation_id)
    return f"최근 센서 행 {int(count or 0)}건, 최신 시각 {latest}"
