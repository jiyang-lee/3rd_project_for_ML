from __future__ import annotations

import pytest

from heatgrid_ops.pipeline.gates import resolve_conflict


@pytest.mark.parametrize(
    ("fault_p", "task_p", "activity_p", "expected_primary", "expected_secondary", "expected_review"),
    [
        (0.1, 0.1, 0.1, "normal", "", False),
        (0.8, 0.1, 0.1, "fault", "", False),
        (0.1, 0.8, 0.1, "task", "", False),
        (0.1, 0.1, 0.8, "activity", "", False),
        (0.8, 0.9, 0.1, "fault", "task", True),
        (0.8, 0.1, 0.9, "fault", "activity", True),
        (0.1, 0.9, 0.7, "task", "activity", True),
    ],
)
def test_resolver_cases(
    fault_p: float,
    task_p: float,
    activity_p: float,
    expected_primary: str,
    expected_secondary: str,
    expected_review: bool,
) -> None:
    result = resolve_conflict(fault_p, task_p, activity_p)
    assert result.primary_state == expected_primary
    assert result.secondary_tags == expected_secondary
    assert result.review_flag == expected_review
