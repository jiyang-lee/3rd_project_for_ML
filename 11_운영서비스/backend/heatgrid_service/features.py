"""compact13 피처 계산 — scripts/run_36_m1_m2_standard_pre_event.py 의 함수를 그대로 포팅.

학습 시점과 동일한 결과를 내야 하므로 window 경계(ge/lt), std(ddof=0), NaN 처리
로직을 원본과 다르게 바꾸면 안 된다. 골든 테스트(tests/test_feature_parity.py)가 이를 보증한다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

COMMON10 = [
    "outdoor_temperature",
    "s_hc1_supply_temperature",
    "s_hc1_supply_temperature_setpoint",
    "p_hc1_return_temperature",
    "p_net_meter_energy",
    "p_net_meter_volume",
    "p_net_meter_heat_power",
    "p_net_meter_flow",
    "p_net_supply_temperature",
    "p_net_return_temperature",
]

DHW_OPTIONAL_SIGNALS = [
    "s_dhw_supply_temperature",
    "s_dhw_supply_temperature_setpoint",
    "s_dhw_upper_storage_temperature",
    "s_dhw_lower_storage_temperature",
    "p_dhw_return_temperature",
    "p_dhw_return_temperature_setpoint",
]

# m1_full_gate_runtime_policy_metadata.json — 4개 gate 모두 동일한 13개 피처
COMPACT13 = [
    "outdoor_temperature__last_12h_mean_minus_prev_12h_mean",
    "outdoor_temperature__last_6h_mean_minus_prev_6h_mean",
    "outdoor_temperature__last_minus_first",
    "p_hc1_return_temperature__last_12h_mean_minus_prev_12h_mean",
    "p_hc1_return_temperature__last_1d_mean_minus_prev_6d_mean",
    "p_net_meter_flow__last_1d_std_minus_prev_6d_std",
    "p_net_return_temperature__last_1d_mean_minus_prev_6d_mean",
    "p_return_gap__last_1d_mean_minus_prev_6d_mean",
    "p_return_gap__last_minus_first",
    "s_hc1_supply_temperature__last_1d_mean_minus_prev_6d_mean",
    "s_hc1_supply_temperature__last_1d_std_minus_prev_6d_std",
    "s_hc1_supply_temperature_error__last_minus_first",
    "s_hc1_supply_temperature_setpoint__last_1d_mean_minus_prev_6d_mean",
]


def add_derived_signals(df: pd.DataFrame) -> pd.DataFrame:
    """run_36 load_operational L188-191의 파생신호 계산."""
    df = df.copy()
    for col in [*COMMON10, *DHW_OPTIONAL_SIGNALS]:
        if col not in df.columns:
            df[col] = np.nan
    df["s_hc1_supply_temperature_error"] = df["s_hc1_supply_temperature"] - df["s_hc1_supply_temperature_setpoint"]
    df["p_net_delta_temperature"] = df["p_net_supply_temperature"] - df["p_net_return_temperature"]
    df["p_net_power_flow_ratio"] = df["p_net_meter_heat_power"] / df["p_net_meter_flow"].replace(0, np.nan)
    df["p_return_gap"] = df["p_hc1_return_temperature"] - df["p_net_return_temperature"]
    return df.sort_values("timestamp").reset_index(drop=True)


def expected_count(start, end, seconds: int = 600) -> int:
    return max(0, int(round((pd.Timestamp(end) - pd.Timestamp(start)).total_seconds() / seconds)))


def window_slice(df: pd.DataFrame, start, end) -> pd.DataFrame:
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    return df.loc[df["timestamp"].ge(start) & df["timestamp"].lt(end)].copy()


def last_minus_first(series: pd.Series) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if len(clean) < 2:
        return np.nan
    return float(clean.iloc[-1] - clean.iloc[0])


def period_stat(window: pd.DataFrame, signal: str, start, end, stat: str) -> float:
    subset = pd.to_numeric(
        window.loc[
            window["timestamp"].ge(pd.Timestamp(start)) & window["timestamp"].lt(pd.Timestamp(end)),
            signal,
        ],
        errors="coerce",
    ).dropna()
    if subset.empty:
        return np.nan
    if stat == "mean":
        return float(subset.mean())
    if stat == "std":
        return float(subset.std(ddof=0))
    raise ValueError(stat)


def compute_feature(window: pd.DataFrame, signal: str, stat: str, start, end) -> float:
    if signal not in window.columns:
        return np.nan
    series = pd.to_numeric(window[signal], errors="coerce")
    if stat == "mean":
        return float(series.mean()) if len(series) else np.nan
    if stat == "std":
        return float(series.std(ddof=0)) if len(series) else np.nan
    if stat == "min":
        return float(series.min()) if len(series) else np.nan
    if stat == "max":
        return float(series.max()) if len(series) else np.nan
    if stat == "median":
        return float(series.median()) if len(series) else np.nan
    if stat == "missing_rate":
        return float(series.isna().mean()) if len(series) else 1.0
    if stat == "last_minus_first":
        return last_minus_first(series)
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if stat == "last_1d_mean_minus_prev_6d_mean":
        return period_stat(window, signal, end_ts - pd.Timedelta(days=1), end_ts, "mean") - period_stat(
            window, signal, start_ts, end_ts - pd.Timedelta(days=1), "mean"
        )
    if stat == "last_12h_mean_minus_prev_12h_mean":
        return period_stat(window, signal, end_ts - pd.Timedelta(hours=12), end_ts, "mean") - period_stat(
            window, signal, end_ts - pd.Timedelta(hours=24), end_ts - pd.Timedelta(hours=12), "mean"
        )
    if stat == "last_6h_mean_minus_prev_6h_mean":
        return period_stat(window, signal, end_ts - pd.Timedelta(hours=6), end_ts, "mean") - period_stat(
            window, signal, end_ts - pd.Timedelta(hours=12), end_ts - pd.Timedelta(hours=6), "mean"
        )
    if stat == "last_1d_std_minus_prev_6d_std":
        return period_stat(window, signal, end_ts - pd.Timedelta(days=1), end_ts, "std") - period_stat(
            window, signal, start_ts, end_ts - pd.Timedelta(days=1), "std"
        )
    raise ValueError(stat)


def compute_compact13(window: pd.DataFrame, start, end) -> dict[str, float]:
    """7일 window DataFrame(파생신호 포함)에서 compact13 피처 dict 계산."""
    feats: dict[str, float] = {}
    for name in COMPACT13:
        signal, stat = name.split("__", 1)
        feats[name] = compute_feature(window, signal, stat, start, end)
    return feats


def window_coverage(window: pd.DataFrame, start, end) -> float:
    exp = expected_count(start, end)
    if exp == 0:
        return 0.0
    return float(len(window)) / float(exp)


def system_capability_for_header(header: tuple[str, ...] | list[str]) -> dict[str, object]:
    """run_36 L277-310 그대로."""
    header_set = set(header)
    dhw_supply = any(col in header_set for col in ["s_dhw_supply_temperature", "s_dhw_supply_temperature_setpoint"])
    dhw_storage = any(
        col in header_set
        for col in [
            "s_dhw_upper_storage_temperature",
            "s_dhw_lower_storage_temperature",
            "s_dhw_upper_storage_temperature_setpoint",
        ]
    )
    dhw_return = any(col in header_set for col in ["p_dhw_return_temperature", "p_dhw_return_temperature_setpoint"])
    multi = any("hc1.1" in col or "hc1.2" in col or "hc1.3" in col for col in header_set)
    common10 = all(col in header_set for col in COMMON10)
    if dhw_storage and dhw_return:
        group = "dhw_storage_return"
    elif dhw_storage:
        group = "dhw_storage"
    elif dhw_supply:
        group = "dhw_supply"
    elif dhw_return:
        group = "dhw_return"
    elif multi:
        group = "multi_circuit"
    else:
        group = "heating_common_only"
    return {
        "common10_ready": common10,
        "dhw_supply_available": dhw_supply,
        "dhw_storage_available": dhw_storage,
        "dhw_return_available": dhw_return,
        "multi_circuit_available": multi,
        "system_capability_group": group,
    }
