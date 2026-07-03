from __future__ import annotations

from dataclasses import dataclass

from .prompts import CARD_GRAPH_ORDER


@dataclass(frozen=True)
class CardGraphTrace:
    intent: str
    nodes: list[str]


def trace_for_intent(intent: str) -> CardGraphTrace:
    return CardGraphTrace(intent=intent, nodes=list(CARD_GRAPH_ORDER))
