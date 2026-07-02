"""LangGraph 그래프: observe → analyze → prioritize → dispatch → record → END."""

from __future__ import annotations

import logging
from functools import lru_cache

from langgraph.graph import END, StateGraph

from .nodes import AgentState, analyze, dispatch, observe, prioritize, record

logger = logging.getLogger("heatgrid.agent")


@lru_cache(maxsize=1)
def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("observe", observe)
    graph.add_node("analyze", analyze)
    graph.add_node("prioritize", prioritize)
    graph.add_node("dispatch", dispatch)
    graph.add_node("record", record)
    graph.set_entry_point("observe")
    graph.add_edge("observe", "analyze")
    graph.add_edge("analyze", "prioritize")
    graph.add_edge("prioritize", "dispatch")
    graph.add_edge("dispatch", "record")
    graph.add_edge("record", END)
    return graph.compile()


async def run_agent(trigger_card_ids: list[int]) -> None:
    if not trigger_card_ids:
        return
    try:
        app = build_graph()
        await app.ainvoke({"trigger_card_ids": trigger_card_ids})
    except Exception:
        logger.exception("agent run failed")
        from ..db import get_pool

        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO agent_runs (trigger_card_ids, status, error) VALUES ($1, 'failed', 'see logs')",
                trigger_card_ids,
            )
