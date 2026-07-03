from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from heatgrid_ops.replay.scenarios import (
    build_fault_scenarios,
    nearest_replay_time,
    next_replay_time,
    prepare_handoff_scenarios,
)


def test_prepare_handoff_scenarios_filters_to_active_substations() -> None:
    frame = _scenario_frame()

    result = prepare_handoff_scenarios(frame, ["M1_30"])

    assert result["replay_substation_id"].tolist() == ["M1_30", "M1_30"]


def test_nearest_and_next_replay_time_use_available_handoff_windows(monkeypatch) -> None:
    frame = _scenario_frame()
    monkeypatch.setattr("heatgrid_ops.replay.scenarios.available_handoff_frame", lambda active_substations=None: frame)

    nearest = nearest_replay_time(datetime(2020, 3, 14, 22, 0, tzinfo=timezone.utc))
    next_time = next_replay_time(datetime(2020, 3, 15, 0, 0, tzinfo=timezone.utc))

    assert nearest == datetime(2020, 3, 15, 0, 0, tzinfo=timezone.utc)
    assert next_time == datetime(2020, 3, 15, 12, 0, tzinfo=timezone.utc)


def test_build_fault_scenarios_keeps_distinct_fault_groups(monkeypatch) -> None:
    frame = prepare_handoff_scenarios(_scenario_frame(), ["M1_30", "M1_11"])
    monkeypatch.setattr("heatgrid_ops.replay.scenarios.available_handoff_frame", lambda active_substations=None: frame)

    scenarios = build_fault_scenarios(limit=2)

    assert [scenario.fault_group for scenario in scenarios] == ["leakage_water_loss", "valve_actuator"]
    assert scenarios[0].label.startswith("M1_30 · 누수/열손실 · 긴급")


def _scenario_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "manufacturer": "manufacturer 1",
                "substation_id": 30,
                "window_end": "2020-03-15 00:00:00",
                "priority_level": "urgent",
                "m1_specialist_fault_group": "leakage_water_loss",
                "predicted_lead_time_bucket": "0-24h",
                "priority_score": 96.0,
            },
            {
                "manufacturer": "manufacturer 1",
                "substation_id": 30,
                "window_end": "2020-03-15 12:00:00",
                "priority_level": "urgent",
                "m1_specialist_fault_group": "leakage_water_loss",
                "predicted_lead_time_bucket": "0-24h",
                "priority_score": 95.0,
            },
            {
                "manufacturer": "manufacturer 1",
                "substation_id": 11,
                "window_end": "2018-06-30 12:00:00",
                "priority_level": "urgent",
                "m1_specialist_fault_group": "valve_actuator",
                "predicted_lead_time_bucket": "1-3d",
                "priority_score": 94.0,
            },
            {
                "manufacturer": "manufacturer 2",
                "substation_id": 30,
                "window_end": "2020-03-15 00:00:00",
                "priority_level": "urgent",
                "m1_specialist_fault_group": "pump_failure",
                "predicted_lead_time_bucket": "0-24h",
                "priority_score": 99.0,
            },
        ]
    )
