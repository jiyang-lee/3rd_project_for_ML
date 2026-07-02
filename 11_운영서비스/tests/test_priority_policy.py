"""priority 정책 단위테스트 — 기존 m1_fault_dispatch_priority_v1.csv 행 재계산 일치 검증."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from heatgrid_service.pipeline.priority import (  # noqa: E402
    leadtime_urgency,
    priority_score,
    priority_tier,
    semantic_fault_group,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIORITY_CSV = REPO_ROOT / "07_데이터산출물" / "m1_fault_dispatch_priority_v1.csv"


def test_leadtime_urgency_bands():
    assert leadtime_urgency(None) == 0.0
    assert leadtime_urgency(float("nan")) == 0.0
    assert leadtime_urgency(0) == 1.0
    assert leadtime_urgency(24) == 1.0
    assert leadtime_urgency(48) == 0.7
    assert leadtime_urgency(72) == 0.7
    assert leadtime_urgency(100) == 0.4


def test_semantic_fault_group():
    assert semantic_fault_group("Pump failure") == "pump_failure"
    assert semantic_fault_group("Leakage in valve") == "leakage_water_loss"
    assert semantic_fault_group("unknown") == "unknown_review"
    assert semantic_fault_group("Differential pressure regulator broken") == "pressure_regulator"


@pytest.mark.skipif(not PRIORITY_CSV.exists(), reason="priority v1 CSV not available")
def test_priority_rows_recompute():
    df = pd.read_csv(PRIORITY_CSV)
    required = {"risk_probability", "leadtime_urgency", "group_weight", "priority_score", "priority_tier"}
    assert required.issubset(df.columns), f"missing columns: {required - set(df.columns)}"
    for _, row in df.head(20).iterrows():
        score = priority_score(
            float(row["risk_probability"]),
            float(row["leadtime_urgency"]),
            float(row["group_weight"]),
        )
        assert np.isclose(score, float(row["priority_score"]), rtol=1e-9), (
            f"score mismatch: computed={score} expected={row['priority_score']}"
        )
        tier = priority_tier(float(row["risk_probability"]), score)
        assert tier == str(row["priority_tier"]), f"tier mismatch: {tier} != {row['priority_tier']}"
