from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json

import asyncpg

from ..scheduler import run_tick
from .prompts import OPS_GRAPH_ORDER


@dataclass(frozen=True)
class OpsGraphResult:
    card_ids: list[int]
    node_trace: dict[str, object]


async def run_ops_graph(conn: asyncpg.Connection, virtual_time: datetime) -> OpsGraphResult:
    card_ids = await run_tick(conn, virtual_time)
    trace = {name: {"status": "ok"} for name in OPS_GRAPH_ORDER}
    trace["record"] = {"status": "ok", "card_ids": card_ids, "llm_calls": 0}
    await conn.execute(
        "INSERT INTO agent_runs (trigger_card_ids, status, node_trace) VALUES ($1, $2, $3)",
        card_ids,
        "completed",
        json.dumps(trace, ensure_ascii=False),
    )
    return OpsGraphResult(card_ids=card_ids, node_trace=trace)
