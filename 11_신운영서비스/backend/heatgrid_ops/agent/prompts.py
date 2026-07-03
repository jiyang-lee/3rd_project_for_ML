from __future__ import annotations

OPS_GRAPH_ORDER = [
    "observe",
    "compute_features",
    "run_gates",
    "run_anomaly",
    "resolve_conflicts",
    "score_priority",
    "upsert_cards",
    "select_top_n",
    "auto_brief",
    "record",
]

CARD_GRAPH_ORDER = [
    "load_card",
    "check_cache",
    "gather_evidence",
    "compose",
    "persist",
]
