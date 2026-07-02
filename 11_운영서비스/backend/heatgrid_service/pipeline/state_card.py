"""상태카드 빌더 — run_39 스키마(L84-110) + 전체 파이프라인 조립.

fault_group은 모델 예측이 아니라 리플레이 시나리오 메타데이터(faults.csv) 조인이다.
UI에는 '시나리오 메타데이터 기반'으로 정직하게 표기한다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime

from ..models_registry import ModelRegistry
from .gates import ResolvedState, resolve_conflict
from .priority import (
    PRE_EVENT_THRESHOLD,
    GroupPolicy,
    leadtime_urgency,
    priority_score,
    priority_tier,
)


@dataclass
class StateCard:
    sample_id: str
    substation_id: str
    window_start: datetime
    window_end: datetime
    data_scope: str
    primary_state: str
    secondary_tags: str
    fault_detected: bool
    task_detected: bool
    activity_detected: bool
    fault_probability: float
    task_probability: float
    activity_probability: float
    pre_event_detected: str
    risk_probability: float | None
    fault_group: str
    leadtime_label: str
    leadtime_urgency: float | None
    group_weight: float | None
    priority_score: float | None
    priority_tier: str
    review_flag: bool
    review_reasons: str
    why_reason: str
    coverage_rate: float
    validation_level: str = "replay_simulation"
    features: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def build_low_coverage_card(
    substation_id: str,
    window_start: datetime,
    window_end: datetime,
    coverage_rate: float,
) -> StateCard:
    return StateCard(
        sample_id=f"{substation_id}_{window_end:%Y%m%d%H%M}",
        substation_id=substation_id,
        window_start=window_start,
        window_end=window_end,
        data_scope="replay_simulation",
        primary_state="review_required",
        secondary_tags="",
        fault_detected=False,
        task_detected=False,
        activity_detected=False,
        fault_probability=float("nan"),
        task_probability=float("nan"),
        activity_probability=float("nan"),
        pre_event_detected="not_available_low_coverage",
        risk_probability=None,
        fault_group="not_applicable",
        leadtime_label="not_available",
        leadtime_urgency=None,
        group_weight=None,
        priority_score=None,
        priority_tier="not_applicable",
        review_flag=True,
        review_reasons="low_coverage",
        why_reason=f"coverage {coverage_rate:.2f} below minimum; cannot compute features",
        coverage_rate=coverage_rate,
    )


def run_pipeline(
    registry: ModelRegistry,
    group_policy: GroupPolicy,
    substation_id: str,
    window_start: datetime,
    window_end: datetime,
    features: dict[str, float],
    coverage_rate: float,
    scenario_fault_group: str | None = None,
) -> StateCard:
    """gate 병렬 → conflict resolver → pre-event → priority 정책 → 상태카드."""
    fault_p = registry.gates["fault_gate"].probability(features)
    task_p = registry.gates["task_gate"].probability(features)
    activity_p = registry.gates["activity_gate"].probability(features)

    resolved: ResolvedState = resolve_conflict(
        fault_p,
        task_p,
        activity_p,
        registry.gates["fault_gate"].threshold,
        registry.gates["task_gate"].threshold,
        registry.gates["activity_gate"].threshold,
    )

    risk: float | None = None
    pre_event_detected = "not_applicable_not_fault"
    fault_group = "not_applicable"
    leadtime_label = "not_available"
    urgency: float | None = None
    group_weight: float | None = None
    score: float | None = None
    tier = "not_applicable"
    review_flag = resolved.review_flag
    review_reasons = resolved.review_reasons
    why = resolved.why_reason

    if resolved.primary_state == "fault":
        risk = registry.pre_event.probability(features)
        pre_event_detected = "true" if risk >= PRE_EVENT_THRESHOLD else "false"

        fault_group = scenario_fault_group or "unknown_review"
        if fault_group == "unknown_review":
            review_flag = True
            review_reasons = "|".join(filter(None, [review_reasons, "fault_group_unmatched"]))

        leadtime_label, stable_hours = group_policy.leadtime(fault_group)
        urgency = leadtime_urgency(stable_hours)
        group_weight = group_policy.weight(fault_group)
        score = priority_score(risk, urgency, group_weight)
        tier = priority_tier(risk, score)
        if pre_event_detected == "true":
            why = f"{why}; pre-event risk {risk:.2f} >= {PRE_EVENT_THRESHOLD}"

    return StateCard(
        sample_id=f"{substation_id}_{window_end:%Y%m%d%H%M}",
        substation_id=substation_id,
        window_start=window_start,
        window_end=window_end,
        data_scope="replay_simulation",
        primary_state=resolved.primary_state,
        secondary_tags=resolved.secondary_tags,
        fault_detected=resolved.fault_detected,
        task_detected=resolved.task_detected,
        activity_detected=resolved.activity_detected,
        fault_probability=fault_p,
        task_probability=task_p,
        activity_probability=activity_p,
        pre_event_detected=pre_event_detected,
        risk_probability=risk,
        fault_group=fault_group,
        leadtime_label=leadtime_label,
        leadtime_urgency=urgency,
        group_weight=group_weight,
        priority_score=score,
        priority_tier=tier,
        review_flag=review_flag,
        review_reasons=review_reasons,
        why_reason=why,
        coverage_rate=coverage_rate,
        features=features,
    )
