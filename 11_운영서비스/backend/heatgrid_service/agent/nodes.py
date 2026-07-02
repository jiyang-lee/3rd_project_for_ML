"""LangGraph 노드: observe → analyze → prioritize → dispatch → record.

LLM 노드는 키가 없거나 호출 실패 시 각자 템플릿 폴백으로 내려간다 (그래프 분기 아님).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, TypedDict

from ..config import get_settings
from ..db import get_pool
from ..api.ws import broadcaster
from .llm import get_llm, llm_text
from .prompts import ANALYZE_PROMPT, DISPATCH_PROMPT, fallback_analysis, fallback_dispatch

logger = logging.getLogger("heatgrid.agent")


class AgentState(TypedDict, total=False):
    trigger_card_ids: list[int]
    cards: list[dict]
    analysis: dict[int, str]        # card_id -> 설명
    ranked: list[dict]
    orders: list[dict]
    llm_used: bool
    node_trace: dict[str, Any]


def _top_features(card: dict, k: int = 3) -> str:
    feats = card.get("features") or {}
    if isinstance(feats, str):
        feats = json.loads(feats)
    valid = {n: v for n, v in feats.items() if v is not None}
    top = sorted(valid.items(), key=lambda kv: abs(kv[1]), reverse=True)[:k]
    return ", ".join(f"{n}={v:.2f}" for n, v in top)


async def observe(state: AgentState) -> AgentState:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM state_cards WHERE card_id = ANY($1)", state["trigger_card_ids"]
        )
        cards = []
        for r in rows:
            card = dict(r)
            # 최근 지시서가 이미 있는 기계실은 중복 발행 방지
            existing = await conn.fetchval(
                """
                SELECT count(*) FROM dispatch_orders
                 WHERE substation_id = $1 AND status = 'draft'
                   AND virtual_time >= $2 - INTERVAL '2 days'
                """,
                card["substation_id"],
                card["window_end"],
            )
            if existing == 0:
                cards.append(card)
    state["cards"] = cards
    state["node_trace"] = {"observe": {"trigger_count": len(state["trigger_card_ids"]), "after_dedup": len(cards)}}
    return state


async def analyze(state: AgentState) -> AgentState:
    analysis: dict[int, str] = {}
    llm_used = False
    for card in state.get("cards", []):
        risk = card.get("risk_probability")
        prompt = ANALYZE_PROMPT.format(
            substation_id=card["substation_id"],
            primary_state=card["primary_state"],
            why_reason=card["why_reason"],
            fault_probability=card.get("fault_probability") or 0.0,
            risk_probability=f"{risk:.3f}" if risk is not None else "N/A",
            fault_group=card.get("fault_group", "unknown"),
            priority_tier=card.get("priority_tier", "N/A"),
            priority_score=card.get("priority_score") or 0.0,
            top_features=_top_features(card),
        )
        text = llm_text(prompt)
        if text:
            llm_used = True
        analysis[card["card_id"]] = text or fallback_analysis(card)
    state["analysis"] = analysis
    state["llm_used"] = state.get("llm_used", False) or llm_used
    state["node_trace"]["analyze"] = {"analyzed": len(analysis), "llm_used": llm_used}
    return state


async def prioritize(state: AgentState) -> AgentState:
    """결정론적 정렬이 기본 — 정책 점수가 authoritative. review_flag는 동점 시 후순위."""
    cards = state.get("cards", [])
    ranked = sorted(
        cards,
        key=lambda c: (-(c.get("priority_score") or 0.0), c.get("review_flag", False)),
    )
    state["ranked"] = ranked
    state["node_trace"]["prioritize"] = {
        "order": [c["substation_id"] for c in ranked],
        "method": "policy_score_deterministic",
    }
    return state


async def dispatch(state: AgentState) -> AgentState:
    settings = get_settings()
    top_k = settings.agent_dispatch_top_k
    orders: list[dict] = []
    llm_used = False
    targets = [c for c in state.get("ranked", []) if c.get("priority_tier") in {"high", "medium"}][:top_k]
    for card in targets:
        analysis = state["analysis"].get(card["card_id"], "")
        risk = card.get("risk_probability")
        prompt = DISPATCH_PROMPT.format(
            substation_id=card["substation_id"],
            fault_group=card.get("fault_group", "unknown"),
            risk_probability=f"{risk:.3f}" if risk is not None else "N/A",
            priority_tier=card.get("priority_tier", "N/A"),
            priority_score=card.get("priority_score") or 0.0,
            leadtime_label=card.get("leadtime_label", "N/A"),
            analysis=analysis,
        )
        text = llm_text(prompt)
        if text:
            llm_used = True
            title = f"[{card.get('priority_tier')}] {card['substation_id']} 사전점검 출동"
            body = text
            generated_by = f"llm:{settings.openai_model}"
        else:
            title, body = fallback_dispatch(card, analysis)
            generated_by = "fallback:template"
        orders.append(
            {
                "card_id": card["card_id"],
                "substation_id": card["substation_id"],
                "virtual_time": card["window_end"],
                "priority_tier": card.get("priority_tier"),
                "priority_score": card.get("priority_score"),
                "title": title,
                "body_markdown": body,
                "recommended_action": card.get("fault_group", ""),
                "generated_by": generated_by,
            }
        )
    state["orders"] = orders
    state["llm_used"] = state.get("llm_used", False) or llm_used
    state["node_trace"]["dispatch"] = {"orders": len(orders), "llm_used": llm_used}
    return state


async def record(state: AgentState) -> AgentState:
    pool = await get_pool()
    status = "completed" if get_llm() is not None else "skipped_no_llm"
    async with pool.acquire() as conn:
        for order in state.get("orders", []):
            row = await conn.fetchrow(
                """
                INSERT INTO dispatch_orders (card_id, substation_id, virtual_time, priority_tier,
                                             priority_score, title, body_markdown, recommended_action, generated_by)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                RETURNING order_id, created_at
                """,
                order["card_id"],
                order["substation_id"],
                order["virtual_time"],
                order["priority_tier"],
                order["priority_score"],
                order["title"],
                order["body_markdown"],
                order["recommended_action"],
                order["generated_by"],
            )
            payload = {**order, "order_id": row["order_id"], "created_at": row["created_at"], "status": "draft"}
            await broadcaster.publish("dispatch_order", payload)
        run_row = await conn.fetchrow(
            """
            INSERT INTO agent_runs (trigger_card_ids, status, node_trace)
            VALUES ($1, $2, $3)
            RETURNING run_id, started_at
            """,
            state["trigger_card_ids"],
            status,
            json.dumps(state.get("node_trace", {}), default=str),
        )
    await broadcaster.publish(
        "agent_run",
        {
            "run_id": run_row["run_id"],
            "started_at": run_row["started_at"],
            "status": status,
            "node_trace": state.get("node_trace", {}),
            "trigger_card_ids": state["trigger_card_ids"],
        },
    )
    logger.info("agent run %s: %d orders (%s)", run_row["run_id"], len(state.get("orders", [])), status)
    return state
