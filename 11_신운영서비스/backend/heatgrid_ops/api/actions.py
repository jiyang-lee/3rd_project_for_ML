from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from ..db import get_pool
from ..llm.budget import check_budget, log_call
from ..llm.cache import cache_key, get_cached, put_cached
from ..llm.client import compose_response, max_tokens_for
from ..tools.documents import responsibility_hint
from ..tools.judgment import rule_judgment
from ..tools.lookup import load_card, recent_timeseries_summary
from ..tools.similar_case import similar_cases
from .ws import broadcaster

router = APIRouter(tags=["actions"])
INTENTS = {"explain_priority", "report", "vendor_message", "resident_notice"}


class ActionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    generated_by: str
    cached: bool
    tokens: int


async def gather_evidence(conn, card: dict[str, object], intent: str) -> list[str]:
    substation_id = str(card["substation_id"])
    fault_group = str(card.get("fault_group") or "unknown_review")
    evidence = [
        rule_judgment(card),
        responsibility_hint(fault_group),
        await recent_timeseries_summary(conn, substation_id),
    ]
    if intent in {"explain_priority", "vendor_message", "report"}:
        evidence.extend(await similar_cases(conn, fault_group))
    return evidence


@router.post("/cards/{card_id}/actions/{intent}", response_model=ActionResponse)
async def run_card_action(card_id: int, intent: str) -> ActionResponse:
    if intent not in INTENTS:
        raise HTTPException(status_code=400, detail="unsupported intent")
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            card = await load_card(conn, card_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="card not found") from exc
        card_hash = json.dumps(card, default=str, sort_keys=True, ensure_ascii=False)
        key = cache_key(intent, card_id, card_hash)
        cached = await get_cached(conn, key)
        if cached is not None:
            await log_call(conn, card_id, intent, cached.generated_by, 0, 0, True)
            return ActionResponse(text=cached.text, generated_by=cached.generated_by, cached=True, tokens=0)
        evidence = await gather_evidence(conn, card, intent)
        prompt = json.dumps({"card": card, "evidence": evidence}, default=str, ensure_ascii=False)
        budget = await check_budget(conn, prompt, max_tokens_for(intent))
        result = await compose_response(intent, card, evidence, budget.allowed)
        await put_cached(conn, key, intent, card_id, result.text, result.generated_by)
        await log_call(conn, card_id, intent, result.generated_by, result.prompt_tokens, result.completion_tokens, False)
        if intent in {"report", "vendor_message", "resident_notice"}:
            row = await conn.fetchrow(
                "INSERT INTO action_ticket (card_id, intent, text, generated_by) VALUES ($1, $2, $3, $4) "
                "RETURNING ticket_id, status, created_at",
                card_id,
                intent,
                result.text,
                result.generated_by,
            )
            await broadcaster.publish("ticket", dict(row))
        return ActionResponse(
            text=result.text,
            generated_by=result.generated_by,
            cached=False,
            tokens=result.prompt_tokens + result.completion_tokens,
        )


@router.patch("/tickets/{ticket_id}")
async def patch_ticket(ticket_id: int, status: str) -> dict[str, object]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE action_ticket SET status = $1, updated_at = now() WHERE ticket_id = $2 RETURNING *",
            status,
            ticket_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    return dict(row)
