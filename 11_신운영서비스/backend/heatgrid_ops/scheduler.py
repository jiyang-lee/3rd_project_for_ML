from __future__ import annotations

import json
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

import asyncpg
import pandas as pd

from .api.ws import broadcaster
from .config import get_settings
from .features import add_derived_signals, compute_compact13, window_coverage
from .handoff_cards import card_from_handoff
from .models_registry import load_registry
from .pipeline.priority import GroupPolicy, semantic_fault_group
from .pipeline.state_card import PipelineInput, StateCard, build_low_coverage_card, run_pipeline
from .replay.extract import META_DIR, parse_substation

WINDOW_DAYS = 7


@lru_cache(maxsize=1)
def get_group_policy() -> GroupPolicy:
    settings = get_settings()
    return GroupPolicy.load(Path(settings.group_profile_csv), Path(settings.leadtime_summary_csv))


@lru_cache(maxsize=4)
def load_fault_metadata(manufacturer: str) -> pd.DataFrame:
    settings = get_settings()
    path = Path(settings.predist_metadata_dir) / META_DIR[manufacturer] / "faults.csv"
    faults = pd.read_csv(path, sep=";")
    faults["Report date"] = pd.to_datetime(faults["Report date"], errors="coerce")
    return faults


def scenario_fault_group(substation_id: str, window_end: datetime) -> str | None:
    manufacturer, raw_id = parse_substation(substation_id)
    faults = load_fault_metadata(manufacturer)
    subset = faults[faults["substation ID"].eq(raw_id)]
    window_key = pd.Timestamp(window_end.replace(tzinfo=None))
    for _, row in subset.iterrows():
        report = row["Report date"]
        if pd.isna(report):
            continue
        if report - pd.Timedelta(days=10) <= window_key <= report + pd.Timedelta(days=2):
            return semantic_fault_group(row.get("Fault label", ""))
    return None


async def fetch_window(conn: asyncpg.Connection, substation_id: str, start: datetime, end: datetime) -> pd.DataFrame:
    rows = await conn.fetch(
        "SELECT * FROM sensor_readings WHERE substation_id = $1 AND ts >= $2 AND ts < $3 ORDER BY ts",
        substation_id,
        start,
        end,
    )
    if not rows:
        return pd.DataFrame(columns=["timestamp"])
    frame = pd.DataFrame([dict(row) for row in rows])
    frame["timestamp"] = pd.to_datetime(frame["ts"]).dt.tz_localize(None)
    return add_derived_signals(frame.drop(columns=["ts", "substation_id"]))


async def upsert_card(conn: asyncpg.Connection, card: StateCard) -> int:
    payload = json.dumps({k: None if pd.isna(v) else v for k, v in card.features.items()})
    source_card = json.dumps(card.source_card, ensure_ascii=False, default=str)
    sql = (
        "INSERT INTO agent_priority_card "
        "(sample_id, substation_id, window_start, window_end, data_scope, primary_state, secondary_tags, "
        "fault_detected, task_detected, activity_detected, fault_probability, task_probability, activity_probability, "
        "pre_event_detected, risk_probability, fault_group, leadtime_label, leadtime_urgency, group_weight, "
        "priority_score, priority_tier, review_flag, review_reasons, why_reason, coverage_rate, validation_level, "
        "features, source_card) VALUES "
        "($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26,$27,$28) "
        "ON CONFLICT (sample_id) DO UPDATE SET created_at = now() RETURNING card_id"
    )
    row = await conn.fetchrow(
        sql,
        card.sample_id,
        card.substation_id,
        card.window_start,
        card.window_end,
        card.data_scope,
        card.primary_state,
        card.secondary_tags,
        card.fault_detected,
        card.task_detected,
        card.activity_detected,
        None if pd.isna(card.fault_probability) else card.fault_probability,
        None if pd.isna(card.task_probability) else card.task_probability,
        None if pd.isna(card.activity_probability) else card.activity_probability,
        card.pre_event_detected,
        card.risk_probability,
        card.fault_group,
        card.leadtime_label,
        card.leadtime_urgency,
        card.group_weight,
        card.priority_score,
        card.priority_tier,
        card.review_flag,
        card.review_reasons,
        card.why_reason,
        card.coverage_rate,
        card.validation_level,
        payload,
        source_card,
    )
    return int(row["card_id"])


async def score_substation(conn: asyncpg.Connection, substation_id: str, virtual_time: datetime) -> StateCard:
    window_end = virtual_time
    window_start = window_end - timedelta(days=WINDOW_DAYS)
    handoff_card = card_from_handoff(substation_id, window_end)
    if handoff_card is not None:
        return handoff_card
    window = await fetch_window(conn, substation_id, window_start, window_end)
    naive_start = window_start.replace(tzinfo=None)
    naive_end = window_end.replace(tzinfo=None)
    coverage = window_coverage(window, naive_start, naive_end)
    settings = get_settings()
    if coverage < settings.coverage_min:
        return build_low_coverage_card(substation_id, window_start, window_end, coverage)
    feats = compute_compact13(window, naive_start, naive_end)
    system_group = await conn.fetchval("SELECT system_capability_group FROM substation WHERE substation_id = $1", substation_id)
    return run_pipeline(
        registry=load_registry(),
        group_policy=get_group_policy(),
        request=PipelineInput(
            substation_id=substation_id,
            window_start=window_start,
            window_end=window_end,
            features=feats,
            coverage_rate=coverage,
            scenario_fault_group=scenario_fault_group(substation_id, window_end),
            system_capability_group=system_group,
        ),
    )


async def run_tick(conn: asyncpg.Connection, virtual_time: datetime) -> list[int]:
    rows = await conn.fetch("SELECT substation_id FROM substation WHERE active ORDER BY substation_id")
    card_ids: list[int] = []
    for row in rows:
        card = await score_substation(conn, str(row["substation_id"]), virtual_time)
        card_id = await upsert_card(conn, card)
        payload = card.to_dict()
        payload["card_id"] = card_id
        await broadcaster.publish("state_card", payload)
        card_ids.append(card_id)
    return card_ids
