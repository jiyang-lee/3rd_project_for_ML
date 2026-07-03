from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime

from ..models_registry import ModelRegistry
from .gates import ResolvedState, resolve_conflict
from .priority import GroupPolicy, leadtime_urgency, priority_score, priority_tier


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
    source_card: dict[str, str | int | float | bool | None] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str | int | float | bool | None | dict[str, float]]:
        return asdict(self)


@dataclass(frozen=True)
class PipelineInput:
    substation_id: str
    window_start: datetime
    window_end: datetime
    features: dict[str, float]
    coverage_rate: float
    scenario_fault_group: str | None = None
    system_capability_group: str | None = None


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
        priority_tier="monitor",
        review_flag=True,
        review_reasons="low_coverage",
        why_reason=f"coverage {coverage_rate:.2f} below minimum",
        coverage_rate=coverage_rate,
    )


def run_pipeline(registry: ModelRegistry, group_policy: GroupPolicy, request: PipelineInput) -> StateCard:
    fault_p = registry.gates["fault_gate"].probability(request.features)
    task_p = registry.gates["task_gate"].probability(request.features)
    activity_p = registry.gates["activity_gate"].probability(request.features)
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
    tier = "monitor"
    review_flag = resolved.review_flag
    review_reasons = resolved.review_reasons
    why = resolved.why_reason

    if resolved.primary_state == "fault" and registry.pre_event is not None:
        risk = registry.pre_event.probability(request.features)
        threshold = registry.pre_event.threshold_for(request.system_capability_group)
        pre_event_detected = "true" if risk >= threshold else "false"
        fault_group = request.scenario_fault_group or "unknown_review"
        if fault_group == "unknown_review":
            review_flag = True
            review_reasons = "|".join(filter(None, [review_reasons, "fault_group_unmatched"]))
        leadtime_label, stable_hours = group_policy.leadtime(fault_group)
        urgency = leadtime_urgency(stable_hours)
        group_weight = group_policy.weight(fault_group)
        score = priority_score(risk, urgency, group_weight)
        tier = priority_tier(risk, score, threshold)
        if pre_event_detected == "true":
            why = f"{why}; pre-event risk {risk:.2f} >= {threshold}"

    return StateCard(
        sample_id=f"{request.substation_id}_{request.window_end:%Y%m%d%H%M}",
        substation_id=request.substation_id,
        window_start=request.window_start,
        window_end=request.window_end,
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
        coverage_rate=request.coverage_rate,
        features=request.features,
    )
