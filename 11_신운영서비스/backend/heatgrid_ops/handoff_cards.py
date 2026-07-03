from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from typing import Final

import pandas as pd

from .config import get_settings
from .pipeline.state_card import StateCard
from .replay.extract import parse_substation

MANUFACTURER_LABELS: Final = {"M1": "manufacturer 1", "M2": "manufacturer 2"}
FEATURE_COLUMNS: Final = (
    "anomaly_ensemble_score",
    "iforest_score_ratio",
    "mahalanobis_score_ratio",
    "anomaly_consensus_count",
    "anomaly_criticality",
    "risk_score",
    "current_best_priority_score",
    "m1_specialist_priority_score",
    "m1_hybrid_priority_score",
    "shadow_priority_score",
    "stable_crossing_lead_hours",
)


@lru_cache(maxsize=1)
def load_handoff_cards() -> pd.DataFrame:
    path = get_settings().handoff_agent_card_csv
    if not path.exists():
        raise FileNotFoundError(f"handoff agent card not found: {path}; run setup/bootstrap.py first")
    cards = pd.read_csv(path)
    cards["window_start"] = pd.to_datetime(cards["window_start"], errors="coerce")
    cards["window_end"] = pd.to_datetime(cards["window_end"], errors="coerce")
    return cards


def card_from_handoff(substation_id: str, window_end: datetime) -> StateCard | None:
    manufacturer, raw_id = parse_substation(substation_id)
    manufacturer_label = MANUFACTURER_LABELS.get(manufacturer)
    if manufacturer_label is None:
        return None
    frame = load_handoff_cards()
    window_key = pd.Timestamp(window_end.replace(tzinfo=None))
    matches = frame[
        frame["manufacturer"].eq(manufacturer_label)
        & frame["substation_id"].eq(raw_id)
        & frame["window_end"].eq(window_key)
    ]
    if matches.empty:
        return None
    row = matches.iloc[0]
    csv_window_start = _datetime(row, "window_start", window_end)
    csv_window_end = _datetime(row, "window_end", window_end)
    pre_event_probability = _float(row, "m1_specialist_pre_event_probability", 0.0)
    priority = _optional_float(row, "priority_score")
    return StateCard(
        sample_id=f"{substation_id}_{csv_window_end:%Y%m%d%H%M}",
        substation_id=substation_id,
        window_start=csv_window_start,
        window_end=csv_window_end,
        data_scope="m1_specialist_handoff",
        primary_state=_text(row, "primary_state", "review_required"),
        secondary_tags=_text(row, "m1_specialist_secondary_tags", ""),
        fault_detected=_float(row, "m1_specialist_fault_probability", 0.0) >= 0.5,
        task_detected=_float(row, "m1_specialist_task_probability", 0.0) >= 0.5,
        activity_detected=_float(row, "m1_specialist_activity_probability", 0.0) >= 0.5,
        fault_probability=_float(row, "m1_specialist_fault_probability", 0.0),
        task_probability=_float(row, "m1_specialist_task_probability", 0.0),
        activity_probability=_float(row, "m1_specialist_activity_probability", 0.0),
        pre_event_detected="true" if pre_event_probability >= 0.6 else "false",
        risk_probability=_optional_float(row, "risk_probability"),
        fault_group=_text(row, "m1_specialist_fault_group", "unknown_review"),
        leadtime_label=_text(row, "predicted_lead_time_bucket", "not_available"),
        leadtime_urgency=_optional_float(row, "leadtime_urgency_score"),
        group_weight=_optional_float(row, "m1_specialist_group_weight"),
        priority_score=priority,
        priority_tier=_text(row, "priority_level", "monitor"),
        review_flag=_bool(row, "review_required"),
        review_reasons=_text(row, "review_reasons", ""),
        why_reason=_text(row, "why_reason", ""),
        coverage_rate=1.0,
        validation_level="m1_specialist_full_handoff",
        features=_features(row),
        source_card={str(k): _json_value(v) for k, v in row.to_dict().items()},
    )


def _datetime(row: pd.Series, column: str, fallback: datetime) -> datetime:
    value = row.get(column)
    if value is None or pd.isna(value):
        return fallback
    timestamp = pd.Timestamp(value).to_pydatetime()
    return timestamp.replace(tzinfo=timezone.utc)


def _text(row: pd.Series, column: str, default: str) -> str:
    value = row.get(column)
    if value is None or pd.isna(value):
        return default
    return str(value)


def _bool(row: pd.Series, column: str) -> bool:
    value = row.get(column)
    if value is None or pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _float(row: pd.Series, column: str, default: float) -> float:
    value = _optional_float(row, column)
    if value is None:
        return default
    return value


def _optional_float(row: pd.Series, column: str) -> float | None:
    value = row.get(column)
    if value is None or pd.isna(value):
        return None
    return float(value)


def _features(row: pd.Series) -> dict[str, float]:
    return {column: float(row[column]) for column in FEATURE_COLUMNS if column in row and not pd.isna(row[column])}


def _json_value(value: object) -> str | int | float | bool | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, bool | int | float | str):
        return value
    return str(value)
