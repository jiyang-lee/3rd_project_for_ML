"""front gate 병렬 판정 + conflict resolver — run_33 L401-437 포팅."""

from __future__ import annotations

from dataclasses import dataclass

NEAR_THRESHOLD_MARGIN = 0.05


@dataclass
class ResolvedState:
    primary_state: str
    secondary_tags: str
    review_flag: bool
    review_reasons: str
    why_reason: str
    fault_detected: bool
    task_detected: bool
    activity_detected: bool
    fault_probability: float
    task_probability: float
    activity_probability: float


def resolve_conflict(
    fault_probability: float,
    task_probability: float,
    activity_probability: float,
    fault_threshold: float = 0.5,
    task_threshold: float = 0.5,
    activity_threshold: float = 0.5,
) -> ResolvedState:
    gate_on = {
        "fault": fault_probability >= fault_threshold,
        "task": task_probability >= task_threshold,
        "activity": activity_probability >= activity_threshold,
    }
    near = {
        "fault": abs(fault_probability - fault_threshold) <= NEAR_THRESHOLD_MARGIN,
        "task": abs(task_probability - task_threshold) <= NEAR_THRESHOLD_MARGIN,
        "activity": abs(activity_probability - activity_threshold) <= NEAR_THRESHOLD_MARGIN,
    }
    active = [name for name in ["fault", "task", "activity"] if gate_on[name]]

    review_reasons: list[str] = []
    if near["fault"] and near["task"] and near["activity"]:
        review_reasons.append("all_gate_probabilities_near_threshold")
    if len(active) > 1:
        review_reasons.append("multi_gate_conflict")

    secondary: list[str] = []
    if not active:
        primary = "normal"
        why = "no gate crossed threshold"
    elif "fault" in active:
        primary = "fault"
        secondary = [x for x in active if x != "fault"]
        why = "fault gate crossed threshold; fault has runtime priority"
    elif set(active) == {"task", "activity"}:
        primary = "task" if task_probability >= activity_probability else "activity"
        secondary = ["activity" if primary == "task" else "task"]
        why = "task and activity both crossed threshold; higher probability selected"
    else:
        primary = active[0]
        why = f"{active[0]} gate crossed threshold"

    return ResolvedState(
        primary_state=primary,
        secondary_tags="|".join(secondary),
        review_flag=bool(review_reasons),
        review_reasons="|".join(review_reasons),
        why_reason=why,
        fault_detected=gate_on["fault"],
        task_detected=gate_on["task"],
        activity_detected=gate_on["activity"],
        fault_probability=fault_probability,
        task_probability=task_probability,
        activity_probability=activity_probability,
    )
