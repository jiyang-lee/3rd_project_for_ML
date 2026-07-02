from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..db import get_pool

router = APIRouter(prefix="/api", tags=["queries"])


def _row_to_dict(row) -> dict:
    d = dict(row)
    if "features" in d and isinstance(d["features"], str):
        d["features"] = json.loads(d["features"])
    return d


@router.get("/health")
async def health():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    from ..models_registry import load_registry

    registry = load_registry()
    return {"db": "ok", "models_loaded": registry.loaded}


@router.get("/replay/status")
async def replay_status():
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT virtual_time, speed_factor, running, updated_at FROM replay_state WHERE id = 1")
    return dict(row) if row else {}


@router.get("/substations")
async def list_substations():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT s.substation_id, s.manufacturer, s.raw_id, s.system_capability_group,
                   s.common10_ready, s.active,
                   c.primary_state, c.priority_tier, c.risk_probability, c.pre_event_detected,
                   c.review_flag, c.window_end AS last_window_end, c.card_id AS last_card_id
              FROM substations s
              LEFT JOIN LATERAL (
                SELECT * FROM state_cards c
                 WHERE c.substation_id = s.substation_id
                 ORDER BY c.window_end DESC LIMIT 1
              ) c ON TRUE
             WHERE s.active
             ORDER BY s.substation_id
            """
        )
    return [dict(r) for r in rows]


@router.get("/substations/{substation_id}/readings")
async def substation_readings(
    substation_id: str,
    hours: int = Query(default=168, le=24 * 14),
    signals: str = Query(default="s_hc1_supply_temperature,p_hc1_return_temperature,p_net_meter_flow,outdoor_temperature"),
):
    requested = [s.strip() for s in signals.split(",") if s.strip()]
    allowed = {
        "outdoor_temperature", "s_hc1_supply_temperature", "s_hc1_supply_temperature_setpoint",
        "p_hc1_return_temperature", "p_net_meter_energy", "p_net_meter_volume",
        "p_net_meter_heat_power", "p_net_meter_flow", "p_net_supply_temperature",
        "p_net_return_temperature", "s_dhw_supply_temperature", "s_dhw_supply_temperature_setpoint",
        "s_dhw_upper_storage_temperature", "s_dhw_lower_storage_temperature",
        "p_dhw_return_temperature", "p_dhw_return_temperature_setpoint",
    }
    cols = [s for s in requested if s in allowed]
    if not cols:
        raise HTTPException(400, "no valid signals requested")
    pool = await get_pool()
    async with pool.acquire() as conn:
        vt = await conn.fetchval("SELECT virtual_time FROM replay_state WHERE id = 1")
        if vt is None:
            return {"signals": cols, "rows": []}
        rows = await conn.fetch(
            f"""
            SELECT ts, {', '.join(cols)}
              FROM sensor_readings
             WHERE substation_id = $1 AND ts >= $2 - make_interval(hours => $3) AND ts <= $2
             ORDER BY ts
            """,
            substation_id,
            vt,
            hours,
        )
    return {"signals": cols, "rows": [dict(r) for r in rows]}


@router.get("/substations/{substation_id}/state-cards")
async def substation_state_cards(substation_id: str, limit: int = Query(default=50, le=500)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM state_cards WHERE substation_id = $1 ORDER BY window_end DESC LIMIT $2",
            substation_id,
            limit,
        )
    return [_row_to_dict(r) for r in rows]


@router.get("/state-cards/latest")
async def latest_state_cards():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT ON (substation_id) *
              FROM state_cards
             ORDER BY substation_id, window_end DESC
            """
        )
    return [_row_to_dict(r) for r in rows]


@router.get("/state-cards/{card_id}")
async def state_card_detail(card_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM state_cards WHERE card_id = $1", card_id)
    if row is None:
        raise HTTPException(404, "state card not found")
    return _row_to_dict(row)


@router.get("/dispatch-orders")
async def dispatch_orders(status: str | None = None, limit: int = Query(default=50, le=500)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if status:
            rows = await conn.fetch(
                "SELECT * FROM dispatch_orders WHERE status = $1 ORDER BY created_at DESC LIMIT $2",
                status,
                limit,
            )
        else:
            rows = await conn.fetch("SELECT * FROM dispatch_orders ORDER BY created_at DESC LIMIT $1", limit)
    return [dict(r) for r in rows]


class OrderPatch(BaseModel):
    status: str


@router.patch("/dispatch-orders/{order_id}")
async def patch_order(order_id: int, patch: OrderPatch):
    if patch.status not in {"draft", "acknowledged", "closed"}:
        raise HTTPException(400, "invalid status")
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE dispatch_orders SET status = $1 WHERE order_id = $2 RETURNING *",
            patch.status,
            order_id,
        )
    if row is None:
        raise HTTPException(404, "order not found")
    return dict(row)


@router.get("/agent-runs")
async def agent_runs(limit: int = Query(default=20, le=200)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM agent_runs ORDER BY started_at DESC LIMIT $1", limit)
    out = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("node_trace"), str):
            d["node_trace"] = json.loads(d["node_trace"])
        out.append(d)
    return out
