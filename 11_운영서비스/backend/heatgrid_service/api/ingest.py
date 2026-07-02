from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from ..db import get_pool
from ..features import COMMON10, DHW_OPTIONAL_SIGNALS, system_capability_for_header
from .ws import broadcaster

router = APIRouter(prefix="/api", tags=["ingest"])

SENSOR_COLUMNS = [*COMMON10, *DHW_OPTIONAL_SIGNALS]


class SubstationIn(BaseModel):
    substation_id: str
    manufacturer: str
    raw_id: int
    sensor_columns: list[str]


class ReadingIn(BaseModel):
    substation_id: str
    ts: datetime
    values: dict[str, float | None]


class ReadingsBatch(BaseModel):
    readings: list[ReadingIn]


class ClockIn(BaseModel):
    virtual_time: datetime
    speed_factor: float
    running: bool


@router.post("/ingest/substations")
async def ingest_substations(substations: list[SubstationIn]):
    pool = await get_pool()
    async with pool.acquire() as conn:
        for sub in substations:
            capability = system_capability_for_header(tuple(sub.sensor_columns))
            await conn.execute(
                """
                INSERT INTO substations (substation_id, manufacturer, raw_id, system_capability_group,
                                         common10_ready, sensor_columns, active)
                VALUES ($1, $2, $3, $4, $5, $6, TRUE)
                ON CONFLICT (substation_id) DO UPDATE
                  SET system_capability_group = EXCLUDED.system_capability_group,
                      common10_ready = EXCLUDED.common10_ready,
                      sensor_columns = EXCLUDED.sensor_columns,
                      active = TRUE
                """,
                sub.substation_id,
                sub.manufacturer,
                sub.raw_id,
                capability["system_capability_group"],
                capability["common10_ready"],
                sub.sensor_columns,
            )
    return {"upserted": len(substations)}


@router.post("/ingest/readings")
async def ingest_readings(batch: ReadingsBatch):
    if not batch.readings:
        return {"inserted": 0}
    pool = await get_pool()
    records = []
    for r in batch.readings:
        ts = r.ts if r.ts.tzinfo else r.ts.replace(tzinfo=timezone.utc)
        records.append(
            (
                ts,
                r.substation_id,
                *[r.values.get(col) for col in SENSOR_COLUMNS],
            )
        )
    columns = ["ts", "substation_id", *SENSOR_COLUMNS]
    placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
    sql = (
        f"INSERT INTO sensor_readings ({', '.join(columns)}) "
        f"VALUES ({placeholders}) ON CONFLICT (substation_id, ts) DO NOTHING"
    )
    async with pool.acquire() as conn:
        await conn.executemany(sql, records)
    return {"inserted": len(records)}


@router.post("/replay/clock")
async def replay_clock(clock: ClockIn):
    if clock.virtual_time.tzinfo is None:
        clock.virtual_time = clock.virtual_time.replace(tzinfo=timezone.utc)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE replay_state
               SET virtual_time = $1, speed_factor = $2, running = $3, updated_at = now()
             WHERE id = 1
            """,
            clock.virtual_time,
            clock.speed_factor,
            clock.running,
        )
    await broadcaster.publish(
        "clock",
        {
            "virtual_time": clock.virtual_time,
            "speed_factor": clock.speed_factor,
            "running": clock.running,
        },
    )
    return {"ok": True}
