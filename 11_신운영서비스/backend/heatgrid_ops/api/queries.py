from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
import re

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from ..db import get_pool
from ..llm.budget import check_budget, log_call
from ..llm.client import compose_rag_answer, max_tokens_for
from ..replay.scenarios import available_time_range, build_fault_scenarios

router = APIRouter(tags=["queries"])


class RagChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    context: str | None = Field(default=None, max_length=1000)
    limit: int = Field(default=5, ge=1, le=8)


class RagChatSource(BaseModel):
    chunk_id: int
    title: str
    breadcrumb: str | None
    content: str


class RagChatResponse(BaseModel):
    answer: str
    generated_by: str
    tokens: int
    sources: list[RagChatSource]


class ReplayRangeResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    start: datetime | None
    end: datetime | None
    count: int


class ReplayScenarioResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    scenario_id: str
    label: str
    virtual_time: datetime
    substation_id: str
    priority_tier: str
    fault_group: str
    leadtime_label: str
    priority_score: float | None
    description: str


class ReplayScenariosResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    time_range: ReplayRangeResponse
    scenarios: list[ReplayScenarioResponse]


def row_to_dict(row) -> dict[str, object]:
    value = dict(row)
    for key in ["features", "source_card", "node_trace", "scores"]:
        if isinstance(value.get(key), str):
            value[key] = json.loads(str(value[key]))
    return value


def rag_search_patterns(question: str) -> list[str]:
    terms = re.findall(r"[0-9A-Za-z가-힣_]{2,}", question)
    if not terms and question.strip():
        terms = [question.strip()]
    return [f"%{term}%" for term in terms[:8]]


@router.get("/health")
async def health() -> dict[str, object]:
    from ..config import get_settings

    settings = get_settings()
    return {
        "service": "heatgrid-ops",
        "bootstrapped": settings.runtime_metadata_path.exists() and settings.handoff_agent_card_csv.exists(),
        "db": "configured",
    }


@router.get("/cards/top")
async def top_cards(n: int = Query(default=5, ge=1, le=50)) -> list[dict[str, object]]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        virtual_time = await conn.fetchval("SELECT virtual_time FROM replay_state WHERE id = 1")
        rows = []
        if virtual_time is not None:
            rows = await conn.fetch(
                "SELECT * FROM agent_priority_card WHERE window_end = $1 "
                "ORDER BY priority_score DESC NULLS LAST, substation_id LIMIT $2",
                virtual_time,
                n,
            )
        if not rows and virtual_time is not None:
            rows = await conn.fetch(
                "SELECT * FROM agent_priority_card WHERE window_end <= $1 "
                "ORDER BY window_end DESC, priority_score DESC NULLS LAST LIMIT $2",
                virtual_time,
                n,
            )
        if not rows:
            rows = await conn.fetch(
                "SELECT * FROM agent_priority_card ORDER BY window_end DESC, priority_score DESC NULLS LAST LIMIT $1",
                n,
            )
    return [row_to_dict(row) for row in rows]


@router.get("/cards/{card_id}")
async def card_detail(card_id: int) -> dict[str, object]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM agent_priority_card WHERE card_id = $1", card_id)
    if row is None:
        raise HTTPException(status_code=404, detail="card not found")
    return row_to_dict(row)


@router.get("/tickets")
async def tickets(status: str | None = None) -> list[dict[str, object]]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if status is None:
            rows = await conn.fetch("SELECT * FROM action_ticket ORDER BY created_at DESC LIMIT 100")
        else:
            rows = await conn.fetch("SELECT * FROM action_ticket WHERE status = $1 ORDER BY created_at DESC LIMIT 100", status)
    return [dict(row) for row in rows]


@router.get("/llm/costs/daily")
async def llm_costs_daily() -> dict[str, object]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT COALESCE(SUM(prompt_tokens),0) prompt_tokens, "
            "COALESCE(SUM(completion_tokens),0) completion_tokens, "
            "COALESCE(SUM(estimated_cost_usd),0) estimated_cost_usd, "
            "COUNT(*) calls, COALESCE(SUM(CASE WHEN cached THEN 1 ELSE 0 END),0) cache_hits "
            "FROM llm_call_log WHERE created_at::date = CURRENT_DATE"
        )
    return dict(row)


@router.get("/rag/search")
async def rag_search(q: str, limit: int = Query(default=5, ge=1, le=20)) -> list[dict[str, object]]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT chunk_id, title, breadcrumb, content FROM doc_chunks "
            "WHERE content ILIKE '%' || $1 || '%' ORDER BY chunk_id LIMIT $2",
            q,
            limit,
        )
    return [dict(row) for row in rows]


@router.post("/rag/chat", response_model=RagChatResponse)
async def rag_chat(request: RagChatRequest) -> RagChatResponse:
    patterns = rag_search_patterns(request.question)
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT chunk_id, title, breadcrumb, content FROM doc_chunks "
            "WHERE content ILIKE ANY($1::text[]) "
            "OR title ILIKE ANY($1::text[]) "
            "OR breadcrumb ILIKE ANY($1::text[]) "
            "ORDER BY chunk_id LIMIT $2",
            patterns,
            request.limit,
        )
        sources = [RagChatSource(**dict(row)) for row in rows]
        evidence = [
            f"[{index}] {source.title} / {source.breadcrumb or '문서'}\n{source.content[:1200]}"
            for index, source in enumerate(sources, start=1)
        ]
        prompt = json.dumps({"question": request.question, "context": request.context, "evidence": evidence}, ensure_ascii=False)
        budget = await check_budget(conn, prompt, max_tokens_for("rag_chat"))
        result = await compose_rag_answer(request.question, evidence, budget.allowed, request.context)
        await log_call(
            conn,
            None,
            "rag_chat",
            result.generated_by,
            result.prompt_tokens,
            result.completion_tokens,
            False,
        )
    return RagChatResponse(
        answer=result.text,
        generated_by=result.generated_by,
        tokens=result.prompt_tokens + result.completion_tokens,
        sources=sources,
    )


@router.get("/replay/status")
async def replay_status() -> dict[str, object]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT virtual_time, speed_factor, running, updated_at FROM replay_state WHERE id = 1")
    return dict(row) if row else {}


@router.get("/replay/scenarios", response_model=ReplayScenariosResponse)
async def replay_scenarios() -> ReplayScenariosResponse:
    replay_range = available_time_range()
    scenarios = build_fault_scenarios()
    return ReplayScenariosResponse(
        time_range=ReplayRangeResponse(start=replay_range.start, end=replay_range.end, count=replay_range.count),
        scenarios=[ReplayScenarioResponse(**asdict(scenario)) for scenario in scenarios],
    )


@router.get("/timeseries/{substation_id}")
async def timeseries(substation_id: str, hours: int = Query(default=72, ge=1, le=336)) -> dict[str, object]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        vt = await conn.fetchval("SELECT virtual_time FROM replay_state WHERE id = 1")
        if vt is None:
            return {"signals": [], "rows": []}
        rows = await conn.fetch(
            "SELECT ts, outdoor_temperature, s_hc1_supply_temperature, p_hc1_return_temperature, p_net_meter_flow "
            "FROM sensor_readings WHERE substation_id = $1 AND ts >= $2 - make_interval(hours => $3) "
            "ORDER BY ts",
            substation_id,
            vt,
            hours,
        )
    return {"signals": ["outdoor_temperature", "s_hc1_supply_temperature", "p_hc1_return_temperature", "p_net_meter_flow"], "rows": [dict(row) for row in rows]}
