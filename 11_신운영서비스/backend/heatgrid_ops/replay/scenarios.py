from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Final, Iterable

import pandas as pd

from ..config import get_settings
from ..handoff_cards import load_handoff_cards
from .extract import ZIP_PREFIX

FAULT_LABELS: Final[dict[str, str]] = {
    "control_controller": "제어기",
    "leakage_water_loss": "누수/열손실",
    "pump_failure": "펌프 고장",
    "pressure_regulator": "차압/압력 조절",
    "valve_actuator": "밸브/구동기",
    "unknown_review": "검토 필요",
}
TIER_LABELS: Final[dict[str, str]] = {
    "urgent": "긴급",
    "high": "높음",
    "medium": "중간",
    "low": "낮음",
    "monitor": "관찰",
    "not_applicable": "해당 없음",
}
FAULT_TIERS: Final[set[str]] = {"urgent", "high", "medium"}
NORMAL_FAULT_GROUPS: Final[set[str]] = {"not_applicable", "normal", "unknown_review", ""}
MANUFACTURER_CODE_BY_LABEL: Final[dict[str, str]] = {label: code for code, label in ZIP_PREFIX.items()}


@dataclass(frozen=True, slots=True)
class ReplayScenario:
    scenario_id: str
    label: str
    virtual_time: datetime
    substation_id: str
    priority_tier: str
    fault_group: str
    leadtime_label: str
    priority_score: float | None
    description: str


@dataclass(frozen=True, slots=True)
class ReplayTimeRange:
    start: datetime | None
    end: datetime | None
    count: int


def utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def prepare_handoff_scenarios(frame: pd.DataFrame, active_substations: Iterable[str]) -> pd.DataFrame:
    active = set(active_substations)
    if frame.empty or not active:
        return pd.DataFrame()

    prepared = frame.copy()
    prepared["manufacturer_code"] = prepared["manufacturer"].map(MANUFACTURER_CODE_BY_LABEL)
    prepared["window_end"] = pd.to_datetime(prepared["window_end"], errors="coerce", utc=True)
    prepared["replay_substation_id"] = prepared.apply(_replay_substation_id, axis=1)
    prepared = prepared[prepared["replay_substation_id"].isin(active) & prepared["window_end"].notna()]
    return prepared.sort_values(["window_end", "priority_score"], ascending=[True, False])


def available_handoff_frame(active_substations: Iterable[str] | None = None) -> pd.DataFrame:
    settings = get_settings()
    active = settings.replay_substation_list if active_substations is None else list(active_substations)
    return prepare_handoff_scenarios(load_handoff_cards(), active)


def available_time_range(active_substations: Iterable[str] | None = None) -> ReplayTimeRange:
    frame = available_handoff_frame(active_substations)
    if frame.empty:
        return ReplayTimeRange(start=None, end=None, count=0)
    times = sorted(_unique_times(frame))
    return ReplayTimeRange(start=times[0], end=times[-1], count=len(times))


def nearest_replay_time(target: datetime, active_substations: Iterable[str] | None = None) -> datetime | None:
    times = sorted(_unique_times(available_handoff_frame(active_substations)))
    if not times:
        return None
    requested = utc_datetime(target)
    return min(times, key=lambda value: abs((value - requested).total_seconds()))


def next_replay_time(current: datetime | None, active_substations: Iterable[str] | None = None) -> datetime | None:
    times = sorted(_unique_times(available_handoff_frame(active_substations)))
    if not times:
        return None
    if current is None:
        return times[0]
    current_utc = utc_datetime(current)
    for candidate in times:
        if candidate > current_utc:
            return candidate
    return times[0]


def build_fault_scenarios(limit: int = 12, active_substations: Iterable[str] | None = None) -> list[ReplayScenario]:
    frame = available_handoff_frame(active_substations)
    if frame.empty:
        return []

    fault_frame = frame[
        frame["priority_level"].isin(FAULT_TIERS) | ~frame["m1_specialist_fault_group"].fillna("").isin(NORMAL_FAULT_GROUPS)
    ]
    if fault_frame.empty:
        fault_frame = frame

    sorted_frame = fault_frame.sort_values(["priority_score", "window_end"], ascending=[False, False])
    diverse = sorted_frame.drop_duplicates(["m1_specialist_fault_group", "replay_substation_id"], keep="first")
    if len(diverse) < limit:
        diverse = pd.concat([diverse, sorted_frame]).drop_duplicates(["replay_substation_id", "window_end"], keep="first")
    return [_scenario_from_row(row) for _, row in diverse.head(limit).iterrows()]


def _replay_substation_id(row: pd.Series) -> str | None:
    manufacturer_code = row.get("manufacturer_code")
    raw_id = row.get("substation_id")
    if not isinstance(manufacturer_code, str) or pd.isna(raw_id):
        return None
    return f"{manufacturer_code}_{int(raw_id)}"


def _unique_times(frame: pd.DataFrame) -> set[datetime]:
    timestamps = pd.to_datetime(frame["window_end"], errors="coerce", utc=True)
    return {timestamp.to_pydatetime().astimezone(timezone.utc) for timestamp in timestamps.dropna().unique()}


def _scenario_from_row(row: pd.Series) -> ReplayScenario:
    substation_id = str(row["replay_substation_id"])
    virtual_time = pd.Timestamp(row["window_end"]).to_pydatetime().astimezone(timezone.utc)
    priority_tier = str(row.get("priority_level", "monitor"))
    fault_group = str(row.get("m1_specialist_fault_group", "unknown_review"))
    leadtime_label = str(row.get("predicted_lead_time_bucket", "not_available"))
    priority_score = _optional_float(row.get("priority_score"))
    fault_label = FAULT_LABELS.get(fault_group, fault_group)
    tier_label = TIER_LABELS.get(priority_tier, priority_tier)
    time_label = virtual_time.strftime("%Y-%m-%d %H:%M")
    score_label = f"{priority_score:.1f}" if priority_score is not None else "-"
    return ReplayScenario(
        scenario_id=f"{substation_id}_{virtual_time:%Y%m%d%H%M}",
        label=f"{substation_id} · {fault_label} · {tier_label} · {time_label}",
        virtual_time=virtual_time,
        substation_id=substation_id,
        priority_tier=priority_tier,
        fault_group=fault_group,
        leadtime_label=leadtime_label,
        priority_score=priority_score,
        description=f"{leadtime_label} 예측, 우선순위 {score_label}",
    )


def _optional_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)
