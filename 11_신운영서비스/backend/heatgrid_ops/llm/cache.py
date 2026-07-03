from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import asyncpg

from ..config import get_settings


@dataclass(frozen=True)
class CachedResponse:
    text: str
    generated_by: str


def cache_key(intent: str, card_id: int, card_hash: str) -> str:
    raw = f"{intent}:{card_id}:{card_hash}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


async def get_cached(conn: asyncpg.Connection, key: str) -> CachedResponse | None:
    row = await conn.fetchrow(
        "SELECT response_text, generated_by FROM llm_response_cache WHERE cache_key = $1 AND expires_at > now()",
        key,
    )
    if row is None:
        return None
    return CachedResponse(text=str(row["response_text"]), generated_by=str(row["generated_by"]))


async def put_cached(conn: asyncpg.Connection, key: str, intent: str, card_id: int, text: str, generated_by: str) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=get_settings().llm_cache_ttl_hours)
    sql = (
        "INSERT INTO llm_response_cache (cache_key, intent, card_id, response_text, generated_by, expires_at) "
        "VALUES ($1, $2, $3, $4, $5, $6) "
        "ON CONFLICT (cache_key) DO UPDATE SET "
        "response_text = EXCLUDED.response_text, "
        "generated_by = EXCLUDED.generated_by, "
        "expires_at = EXCLUDED.expires_at"
    )
    await conn.execute(
        sql,
        key,
        intent,
        card_id,
        text,
        generated_by,
        expires_at,
    )
