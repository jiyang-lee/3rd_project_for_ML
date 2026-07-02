"""추론 스케줄러 — 가상시계 기준으로 substation별 7일 window를 주기적으로 채점하는 asyncio 루프."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .config import get_settings
from .db import get_pool
from .features import add_derived_signals, compute_compact13, window_coverage
from .models_registry import load_registry
from .pipeline.priority import GroupPolicy, semantic_fault_group
from .pipeline.state_card import StateCard, build_low_coverage_card, run_pipeline
from .api.ws import broadcaster
from .replay.extract import META_DIR, parse_substation

logger = logging.getLogger("heatgrid.scheduler")

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
    """리플레이 시나리오 메타데이터(faults.csv) 조인으로 fault_group 부여.

    모델 예측이 아님 — window_end가 [Report date - 10d, Report date + 2d] 안에 있으면 해당 이벤트로 간주.
    """
    manufacturer, raw_id = parse_substation(substation_id)
    faults = load_fault_metadata(manufacturer)
    subset = faults[faults["substation ID"].eq(raw_id)]
    we = pd.Timestamp(window_end.replace(tzinfo=None))
    for _, row in subset.iterrows():
        report = row["Report date"]
        if pd.isna(report):
            continue
        if report - pd.Timedelta(days=10) <= we <= report + pd.Timedelta(days=2):
            return semantic_fault_group(row.get("Fault label", ""))
    return None


async def fetch_window(conn, substation_id: str, start: datetime, end: datetime) -> pd.DataFrame:
    rows = await conn.fetch(
        "SELECT * FROM sensor_readings WHERE substation_id = $1 AND ts >= $2 AND ts < $3 ORDER BY ts",
        substation_id,
        start,
        end,
    )
    if not rows:
        return pd.DataFrame(columns=["timestamp"])
    df = pd.DataFrame([dict(r) for r in rows])
    df["timestamp"] = pd.to_datetime(df["ts"]).dt.tz_localize(None)
    return add_derived_signals(df.drop(columns=["ts", "substation_id"]))


async def upsert_card(conn, card: StateCard) -> int:
    row = await conn.fetchrow(
        """
        INSERT INTO state_cards (
            sample_id, substation_id, window_start, window_end, data_scope,
            primary_state, secondary_tags,
            fault_detected, task_detected, activity_detected,
            fault_probability, task_probability, activity_probability,
            pre_event_detected, risk_probability, fault_group, leadtime_label,
            leadtime_urgency, group_weight, priority_score, priority_tier,
            review_flag, review_reasons, why_reason, coverage_rate,
            validation_level, features
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26,$27)
        ON CONFLICT (sample_id) DO UPDATE SET created_at = now()
        RETURNING card_id
        """,
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
        json.dumps({k: (None if pd.isna(v) else v) for k, v in card.features.items()}),
    )
    return int(row["card_id"])


async def score_substation(conn, substation_id: str, virtual_time: datetime) -> StateCard | None:
    settings = get_settings()
    window_end = virtual_time
    window_start = window_end - timedelta(days=WINDOW_DAYS)

    last_end = await conn.fetchval(
        "SELECT max(window_end) FROM state_cards WHERE substation_id = $1", substation_id
    )
    if last_end is not None:
        stride = timedelta(hours=settings.inference_virtual_stride_hours)
        if window_end - last_end < stride:
            return None

    window = await fetch_window(conn, substation_id, window_start, window_end)
    naive_start = window_start.replace(tzinfo=None)
    naive_end = window_end.replace(tzinfo=None)
    coverage = window_coverage(window, naive_start, naive_end)

    if coverage < settings.coverage_min:
        card = build_low_coverage_card(substation_id, window_start, window_end, coverage)
    else:
        feats = compute_compact13(window, naive_start, naive_end)
        card = run_pipeline(
            registry=load_registry(),
            group_policy=get_group_policy(),
            substation_id=substation_id,
            window_start=window_start,
            window_end=window_end,
            features=feats,
            coverage_rate=coverage,
            scenario_fault_group=scenario_fault_group(substation_id, window_end),
        )
    return card


async def inference_loop() -> None:
    settings = get_settings()
    from .agent.graph import run_agent  # 지연 import (순환 방지)

    last_agent_run = datetime.min.replace(tzinfo=timezone.utc)
    while True:
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                vt = await conn.fetchval("SELECT virtual_time FROM replay_state WHERE id = 1")
                if vt is None:
                    await asyncio.sleep(settings.inference_real_interval_sec)
                    continue
                subs = [r["substation_id"] for r in await conn.fetch("SELECT substation_id FROM substations WHERE active")]
                alert_cards: list[tuple[int, StateCard]] = []
                for sub in subs:
                    card = await score_substation(conn, sub, vt)
                    if card is None:
                        continue
                    card_id = await upsert_card(conn, card)
                    payload = card.to_dict()
                    payload["card_id"] = card_id
                    await broadcaster.publish("state_card", payload)
                    logger.info(
                        "card %s: %s (fault_p=%.2f, tier=%s)",
                        card.sample_id,
                        card.primary_state,
                        0 if pd.isna(card.fault_probability) else card.fault_probability,
                        card.priority_tier,
                    )
                    if (card.primary_state == "fault" and card.pre_event_detected == "true") or card.review_flag:
                        alert_cards.append((card_id, card))

            now = datetime.now(timezone.utc)
            if alert_cards and (now - last_agent_run).total_seconds() >= settings.agent_min_interval_sec:
                last_agent_run = now
                asyncio.create_task(run_agent([cid for cid, _ in alert_cards]))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("inference loop iteration failed")
        await asyncio.sleep(settings.inference_real_interval_sec)
