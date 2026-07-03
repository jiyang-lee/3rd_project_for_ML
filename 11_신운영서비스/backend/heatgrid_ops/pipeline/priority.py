"""priority 정책 layer — run_28 L272-307 포팅. ML 모델이 아니라 정책 점수."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PRE_EVENT_THRESHOLD = 0.6
WEIGHTS = {"risk_probability": 0.55, "leadtime_urgency": 0.30, "group_weight": 0.15}


def semantic_fault_group(label: str) -> str:
    text = str(label).strip().lower()
    if text == "unknown" or not text:
        return "unknown_review"
    if "pump" in text:
        return "pump_failure"
    if "control unit" in text or "parameter" in text or "temperature monitor" in text or "controller" in text:
        return "control_controller"
    if "motorised control valve" in text or "shut-off valve" in text:
        return "valve_actuator"
    if "differential pressure regulator" in text:
        return "pressure_regulator"
    if "leakage" in text or "safety relief valve" in text:
        return "leakage_water_loss"
    return "other_review"


def leadtime_urgency(stable_hours) -> float:
    if stable_hours is None or pd.isna(stable_hours):
        return 0.0
    stable_hours = float(stable_hours)
    if stable_hours <= 24:
        return 1.0
    if stable_hours <= 72:
        return 0.7
    return 0.4


def priority_score(risk_probability: float, urgency: float, group_weight: float) -> float:
    return 100.0 * (
        WEIGHTS["risk_probability"] * risk_probability
        + WEIGHTS["leadtime_urgency"] * urgency
        + WEIGHTS["group_weight"] * group_weight
    )


def priority_tier(risk_probability: float, score: float, risk_threshold: float = PRE_EVENT_THRESHOLD) -> str:
    if risk_probability < risk_threshold or score < 50:
        return "monitor"
    if score >= 80:
        return "high"
    if score >= 65:
        return "medium"
    return "low"


def leadtime_label_from_hours(hours) -> str:
    if hours is None or pd.isna(hours):
        return "not_available"
    hours = float(hours)
    if hours >= 72:
        return "early_stable"
    if hours >= 12:
        return "short_stable"
    if hours >= 0:
        return "report_time_only"
    return "unstable_or_not_detected"


@dataclass
class GroupPolicy:
    weights: dict[str, float]
    leadtime_labels: dict[str, str]
    leadtime_hours: dict[str, float]

    @classmethod
    def load(cls, profile_csv: Path, leadtime_csv: Path) -> "GroupPolicy":
        profile = pd.read_csv(profile_csv)
        leadtime = pd.read_csv(leadtime_csv, encoding="utf-8-sig")
        leadtime = leadtime.loc[leadtime["scope"].eq("main")]
        weights = dict(zip(profile["fault_group"], profile["group_weight"].astype(float)))
        labels = dict(zip(leadtime["fault_group"], leadtime["leadtime_label"].astype(str)))
        hours = dict(zip(leadtime["fault_group"], pd.to_numeric(leadtime["median_stable_lead_time_hours"], errors="coerce")))
        return cls(weights=weights, leadtime_labels=labels, leadtime_hours=hours)

    def weight(self, fault_group: str) -> float:
        return float(self.weights.get(fault_group, 0.1))

    def leadtime(self, fault_group: str) -> tuple[str, float | None]:
        label = self.leadtime_labels.get(fault_group)
        hours = self.leadtime_hours.get(fault_group)
        if label is None:
            return leadtime_label_from_hours(hours), hours
        return label, hours
