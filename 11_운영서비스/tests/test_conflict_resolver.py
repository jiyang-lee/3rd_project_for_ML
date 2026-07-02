"""conflict resolver 단위테스트 — run_33 resolve()의 8개 gate 조합 케이스."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from heatgrid_service.pipeline.gates import resolve_conflict  # noqa: E402


@pytest.mark.parametrize(
    "fault_p,task_p,activity_p,expected_primary,expected_secondary,expected_review",
    [
        (0.1, 0.1, 0.1, "normal", "", False),                    # no gate
        (0.8, 0.1, 0.1, "fault", "", False),                     # fault only
        (0.1, 0.8, 0.1, "task", "", False),                      # task only
        (0.1, 0.1, 0.8, "activity", "", False),                  # activity only
        (0.8, 0.9, 0.1, "fault", "task", True),                  # fault+task → fault 우선
        (0.8, 0.1, 0.9, "fault", "activity", True),              # fault+activity
        (0.1, 0.9, 0.7, "task", "activity", True),               # task+activity → 높은 확률
        (0.1, 0.6, 0.9, "activity", "task", True),               # activity 확률 우세
        (0.8, 0.9, 0.9, "fault", "task|activity", True),         # all on → fault 우선
    ],
)
def test_resolver_cases(fault_p, task_p, activity_p, expected_primary, expected_secondary, expected_review):
    result = resolve_conflict(fault_p, task_p, activity_p)
    assert result.primary_state == expected_primary
    assert result.secondary_tags == expected_secondary
    assert result.review_flag == expected_review


def test_all_near_threshold_review():
    result = resolve_conflict(0.52, 0.48, 0.51)
    assert "all_gate_probabilities_near_threshold" in result.review_reasons
    assert result.review_flag is True


def test_task_activity_tie_prefers_task():
    result = resolve_conflict(0.1, 0.7, 0.7)
    assert result.primary_state == "task"  # run_33: task_p >= act_p → task
