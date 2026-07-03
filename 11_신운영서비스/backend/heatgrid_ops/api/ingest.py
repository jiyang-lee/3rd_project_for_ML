from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from ..db import get_pool
from ..features import COMMON10, DHW_OPTIONAL_SIGNALS, system_capability_for_header
from ..replay.scenarios import nearest_replay_time, next_replay_time, utc_datetime
from .ws import broadcaster

router = APIRouter(tags=["ingest"])
SENSOR_COLUMNS = [*COMMON10, *DHW_OPTIONAL_SIGNALS]


class SubstationIn(BaseModel):
    model_config = ConfigDict(frozen=True)

    substation_id: str
    manufacturer: str
    raw_id: int
    sensor_columns: list[str]


class ReadingIn(BaseModel):
    model_config = ConfigDict(frozen=True)

    substation_id: str
    ts: datetime
    values: dict[str, float | None]


class ReadingsBatch(BaseModel):
    model_config = ConfigDict(frozen=True)

    readings: list[ReadingIn]


class ClockIn(BaseModel):
    model_config = ConfigDict(frozen=True)

    virtual_time: datetime
    speed_factor: float
    running: bool


class SeekIn(BaseModel):
    model_config = ConfigDict(frozen=True)

    virtual_time: datetime


@router.post("/ingest/substations")
async def ingest_substations(substations: list[SubstationIn]) -> dict[str, int]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        for substation in substations:
            capability = system_capability_for_header(tuple(substation.sensor_columns))
            await conn.execute(
                "INSERT INTO substation "
                "(substation_id, manufacturer, raw_id, system_capability_group, common10_ready, sensor_columns, active) "
                "VALUES ($1, $2, $3, $4, $5, $6, TRUE) "
                "ON CONFLICT (substation_id) DO UPDATE SET "
                "system_capability_group = EXCLUDED.system_capability_group, "
                "common10_ready = EXCLUDED.common10_ready, "
                "sensor_columns = EXCLUDED.sensor_columns, active = TRUE",
                substation.substation_id,
                substation.manufacturer,
                substation.raw_id,
                capability["system_capability_group"],
                capability["common10_ready"],
                substation.sensor_columns,
            )
    return {"upserted": len(substations)}


@router.post("/ingest/readings")
async def ingest_readings(batch: ReadingsBatch) -> dict[str, int]:
    if not batch.readings:
        return {"inserted": 0}
    records = []
    for reading in batch.readings:
        ts = reading.ts if reading.ts.tzinfo else reading.ts.replace(tzinfo=timezone.utc)
        records.append((reading.substation_id, ts, *[reading.values.get(col) for col in SENSOR_COLUMNS]))
    columns = ["substation_id", "ts", *SENSOR_COLUMNS]
    placeholders = ", ".join(f"${index + 1}" for index in range(len(columns)))
    sql = (
        f"INSERT INTO sensor_readings ({', '.join(columns)}) VALUES ({placeholders}) "
        "ON CONFLICT (substation_id, ts) DO NOTHING"
    )
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(sql, records)
    return {"inserted": len(records)}


@router.post("/replay/clock")
async def replay_clock(clock: ClockIn) -> dict[str, bool]:
    virtual_time = clock.virtual_time if clock.virtual_time.tzinfo else clock.virtual_time.replace(tzinfo=timezone.utc)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE replay_state SET virtual_time = $1, speed_factor = $2, running = $3, updated_at = now() WHERE id = 1",
            virtual_time,
            clock.speed_factor,
            clock.running,
        )
    await broadcaster.publish("clock", {"virtual_time": virtual_time, "speed_factor": clock.speed_factor, "running": clock.running})
    return {"ok": True}


@router.post("/replay/start")
async def replay_start() -> dict[str, bool]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        virtual_time = await conn.fetchval("SELECT virtual_time FROM replay_state WHERE id = 1")
        if virtual_time is None:
            first_time = next_replay_time(None)
            if first_time is not None:
                await conn.execute("UPDATE replay_state SET virtual_time = $1, running = TRUE, updated_at = now() WHERE id = 1", first_time)
            else:
                await conn.execute("UPDATE replay_state SET running = TRUE, updated_at = now() WHERE id = 1")
        else:
            await conn.execute("UPDATE replay_state SET running = TRUE, updated_at = now() WHERE id = 1")
    await broadcaster.publish("clock", {"running": True})
    return {"ok": True}


@router.post("/replay/stop")
async def replay_stop() -> dict[str, bool]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE replay_state SET running = FALSE, updated_at = now() WHERE id = 1")
    await broadcaster.publish("clock", {"running": False})
    return {"ok": True}


@router.post("/replay/tick")
async def replay_tick() -> dict[str, object]:
    from ..agent.ops_graph import run_ops_graph

    pool = await get_pool()
    async with pool.acquire() as conn:
        virtual_time = await conn.fetchval("SELECT virtual_time FROM replay_state WHERE id = 1")
        target_time = next_replay_time(virtual_time)
        if target_time is None:
            raise HTTPException(status_code=409, detail="replay scenario source is empty")
        await conn.execute("UPDATE replay_state SET virtual_time = $1, updated_at = now() WHERE id = 1", target_time)
        result = await run_ops_graph(conn, target_time)
        row = await conn.fetchrow("SELECT virtual_time, speed_factor, running, updated_at FROM replay_state WHERE id = 1")
    clock = dict(row) if row else {"virtual_time": target_time}
    await broadcaster.publish("clock", clock)
    return {"ok": True, "virtual_time": target_time, "card_ids": result.card_ids, "node_trace": result.node_trace}


@router.post("/replay/seek")
async def replay_seek(seek: SeekIn) -> dict[str, object]:
    from ..agent.ops_graph import run_ops_graph

    requested_time = utc_datetime(seek.virtual_time)
    target_time = nearest_replay_time(requested_time) or requested_time
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE replay_state SET virtual_time = $1, running = FALSE, updated_at = now() WHERE id = 1",
            target_time,
        )
        result = await run_ops_graph(conn, target_time)
        row = await conn.fetchrow("SELECT virtual_time, speed_factor, running, updated_at FROM replay_state WHERE id = 1")
    clock = dict(row) if row else {"virtual_time": target_time, "running": False}
    await broadcaster.publish("clock", clock)
    return {
        "ok": True,
        "requested_time": requested_time,
        "virtual_time": target_time,
        "card_ids": result.card_ids,
        "node_trace": result.node_trace,
    }
