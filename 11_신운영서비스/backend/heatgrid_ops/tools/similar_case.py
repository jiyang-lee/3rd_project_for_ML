from __future__ import annotations

import asyncpg


async def similar_cases(conn: asyncpg.Connection, fault_group: str, limit: int = 3) -> list[str]:
    sql = (
        "SELECT source_row FROM official_card_reference "
        "WHERE source_row ->> 'm1_specialist_fault_group' = $1 "
        "ORDER BY priority_score DESC NULLS LAST LIMIT $2"
    )
    rows = await conn.fetch(
        sql,
        fault_group,
        limit,
    )
    cases: list[str] = []
    for row in rows:
        payload = dict(row["source_row"])
        cases.append(
            f"{payload.get('manufacturer')} #{payload.get('substation_id')} "
            f"{payload.get('priority_level')} score={payload.get('priority_score')}"
        )
    return cases
