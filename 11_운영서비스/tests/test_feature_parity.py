"""골든 패리티 테스트: features.py 포팅본이 run_36 산출물과 동일한 compact13 값을 내는지 검증.

기준: 09_실험라인/m1_m2_standard_pre_event/outputs/standard_feature_pool.csv
원본 zip에서 substation CSV를 직접 읽어 재계산 후 np.isclose 비교.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT / "backend"))

from heatgrid_service.features import (  # noqa: E402
    COMPACT13,
    add_derived_signals,
    compute_compact13,
    window_slice,
)

REPO_ROOT = SERVICE_ROOT.parent
GOLDEN_CSV = REPO_ROOT / "09_실험라인" / "m1_m2_standard_pre_event" / "outputs" / "standard_feature_pool.csv"
PREDIST_ZIP = REPO_ROOT / "05_데이터셋" / "PreDist" / "predist_dataset.zip"

pytestmark = pytest.mark.skipif(
    not (GOLDEN_CSV.exists() and PREDIST_ZIP.exists()),
    reason="golden CSV or PreDist zip not available",
)


def load_operational_from_zip(substation_id: int) -> pd.DataFrame:
    name = f"manufacturer 1/operational_data/substation_{substation_id}.csv"
    with zipfile.ZipFile(PREDIST_ZIP) as zf:
        with zf.open(name) as handle:
            df = pd.read_csv(handle, sep=";")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in df.columns:
        if col != "timestamp":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return add_derived_signals(df)


def golden_rows() -> pd.DataFrame:
    df = pd.read_csv(GOLDEN_CSV)
    m1 = df[(df["manufacturer"] == "M1") & (df["coverage_rate"] == 1.0)]
    # normal / fault 라벨을 섞어 3개 window 선택
    picks = pd.concat([m1[m1["label"] == "normal"].head(2), m1[m1["label"] != "normal"].head(1)])
    assert len(picks) == 3
    return picks


@pytest.mark.parametrize("idx", [0, 1, 2])
def test_compact13_parity(idx: int):
    row = golden_rows().iloc[idx]
    ops = load_operational_from_zip(int(row["substation_id"]))
    start = pd.Timestamp(row["window_start"])
    end = pd.Timestamp(row["window_end"])
    window = window_slice(ops, start, end)
    feats = compute_compact13(window, start, end)
    for name in COMPACT13:
        expected = row[name]
        actual = feats[name]
        if pd.isna(expected):
            assert pd.isna(actual), f"{name}: expected NaN, got {actual}"
        else:
            assert np.isclose(actual, float(expected), rtol=1e-9, atol=1e-12), (
                f"{name}: golden={expected} recomputed={actual} (sample={row['sample_id']})"
            )
