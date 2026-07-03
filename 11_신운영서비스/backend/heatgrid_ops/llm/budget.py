from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import asyncpg

from ..config import get_settings


@dataclass(frozen=True)
class BudgetDecision:
    allowed: bool
    used_tokens: int
    budget_tokens: int


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


async def daily_usage(conn: asyncpg.Connection) -> int:
    value = await conn.fetchval(
        "SELECT COALESCE(SUM(prompt_tokens + completion_tokens), 0) FROM llm_call_log WHERE created_at::date = $1",
        date.today(),
    )
    return int(value or 0)


async def check_budget(conn: asyncpg.Connection, prompt: str, max_tokens: int) -> BudgetDecision:
    settings = get_settings()
    used = await daily_usage(conn)
    projected = used + estimate_tokens(prompt) + max_tokens
    return BudgetDecision(
        allowed=projected <= settings.llm_daily_token_budget,
        used_tokens=used,
        budget_tokens=settings.llm_daily_token_budget,
    )


async def log_call(
    conn: asyncpg.Connection,
    card_id: int | None,
    intent: str,
    generated_by: str,
    prompt_tokens: int,
    completion_tokens: int,
    cached: bool,
) -> None:
    sql = (
        "INSERT INTO llm_call_log "
        "(card_id, intent, model, generated_by, prompt_tokens, completion_tokens, estimated_cost_usd, cached) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)"
    )
    await conn.execute(
        sql,
        card_id,
        intent,
        get_settings().openai_model,
        generated_by,
        prompt_tokens,
        completion_tokens,
        0,
        cached,
    )
