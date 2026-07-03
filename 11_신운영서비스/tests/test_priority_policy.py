from __future__ import annotations

import pytest

from heatgrid_ops.pipeline.priority import leadtime_urgency, semantic_fault_group


def test_leadtime_urgency_bands() -> None:
    assert leadtime_urgency(None) == 0.0
    assert leadtime_urgency(float("nan")) == 0.0
    assert leadtime_urgency(24) == 1.0
    assert leadtime_urgency(72) == 0.7
    assert leadtime_urgency(100) == 0.4


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Pump failure", "pump_failure"),
        ("Leakage in valve", "leakage_water_loss"),
        ("unknown", "unknown_review"),
        ("Differential pressure regulator broken", "pressure_regulator"),
    ],
)
def test_semantic_fault_group(label: str, expected: str) -> None:
    assert semantic_fault_group(label) == expected
