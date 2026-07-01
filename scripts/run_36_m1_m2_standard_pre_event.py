from __future__ import annotations

import argparse
import json
import subprocess
import warnings
import zipfile
from functools import lru_cache
from pathlib import Path

import nbformat as nbf
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")

try:
    from lightgbm import LGBMClassifier
except Exception:  # pragma: no cover - optional dependency
    LGBMClassifier = None

try:
    from xgboost import XGBClassifier
except Exception:  # pragma: no cover - optional dependency
    XGBClassifier = None

RANDOM_STATE = 42
COVERAGE_MIN = 0.95
THRESHOLDS = [0.4, 0.5, 0.6]
DEFAULT_THRESHOLD = 0.6

MANUFACTURERS = {
    "M1": {
        "meta": "manufacturer_1",
        "zip_prefix": "manufacturer 1",
        "special_events": {20: "low_coverage", 34: "unknown_fault_label", 67: "long_anomaly", 69: "unknown_or_metadata_review"},
        "hard_normal_events": {19, 35, 48, 68},
    },
    "M2": {
        "meta": "manufacturer_2",
        "zip_prefix": "manufacturer 2",
        "special_events": {},
        "hard_normal_events": set(),
    },
}

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

BASE_STATS = ["mean", "std", "min", "max", "median", "last_minus_first", "missing_rate"]
DERIVED_SIGNALS = [
    "s_hc1_supply_temperature_error",
    "p_net_delta_temperature",
    "p_net_power_flow_ratio",
    "p_return_gap",
]
DHW_OPTIONAL_SIGNALS = [
    "s_dhw_supply_temperature",
    "s_dhw_supply_temperature_setpoint",
    "s_dhw_upper_storage_temperature",
    "s_dhw_lower_storage_temperature",
    "p_dhw_return_temperature",
    "p_dhw_return_temperature_setpoint",
]

SYSTEM_TAG_COLUMNS = [
    "common10_ready",
    "dhw_supply_available",
    "dhw_storage_available",
    "dhw_return_available",
    "multi_circuit_available",
    "system_capability_group",
]


def repo_paths() -> dict[str, Path]:
    root = Path.cwd()
    return {
        "root": root,
        "data": root / "05_데이터셋" / "PreDist",
        "zip": root / "05_데이터셋" / "PreDist" / "predist_dataset.zip",
        "legacy_out": root / "07_데이터산출물",
        "line": root / "09_실험라인" / "m1_m2_standard_pre_event",
    }


PATHS = repo_paths()
NOTEBOOK_DIR = PATHS["line"] / "notebooks"
OUTPUT_DIR = PATHS["line"] / "outputs"
REPORT_DIR = PATHS["line"] / "reports"


def ensure_dirs() -> None:
    for path in [NOTEBOOK_DIR, OUTPUT_DIR, REPORT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def source_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PATHS["root"], text=True).strip()
    except Exception:
        return "unknown"


def md_table(df: pd.DataFrame, columns: list[str] | None = None, max_rows: int | None = None) -> str:
    view = df.copy()
    if columns is not None:
        view = view[columns]
    if max_rows is not None:
        view = view.head(max_rows)
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.4f}")
        else:
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else str(x))
    lines = ["| " + " | ".join(view.columns) + " |", "| " + " | ".join(["---"] * len(view.columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "\\|") for col in view.columns) + " |")
    return "\n".join(lines)


def read_meta(manufacturer: str, filename: str) -> pd.DataFrame:
    path = PATHS["data"] / "metadata" / MANUFACTURERS[manufacturer]["meta"] / filename
    return pd.read_csv(path, sep=";")


def zip_names() -> set[str]:
    with zipfile.ZipFile(PATHS["zip"]) as zf:
        return set(zf.namelist())


@lru_cache(maxsize=256)
def operational_header(manufacturer: str, substation_id: int) -> tuple[str, ...]:
    prefix = MANUFACTURERS[manufacturer]["zip_prefix"]
    name = f"{prefix}/operational_data/substation_{int(substation_id)}.csv"
    with zipfile.ZipFile(PATHS["zip"]) as zf:
        if name not in set(zf.namelist()):
            return tuple()
        with zf.open(name) as handle:
            header = pd.read_csv(handle, sep=";", nrows=0)
    return tuple(header.columns)


@lru_cache(maxsize=256)
def load_operational(manufacturer: str, substation_id: int) -> pd.DataFrame:
    prefix = MANUFACTURERS[manufacturer]["zip_prefix"]
    name = f"{prefix}/operational_data/substation_{int(substation_id)}.csv"
    with zipfile.ZipFile(PATHS["zip"]) as zf:
        if name not in set(zf.namelist()):
            columns = ["timestamp", *COMMON10, *DHW_OPTIONAL_SIGNALS]
            return pd.DataFrame(columns=columns)
        with zf.open(name) as handle:
            df = pd.read_csv(handle, sep=";")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in df.columns:
        if col != "timestamp":
            df[col] = pd.to_numeric(df[col], errors="coerce")
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


def parse_compact13_features() -> list[str]:
    path = PATHS["legacy_out"] / "m1_compact_feature_set_summary.csv"
    df = pd.read_csv(path)
    row = df.loc[df["feature_set"].eq("compact13_overlap")]
    if len(row) != 1:
        raise ValueError("compact13_overlap feature set not found")
    return [feature for feature in str(row.iloc[0]["features"]).split("|") if feature]


def system_capability_for_header(header: tuple[str, ...]) -> dict[str, object]:
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


def build_system_capability_audit() -> pd.DataFrame:
    rows = []
    for manufacturer in MANUFACTURERS:
        normal = read_meta(manufacturer, "normal_events.csv")
        faults = read_meta(manufacturer, "faults.csv")
        disturbances = read_meta(manufacturer, "disturbances.csv")
        substation_ids = sorted(
            set(normal["substation ID"].dropna().astype(int))
            | set(faults["substation ID"].dropna().astype(int))
            | set(disturbances["substation ID"].dropna().astype(int))
        )
        for sid in substation_ids:
            header = operational_header(manufacturer, sid)
            capability = system_capability_for_header(header)
            rows.append(
                {
                    "manufacturer": manufacturer,
                    "substation_id": sid,
                    "manufacturer_substation_id": f"{manufacturer}_{sid}",
                    "raw_column_count": len(header),
                    "raw_sensor_columns": "|".join([c for c in header if c != "timestamp"]),
                    "normal_event_count": int(normal["substation ID"].eq(sid).sum()),
                    "fault_event_count": int(faults["substation ID"].eq(sid).sum()),
                    "efd_possible_count": int(
                        faults.loc[faults["substation ID"].eq(sid), "efd_possible"].astype(str).str.lower().eq("true").sum()
                    ),
                    "disturbance_count": int(disturbances["substation ID"].eq(sid).sum()),
                    **capability,
                }
            )
    return pd.DataFrame(rows)


def build_standard_sensor_schema(system_audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    all_headers: dict[str, set[str]] = {}
    for manufacturer in MANUFACTURERS:
        headers = set()
        for sid in system_audit.loc[system_audit["manufacturer"].eq(manufacturer), "substation_id"]:
            headers.update(operational_header(manufacturer, int(sid)))
        all_headers[manufacturer] = headers
    for concept in COMMON10:
        rows.append(
            {
                "sensor_concept": concept,
                "canonical_column": concept,
                "schema_role": "required",
                "missing_allowed": False,
                "system_specific": False,
                "m1_available": concept in all_headers["M1"],
                "m2_available": concept in all_headers["M2"],
                "feature_policy": "standard_common_and_common13_source",
            }
        )
    for concept in DERIVED_SIGNALS:
        rows.append(
            {
                "sensor_concept": concept,
                "canonical_column": concept,
                "schema_role": "derived_required_from_common10",
                "missing_allowed": False,
                "system_specific": False,
                "m1_available": True,
                "m2_available": True,
                "feature_policy": "derived_for_common13_temporal_features",
            }
        )
    for concept in DHW_OPTIONAL_SIGNALS:
        rows.append(
            {
                "sensor_concept": concept,
                "canonical_column": concept,
                "schema_role": "optional",
                "missing_allowed": True,
                "system_specific": True,
                "m1_available": concept in all_headers["M1"],
                "m2_available": concept in all_headers["M2"],
                "feature_policy": "standard_optional_dhw_subset_only",
            }
        )
    return pd.DataFrame(rows)


def event_flags(manufacturer: str, row: pd.Series, coverage_rate: float) -> dict[str, object]:
    event_id = int(row["Event ID"]) if "Event ID" in row and pd.notna(row["Event ID"]) else -1
    fault_label = str(row.get("Fault label", "")).strip()
    report_date = pd.to_datetime(row.get("Report date"), errors="coerce")
    possible_start = pd.to_datetime(row.get("Possible anomaly start"), errors="coerce")
    training_end = pd.to_datetime(row.get("Training end"), errors="coerce")
    anomaly_start_to_report_days = np.nan
    if pd.notna(possible_start) and pd.notna(report_date):
        anomaly_start_to_report_days = (report_date - possible_start).total_seconds() / 86400
    special_reason = MANUFACTURERS[manufacturer]["special_events"].get(event_id, "")
    unknown = fault_label.lower() in {"", "nan", "unknown"}
    training_missing = pd.isna(training_end)
    long_anomaly = bool(pd.notna(anomaly_start_to_report_days) and anomaly_start_to_report_days > 90)
    return {
        "fault_label": fault_label,
        "fault_label_unknown": unknown,
        "training_end_missing": training_missing,
        "low_coverage_flag": bool(coverage_rate < COVERAGE_MIN),
        "long_anomaly_flag": long_anomaly,
        "anomaly_metadata_missing": bool(pd.isna(possible_start)),
        "anomaly_start_to_report_days": anomaly_start_to_report_days,
        "special_event_reason": special_reason,
    }


def compute_features_for_window(manufacturer: str, substation_id: int, start, end, feature_names: list[str]) -> tuple[dict, int, int, float]:
    df = load_operational(manufacturer, int(substation_id))
    window = window_slice(df, start, end)
    values = {}
    for feature in feature_names:
        signal, stat = feature.split("__", 1)
        values[feature] = compute_feature(window, signal, stat, start, end)
    exp_count = expected_count(start, end)
    sample_count = int(len(window))
    coverage = sample_count / exp_count if exp_count else 0
    return values, sample_count, exp_count, coverage


def all_raw_feature_names() -> dict[str, list[str]]:
    compact13 = parse_compact13_features()
    standard_common = [f"{signal}__{stat}" for signal in COMMON10 for stat in BASE_STATS]
    optional_dhw = [f"{signal}__{stat}" for signal in DHW_OPTIONAL_SIGNALS for stat in BASE_STATS]
    all_features = list(dict.fromkeys([*compact13, *standard_common, *optional_dhw]))
    return {
        "common13": compact13,
        "standard_common": standard_common,
        "standard_optional_dhw": [*standard_common, *optional_dhw],
        "all_raw": all_features,
    }


def build_dataset_and_features(system_audit: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_names = all_raw_feature_names()
    all_raw = feature_names["all_raw"]
    system_lookup = system_audit.set_index(["manufacturer", "substation_id"]).to_dict("index")
    index_rows = []
    feature_rows = []
    for manufacturer in MANUFACTURERS:
        normal = read_meta(manufacturer, "normal_events.csv")
        faults = read_meta(manufacturer, "faults.csv")
        for _, row in normal.iterrows():
            sid = int(row["substation ID"])
            start = pd.Timestamp(row["Event start"])
            end = pd.Timestamp(row["Event end"])
            features, sample_count, expected, coverage = compute_features_for_window(manufacturer, sid, start, end, all_raw)
            cap = system_lookup.get((manufacturer, sid), {})
            event_id = int(row["Event ID"])
            main_eligible = bool(coverage >= COVERAGE_MIN and cap.get("common10_ready", False))
            base = {
                "sample_id": f"{manufacturer}_normal_{event_id:04d}",
                "manufacturer": manufacturer,
                "event_source": "normal_events",
                "source_event_id": event_id,
                "substation_id": sid,
                "manufacturer_substation_id": f"{manufacturer}_{sid}",
                "label": "normal",
                "y": 0,
                "window_policy": "normal_event_7d",
                "window_start": start,
                "window_end": end,
                "sample_count": sample_count,
                "expected_sample_count": expected,
                "coverage_rate": coverage,
                "main_eligible": main_eligible,
                "sensitivity_no_long_anomaly_eligible": main_eligible,
                "exclude_reason": "" if main_eligible else "low_coverage_or_common10_missing",
                "hard_normal_metadata": event_id in MANUFACTURERS[manufacturer]["hard_normal_events"],
                "pre_event_eligible": False,
                "fault_label": "",
                "fault_label_unknown": False,
                "training_end_missing": False,
                "low_coverage_flag": coverage < COVERAGE_MIN,
                "long_anomaly_flag": False,
                "anomaly_metadata_missing": False,
                "anomaly_start_to_report_days": np.nan,
                "special_event_reason": "",
                **{col: cap.get(col, np.nan) for col in SYSTEM_TAG_COLUMNS},
            }
            index_rows.append(base)
            feature_rows.append({**base, **features})
        faults = faults.copy()
        faults["efd_possible_bool"] = faults["efd_possible"].astype(str).str.lower().eq("true")
        faults = faults.loc[faults["efd_possible_bool"] & faults["Report date"].notna()].copy()
        for _, row in faults.iterrows():
            sid = int(row["substation ID"])
            event_id = int(row["Event ID"])
            end = pd.Timestamp(row["Report date"])
            start = end - pd.Timedelta(days=7)
            features, sample_count, expected, coverage = compute_features_for_window(manufacturer, sid, start, end, all_raw)
            cap = system_lookup.get((manufacturer, sid), {})
            flags = event_flags(manufacturer, row, coverage)
            exclude_reasons = []
            if coverage < COVERAGE_MIN:
                exclude_reasons.append("low_coverage")
            if not cap.get("common10_ready", False):
                exclude_reasons.append("common10_missing")
            if flags["fault_label_unknown"]:
                exclude_reasons.append("unknown_fault_label")
            if flags["training_end_missing"]:
                exclude_reasons.append("training_end_missing")
            main_eligible = len(exclude_reasons) == 0
            no_long = main_eligible and not flags["long_anomaly_flag"]
            base = {
                "sample_id": f"{manufacturer}_pre_event_{event_id:04d}",
                "manufacturer": manufacturer,
                "event_source": "faults",
                "source_event_id": event_id,
                "substation_id": sid,
                "manufacturer_substation_id": f"{manufacturer}_{sid}",
                "label": "pre_event",
                "y": 1,
                "window_policy": "report_pre_7d",
                "window_start": start,
                "window_end": end,
                "sample_count": sample_count,
                "expected_sample_count": expected,
                "coverage_rate": coverage,
                "main_eligible": main_eligible,
                "sensitivity_no_long_anomaly_eligible": no_long,
                "exclude_reason": "|".join(exclude_reasons),
                "hard_normal_metadata": False,
                "pre_event_eligible": True,
                **flags,
                **{col: cap.get(col, np.nan) for col in SYSTEM_TAG_COLUMNS},
            }
            index_rows.append(base)
            feature_rows.append({**base, **features})
    index = pd.DataFrame(index_rows)
    features = pd.DataFrame(feature_rows)
    for col in ["window_start", "window_end"]:
        index[col] = pd.to_datetime(index[col]).dt.strftime("%Y-%m-%d %H:%M:%S")
        features[col] = pd.to_datetime(features[col]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return index, features


def feature_sets(feature_pool: pd.DataFrame) -> dict[str, list[str]]:
    names = all_raw_feature_names()
    groups = sorted(feature_pool["system_capability_group"].dropna().astype(str).unique())
    group_cols = [f"system_group__{group}" for group in groups]
    for group in groups:
        feature_pool[f"system_group__{group}"] = feature_pool["system_capability_group"].astype(str).eq(group).astype(int)
    system_binary = [
        "common10_ready",
        "dhw_supply_available",
        "dhw_storage_available",
        "dhw_return_available",
        "multi_circuit_available",
    ]
    for col in system_binary:
        feature_pool[col] = feature_pool[col].astype(bool).astype(int)
    return {
        "common13": names["common13"],
        "standard_common": names["standard_common"],
        "standard_common_plus_system": [*names["standard_common"], *system_binary, *group_cols],
        "standard_optional_dhw": names["standard_optional_dhw"],
    }


def make_model(name: str, y_train: pd.Series | None = None) -> Pipeline:
    if name == "dummy_most_frequent":
        estimator = DummyClassifier(strategy="most_frequent")
        scale = False
    elif name == "logistic_balanced":
        estimator = LogisticRegression(class_weight="balanced", solver="liblinear", random_state=RANDOM_STATE, max_iter=1000)
        scale = True
    elif name == "random_forest_depth3":
        estimator = RandomForestClassifier(
            n_estimators=160, max_depth=3, class_weight="balanced", random_state=RANDOM_STATE, min_samples_leaf=2
        )
        scale = False
    elif name == "random_forest_depth5":
        estimator = RandomForestClassifier(
            n_estimators=160, max_depth=5, class_weight="balanced", random_state=RANDOM_STATE, min_samples_leaf=2
        )
        scale = False
    elif name == "extra_trees_depth3":
        estimator = ExtraTreesClassifier(
            n_estimators=160, max_depth=3, class_weight="balanced", random_state=RANDOM_STATE, min_samples_leaf=2
        )
        scale = False
    elif name == "extra_trees_depth5":
        estimator = ExtraTreesClassifier(
            n_estimators=160, max_depth=5, class_weight="balanced", random_state=RANDOM_STATE, min_samples_leaf=2
        )
        scale = False
    elif name == "hist_gradient_boosting":
        estimator = HistGradientBoostingClassifier(max_iter=80, learning_rate=0.05, max_leaf_nodes=8, random_state=RANDOM_STATE)
        scale = False
    elif name == "lightgbm_depth3" and LGBMClassifier is not None:
        estimator = LGBMClassifier(
            n_estimators=80,
            learning_rate=0.05,
            max_depth=3,
            num_leaves=7,
            min_child_samples=3,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            verbose=-1,
        )
        scale = False
    elif name == "xgboost_depth3" and XGBClassifier is not None:
        scale_pos_weight = 1.0
        if y_train is not None and int(y_train.sum()) > 0:
            scale_pos_weight = max(1.0, float((len(y_train) - int(y_train.sum())) / int(y_train.sum())))
        estimator = XGBClassifier(
            n_estimators=80,
            learning_rate=0.05,
            max_depth=3,
            min_child_weight=1,
            subsample=0.9,
            colsample_bytree=0.9,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=RANDOM_STATE,
        )
        scale = False
    else:
        raise ValueError(f"model unavailable: {name}")
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", estimator))
    return Pipeline(steps)


def available_model_names() -> list[str]:
    names = [
        "dummy_most_frequent",
        "logistic_balanced",
        "random_forest_depth3",
        "random_forest_depth5",
        "extra_trees_depth3",
        "extra_trees_depth5",
        "hist_gradient_boosting",
    ]
    if LGBMClassifier is not None:
        names.append("lightgbm_depth3")
    if XGBClassifier is not None:
        names.append("xgboost_depth3")
    return names


def class_one_probability(model: Pipeline, x: pd.DataFrame) -> np.ndarray:
    classes = list(model.named_steps["model"].classes_)
    probs = model.predict_proba(x)
    if 1 not in classes:
        return np.zeros(len(x))
    return probs[:, classes.index(1)]


def metric_row(scope: str, feature_set_name: str, model_name: str, threshold: float, y_true, prob, rows: int) -> dict:
    pred = (np.asarray(prob) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, pred, labels=[1], average="binary", zero_division=0)
    return {
        "evaluation_scope": scope,
        "feature_set": feature_set_name,
        "model": model_name,
        "threshold": threshold,
        "rows": int(rows),
        "normal_rows": int((np.asarray(y_true) == 0).sum()),
        "pre_event_rows": int((np.asarray(y_true) == 1).sum()),
        "balanced_accuracy": balanced_accuracy_score(y_true, pred),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "normal_fpr": fp / (fp + tn) if (fp + tn) else np.nan,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def class_metric_rows(scope: str, feature_set_name: str, model_name: str, threshold: float, y_true, prob) -> list[dict]:
    pred = (np.asarray(prob) >= threshold).astype(int)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, pred, labels=[0, 1], zero_division=0
    )
    return [
        {
            "evaluation_scope": scope,
            "feature_set": feature_set_name,
            "model": model_name,
            "threshold": threshold,
            "class": "normal" if label == 0 else "pre_event",
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "support": int(support[i]),
        }
        for i, label in enumerate([0, 1])
    ]


def confusion_rows(scope: str, feature_set_name: str, model_name: str, threshold: float, y_true, prob) -> list[dict]:
    pred = (np.asarray(prob) >= threshold).astype(int)
    cm = confusion_matrix(y_true, pred, labels=[0, 1])
    rows = []
    for i, actual in enumerate([0, 1]):
        for j, predicted in enumerate([0, 1]):
            rows.append(
                {
                    "evaluation_scope": scope,
                    "feature_set": feature_set_name,
                    "model": model_name,
                    "threshold": threshold,
                    "actual": actual,
                    "predicted": predicted,
                    "count": int(cm[i, j]),
                }
            )
    return rows


def can_evaluate(data: pd.DataFrame) -> bool:
    return len(data) >= 4 and data["y"].nunique() == 2 and data["manufacturer_substation_id"].nunique() >= 2


def run_fit_predict(train: pd.DataFrame, test: pd.DataFrame, features: list[str], model_name: str) -> tuple[np.ndarray, str]:
    try:
        model = make_model(model_name, train["y"].astype(int))
        model.fit(train[features], train["y"].astype(int))
        return class_one_probability(model, test[features]), ""
    except Exception as exc:
        return np.full(len(test), np.nan), str(exc)


def cv_predictions(data: pd.DataFrame, scope: str, features: list[str], feature_set_name: str, model_name: str) -> tuple[list[dict], list[dict]]:
    if not can_evaluate(data):
        return [], [
            {
                "evaluation_scope": scope,
                "feature_set": feature_set_name,
                "model": model_name,
                "quality_check": "skipped_insufficient_data",
                "passed": False,
                "detail": f"rows={len(data)}, labels={data['y'].nunique()}",
            }
        ]
    min_class = int(data["y"].value_counts().min())
    n_splits = max(2, min(5, min_class, data["manufacturer_substation_id"].nunique()))
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    pred_rows = []
    qa_rows = []
    for fold, (train_idx, test_idx) in enumerate(
        sgkf.split(data[features], data["y"].astype(int), data["manufacturer_substation_id"]), start=1
    ):
        train = data.iloc[train_idx].copy()
        test = data.iloc[test_idx].copy()
        overlap = sorted(set(train["manufacturer_substation_id"]) & set(test["manufacturer_substation_id"]))
        prob, error = run_fit_predict(train, test, features, model_name)
        qa_rows.append(
            {
                "evaluation_scope": scope,
                "feature_set": feature_set_name,
                "model": model_name,
                "fold": fold,
                "quality_check": "train_test_group_overlap_zero",
                "passed": len(overlap) == 0,
                "detail": "|".join(overlap) if overlap else "",
            }
        )
        if error:
            qa_rows.append(
                {
                    "evaluation_scope": scope,
                    "feature_set": feature_set_name,
                    "model": model_name,
                    "fold": fold,
                    "quality_check": "model_fit_predict",
                    "passed": False,
                    "detail": error[:300],
                }
            )
            continue
        for row, p in zip(test.to_dict("records"), prob):
            pred_rows.append(
                {
                    "evaluation_scope": scope,
                    "feature_set": feature_set_name,
                    "model": model_name,
                    "fold": fold,
                    "sample_id": row["sample_id"],
                    "manufacturer": row["manufacturer"],
                    "source_event_id": row["source_event_id"],
                    "substation_id": row["substation_id"],
                    "manufacturer_substation_id": row["manufacturer_substation_id"],
                    "label": row["label"],
                    "y_true": int(row["y"]),
                    "probability": float(p),
                }
            )
    return pred_rows, qa_rows


def holdout_predictions(train: pd.DataFrame, test: pd.DataFrame, scope: str, features: list[str], feature_set_name: str, model_name: str) -> tuple[list[dict], list[dict]]:
    if not can_evaluate(train) or test["y"].nunique() < 2:
        return [], [
            {
                "evaluation_scope": scope,
                "feature_set": feature_set_name,
                "model": model_name,
                "quality_check": "skipped_insufficient_train_or_test",
                "passed": False,
                "detail": f"train_rows={len(train)}, test_rows={len(test)}",
            }
        ]
    overlap = sorted(set(train["manufacturer_substation_id"]) & set(test["manufacturer_substation_id"]))
    prob, error = run_fit_predict(train, test, features, model_name)
    qa_rows = [
        {
            "evaluation_scope": scope,
            "feature_set": feature_set_name,
            "model": model_name,
            "quality_check": "train_test_group_overlap_zero",
            "passed": len(overlap) == 0,
            "detail": "|".join(overlap) if overlap else "",
        }
    ]
    if error:
        qa_rows.append(
            {
                "evaluation_scope": scope,
                "feature_set": feature_set_name,
                "model": model_name,
                "quality_check": "model_fit_predict",
                "passed": False,
                "detail": error[:300],
            }
        )
        return [], qa_rows
    pred_rows = []
    for row, p in zip(test.to_dict("records"), prob):
        pred_rows.append(
            {
                "evaluation_scope": scope,
                "feature_set": feature_set_name,
                "model": model_name,
                "fold": "holdout",
                "sample_id": row["sample_id"],
                "manufacturer": row["manufacturer"],
                "source_event_id": row["source_event_id"],
                "substation_id": row["substation_id"],
                "manufacturer_substation_id": row["manufacturer_substation_id"],
                "label": row["label"],
                "y_true": int(row["y"]),
                "probability": float(p),
            }
        )
    return pred_rows, qa_rows


def build_trainable_sets(feature_pool: pd.DataFrame) -> dict[str, pd.DataFrame]:
    main = feature_pool.loc[feature_pool["main_eligible"].astype(bool)].copy()
    no_long = feature_pool.loc[feature_pool["sensitivity_no_long_anomaly_eligible"].astype(bool)].copy()
    return {
        "main": main,
        "sensitivity_no_long_anomaly": no_long,
    }


def evaluate_models(feature_pool: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    set_map = feature_sets(feature_pool)
    trainable = build_trainable_sets(feature_pool)
    main = trainable["main"].copy()
    rows_for_optional = main.loc[
        main[["dhw_supply_available", "dhw_storage_available", "dhw_return_available"]].astype(bool).any(axis=1)
    ].copy()
    datasets = {
        "M1_CV": main.loc[main["manufacturer"].eq("M1")].copy(),
        "M2_CV": main.loc[main["manufacturer"].eq("M2")].copy(),
        "Pooled_M1_M2_group_CV": main.copy(),
    }
    predictions = []
    qa_rows = []
    for feature_set_name, feature_list in set_map.items():
        dataset_source = datasets
        if feature_set_name == "standard_optional_dhw":
            if len(rows_for_optional) < 20 or rows_for_optional["y"].value_counts().min() < 10:
                qa_rows.append(
                    {
                        "evaluation_scope": "all",
                        "feature_set": feature_set_name,
                        "model": "all",
                        "quality_check": "standard_optional_dhw_feasibility",
                        "passed": False,
                        "detail": f"rows={len(rows_for_optional)}, label_counts={rows_for_optional['y'].value_counts().to_dict()}",
                    }
                )
                continue
            dataset_source = {
                "M1_CV": rows_for_optional.loc[rows_for_optional["manufacturer"].eq("M1")].copy(),
                "M2_CV": rows_for_optional.loc[rows_for_optional["manufacturer"].eq("M2")].copy(),
                "Pooled_M1_M2_group_CV": rows_for_optional.copy(),
            }
        for model_name in available_model_names():
            for scope, data in dataset_source.items():
                pred, qa = cv_predictions(data, scope, feature_list, feature_set_name, model_name)
                predictions.extend(pred)
                qa_rows.extend(qa)
            train_m1 = dataset_source.get("M1_CV", pd.DataFrame())
            train_m2 = dataset_source.get("M2_CV", pd.DataFrame())
            pred, qa = holdout_predictions(train_m1, train_m2, "M1_to_M2", feature_list, feature_set_name, model_name)
            predictions.extend(pred)
            qa_rows.extend(qa)
            pred, qa = holdout_predictions(train_m2, train_m1, "M2_to_M1", feature_list, feature_set_name, model_name)
            predictions.extend(pred)
            qa_rows.extend(qa)
    pred_df = pd.DataFrame(predictions)
    qa_df = pd.DataFrame(qa_rows)
    metric_rows = []
    class_rows = []
    confusion = []
    if not pred_df.empty:
        for keys, group in pred_df.groupby(["evaluation_scope", "feature_set", "model"], dropna=False):
            scope, feature_set_name, model_name = keys
            y_true = group["y_true"].astype(int).to_numpy()
            prob = group["probability"].astype(float).to_numpy()
            if np.isnan(prob).any():
                continue
            for threshold in THRESHOLDS:
                metric_rows.append(metric_row(scope, feature_set_name, model_name, threshold, y_true, prob, len(group)))
                class_rows.extend(class_metric_rows(scope, feature_set_name, model_name, threshold, y_true, prob))
                confusion.extend(confusion_rows(scope, feature_set_name, model_name, threshold, y_true, prob))
    metrics = pd.DataFrame(metric_rows)
    class_metrics = pd.DataFrame(class_rows)
    confusion_df = pd.DataFrame(confusion)
    leave = metrics.loc[metrics["evaluation_scope"].isin(["M1_to_M2", "M2_to_M1"])].copy()
    return pred_df, metrics, leave, class_metrics, confusion_df, qa_df


def build_dataset_summary(index: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope_name, data in {
        "all_index": index,
        "main_eligible": index.loc[index["main_eligible"].astype(bool)],
        "sensitivity_no_long_anomaly": index.loc[index["sensitivity_no_long_anomaly_eligible"].astype(bool)],
    }.items():
        for manufacturer, group in data.groupby("manufacturer"):
            rows.append(
                {
                    "scope": scope_name,
                    "manufacturer": manufacturer,
                    "rows": len(group),
                    "normal_rows": int(group["y"].eq(0).sum()),
                    "pre_event_rows": int(group["y"].eq(1).sum()),
                    "substation_count": int(group["manufacturer_substation_id"].nunique()),
                    "coverage_median": float(group["coverage_rate"].median()) if len(group) else np.nan,
                    "excluded_rows": int((~group["main_eligible"].astype(bool)).sum()) if scope_name == "all_index" else 0,
                }
            )
    return pd.DataFrame(rows)


def build_decision_matrix(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return pd.DataFrame()
    rows = []
    for (feature_set_name, model_name, threshold), group in metrics.groupby(["feature_set", "model", "threshold"]):
        lookup = {row["evaluation_scope"]: row for _, row in group.iterrows()}
        required_scopes = ["M1_to_M2", "M2_to_M1", "Pooled_M1_M2_group_CV"]
        if not all(scope in lookup for scope in required_scopes):
            continue
        m1_to_m2 = lookup["M1_to_M2"]
        m2_to_m1 = lookup["M2_to_M1"]
        pooled = lookup["Pooled_M1_M2_group_CV"]
        min_leave_ba = min(float(m1_to_m2["balanced_accuracy"]), float(m2_to_m1["balanced_accuracy"]))
        max_leave_gap = abs(float(m1_to_m2["balanced_accuracy"]) - float(m2_to_m1["balanced_accuracy"]))
        min_recall = min(float(m1_to_m2["recall"]), float(m2_to_m1["recall"]), float(pooled["recall"]))
        max_fpr = max(float(m1_to_m2["normal_fpr"]), float(m2_to_m1["normal_fpr"]), float(pooled["normal_fpr"]))
        m2_fpr_improved = float(m1_to_m2["normal_fpr"]) < 0.60
        standardizable = (
            min_leave_ba >= 0.60
            and max_leave_gap <= 0.25
            and min_recall >= 0.70
            and max_fpr <= 0.25
            and m2_fpr_improved
        )
        if standardizable and feature_set_name == "standard_common_plus_system":
            decision = "system_aware_model_candidate"
        elif standardizable and feature_set_name == "standard_optional_dhw":
            decision = "dhw_aux_model_candidate"
        elif standardizable:
            decision = "standard_common_model_ready"
        elif min_recall < 0.70 or max_fpr > 0.25:
            decision = "label_window_recheck_required"
        else:
            decision = "model_not_standardizable_yet"
        rows.append(
            {
                "feature_set": feature_set_name,
                "model": model_name,
                "threshold": threshold,
                "m1_to_m2_balanced_accuracy": float(m1_to_m2["balanced_accuracy"]),
                "m2_to_m1_balanced_accuracy": float(m2_to_m1["balanced_accuracy"]),
                "pooled_balanced_accuracy": float(pooled["balanced_accuracy"]),
                "min_leave_manufacturer_ba": min_leave_ba,
                "leave_manufacturer_ba_gap": max_leave_gap,
                "min_recall": min_recall,
                "max_normal_fpr": max_fpr,
                "m2_normal_fpr_vs_old_0_60": float(m1_to_m2["normal_fpr"]),
                "m2_fpr_improved_vs_old_failure": m2_fpr_improved,
                "candidate_pass": standardizable,
                "decision": decision,
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["rank_key"] = (
        out["candidate_pass"].astype(int) * 100
        + out["min_leave_manufacturer_ba"]
        + out["min_recall"]
        - out["max_normal_fpr"]
    )
    return out.sort_values(["candidate_pass", "rank_key"], ascending=[False, False]).drop(columns=["rank_key"])


def independent_metric_recheck(predictions: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if predictions.empty or metrics.empty:
        return pd.DataFrame(rows)
    for _, row in metrics.iterrows():
        pred = predictions.loc[
            predictions["evaluation_scope"].eq(row["evaluation_scope"])
            & predictions["feature_set"].eq(row["feature_set"])
            & predictions["model"].eq(row["model"])
        ]
        if pred.empty:
            continue
        recalculated = metric_row(
            row["evaluation_scope"],
            row["feature_set"],
            row["model"],
            float(row["threshold"]),
            pred["y_true"].astype(int).to_numpy(),
            pred["probability"].astype(float).to_numpy(),
            len(pred),
        )
        rows.append(
            {
                "evaluation_scope": row["evaluation_scope"],
                "feature_set": row["feature_set"],
                "model": row["model"],
                "threshold": row["threshold"],
                "balanced_accuracy_match": abs(row["balanced_accuracy"] - recalculated["balanced_accuracy"]) < 1e-12,
                "recall_match": abs(row["recall"] - recalculated["recall"]) < 1e-12,
                "normal_fpr_match": abs(row["normal_fpr"] - recalculated["normal_fpr"]) < 1e-12,
            }
        )
    return pd.DataFrame(rows)


def write_outputs() -> None:
    ensure_dirs()
    system = build_system_capability_audit()
    schema = build_standard_sensor_schema(system)
    index, pool = build_dataset_and_features(system)
    fs = feature_sets(pool)
    dataset_summary = build_dataset_summary(index)
    predictions, metrics, leave, class_metrics, confusion, qa = evaluate_models(pool)
    decision = build_decision_matrix(metrics)
    recheck = independent_metric_recheck(predictions, metrics)

    schema.to_csv(OUTPUT_DIR / "standard_sensor_schema.csv", index=False, encoding="utf-8-sig")
    system.to_csv(OUTPUT_DIR / "system_capability_audit.csv", index=False, encoding="utf-8-sig")
    index.to_csv(OUTPUT_DIR / "pre_event_dataset_index.csv", index=False, encoding="utf-8-sig")
    pool.to_csv(OUTPUT_DIR / "standard_feature_pool.csv", index=False, encoding="utf-8-sig")
    dataset_summary.to_csv(OUTPUT_DIR / "pre_event_dataset_summary.csv", index=False, encoding="utf-8-sig")
    metrics.loc[metrics["threshold"].eq(DEFAULT_THRESHOLD)].to_csv(
        OUTPUT_DIR / "model_selection_metrics.csv", index=False, encoding="utf-8-sig"
    )
    leave.to_csv(OUTPUT_DIR / "leave_manufacturer_out_metrics.csv", index=False, encoding="utf-8-sig")
    metrics.to_csv(OUTPUT_DIR / "calibration_threshold_audit.csv", index=False, encoding="utf-8-sig")
    predictions.to_csv(OUTPUT_DIR / "model_selection_predictions.csv", index=False, encoding="utf-8-sig")
    class_metrics.to_csv(OUTPUT_DIR / "model_selection_class_metrics.csv", index=False, encoding="utf-8-sig")
    confusion.to_csv(OUTPUT_DIR / "model_selection_confusion_matrix.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(OUTPUT_DIR / "standard_model_decision_matrix.csv", index=False, encoding="utf-8-sig")

    qa_extra = [
        {
            "quality_check": "m1_m2_original_zip_exists",
            "passed": PATHS["zip"].exists(),
            "detail": str(PATHS["zip"]),
        },
        {
            "quality_check": "manufacturer_not_used_as_feature",
            "passed": all("manufacturer" not in feature for features in fs.values() for feature in features),
            "detail": "manufacturer is metadata only",
        },
        {
            "quality_check": "metric_independent_recheck_all_passed",
            "passed": bool(
                not recheck.empty
                and recheck[["balanced_accuracy_match", "recall_match", "normal_fpr_match"]].all().all()
            ),
            "detail": f"checked_rows={len(recheck)}",
        },
        {
            "quality_check": "source_commit",
            "passed": True,
            "detail": source_commit_hash(),
        },
    ]
    qa_all = pd.concat([qa, pd.DataFrame(qa_extra)], ignore_index=True, sort=False)
    qa_all.to_csv(OUTPUT_DIR / "quality_audit.csv", index=False, encoding="utf-8-sig")
    write_report(dataset_summary, metrics, decision, qa_all, schema, system)


def write_report(
    dataset_summary: pd.DataFrame,
    metrics: pd.DataFrame,
    decision: pd.DataFrame,
    qa: pd.DataFrame,
    schema: pd.DataFrame,
    system: pd.DataFrame,
) -> None:
    if decision.empty:
        final_decision = "model_not_standardizable_yet"
        best = pd.DataFrame()
    else:
        best = decision.head(1)
        final_decision = str(best.iloc[0]["decision"])
    top_metrics = metrics.loc[metrics["threshold"].eq(DEFAULT_THRESHOLD)].copy()
    if not decision.empty:
        top_keys = decision.head(8)[["feature_set", "model", "threshold"]]
        top_metrics = metrics.merge(top_keys, on=["feature_set", "model", "threshold"], how="inner")
    capability_summary = (
        system.groupby("manufacturer")
        .agg(
            substations=("substation_id", "count"),
            common10_ready=("common10_ready", "sum"),
            dhw_supply_available=("dhw_supply_available", "sum"),
            dhw_storage_available=("dhw_storage_available", "sum"),
            dhw_return_available=("dhw_return_available", "sum"),
            multi_circuit_available=("multi_circuit_available", "sum"),
        )
        .reset_index()
    )
    schema_summary = schema.groupby(["schema_role", "system_specific"]).size().reset_index(name="sensor_count")
    qa_failed = qa.loc[qa["passed"].astype(str).str.lower().eq("false")].copy()
    report = f"""# M1+M2 Standardizable Pre-Event Model 보고서

## 결론
최종 판단: **{final_decision}**

이번 실험은 M1 전용 성능을 올리는 것이 아니라, M1/M2를 함께 놓고 다른 현장으로 옮겨갈 수 있는 `normal vs pre_event` 표준 구조를 검증했다.

핵심 결론은 다음과 같다.

- M1/M2 모두 같은 `standard_sensor_schema`로 feature를 계산했다.
- `manufacturer` 값은 학습 feature에 넣지 않고, 검증/분할 metadata로만 사용했다.
- system capability tag는 audit-only와 feature 사용 버전을 분리해 비교했다.
- M2를 학습에 포함한 결과는 외부 성능이 아니라 cross-manufacturer 표준화 검증으로 해석해야 한다.

## 최상위 후보
{md_table(best) if not best.empty else "후보 없음"}

## Dataset 구성
{md_table(dataset_summary)}

## System Capability 요약
{md_table(capability_summary)}

## 표준 Sensor Schema 요약
{md_table(schema_summary)}

## 주요 성능표
아래 표는 threshold 0.4/0.5/0.6 후보 중 최상위 decision 후보 중심으로 표시했다.

{md_table(top_metrics, max_rows=30) if not top_metrics.empty else "성능표 없음"}

## Decision Matrix
{md_table(decision, max_rows=20) if not decision.empty else "decision matrix 없음"}

## 해석
- `standard_common`은 공통 10개 센서 기반으로 모든 현장에 가장 쉽게 이식할 수 있는 기준이다.
- `standard_common_plus_system`은 시스템 구성을 반영하지만, 제조사/설비 구성에 과적합할 수 있어 양방향 제조사 검증을 반드시 통과해야 한다.
- `standard_optional_dhw`는 DHW 센서가 있는 현장에서만 의미가 있으므로, 전체 운영 모델이 아니라 보조 모델 후보로만 본다.
- 복잡한 tree/boosting 모델은 Logistic보다 좋아 보여도 `M1→M2`, `M2→M1` 중 한쪽이 무너지면 표준 모델 후보로 잠그지 않는다.

## 한계
- M1/M2는 같은 PreDist 계열이므로 완전히 독립된 외부 기관 검증은 아니다.
- `efd_possible=True` 자체가 fault 내부 metadata이므로, 조기탐지 가능 라벨의 품질 한계가 남아 있다.
- system tag는 실제 설비 구성을 완벽히 설명하는 엔지니어링 메타데이터가 아니라 raw sensor 보유 상태 기반 proxy다.
- DHW 보조 모델은 샘플 수와 센서 보유 편향을 함께 확인해야 한다.

## 다음 작업 순서
1. decision matrix의 최상위 후보가 `*_candidate` 또는 `*_ready`이면 해당 조합으로 final joblib 후보를 별도 검증한다.
2. 후보가 `label_window_recheck_required`이면 모델 확장보다 positive/normal window 정책을 다시 검토한다.
3. DHW subset이 유효하면 DHW 보조 gate를 별도 산출물로 분리한다.
4. 완전히 독립된 라벨 포함 SCADA 데이터가 생기면 현재 schema로 external validation을 추가한다.

## 품질 검증
{md_table(qa_failed, max_rows=40) if not qa_failed.empty else "실패한 품질 검증 없음"}

## 산출물
- `standard_sensor_schema.csv`
- `system_capability_audit.csv`
- `pre_event_dataset_index.csv`
- `standard_feature_pool.csv`
- `model_selection_metrics.csv`
- `leave_manufacturer_out_metrics.csv`
- `calibration_threshold_audit.csv`
- `standard_model_decision_matrix.csv`
- `quality_audit.csv`

source commit: `{source_commit_hash()}`
"""
    (REPORT_DIR / "M1_M2_standardizable_pre_event_model_보고서.md").write_text(report, encoding="utf-8")


def write_notebooks() -> None:
    ensure_dirs()
    notebook_specs = [
        (
            "01_standard_schema_and_system_audit.ipynb",
            "M1+M2 standard schema and system capability audit",
            "schema",
        ),
        (
            "02_m1_m2_pre_event_model_selection.ipynb",
            "M1+M2 pre-event model selection",
            "model",
        ),
        (
            "03_standardization_stress_test.ipynb",
            "M1+M2 standardization stress test and report",
            "stress",
        ),
    ]
    for filename, title, stage in notebook_specs:
        nb = nbf.v4.new_notebook()
        nb["cells"] = [
            nbf.v4.new_markdown_cell(f"# {title}\n\n이 노트북은 새 `09_실험라인` 산출물을 재현하기 위한 실행 단위입니다."),
            nbf.v4.new_code_cell(
                "from pathlib import Path\n"
                "import subprocess, sys\n"
                "root = Path.cwd()\n"
                f"result = subprocess.run([sys.executable, str(root / 'scripts' / 'run_36_m1_m2_standard_pre_event.py'), '--stage', '{stage}'], check=True, text=True, capture_output=True)\n"
                "print(result.stdout)\n"
                "if result.stderr:\n"
                "    print(result.stderr)\n"
            ),
        ]
        nb["metadata"]["kernelspec"] = {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        }
        nb["metadata"]["language_info"] = {"name": "python", "pygments_lexer": "ipython3"}
        nbf.write(nb, NOTEBOOK_DIR / filename)


def run_stage(stage: str) -> None:
    if stage == "schema":
        ensure_dirs()
        system = build_system_capability_audit()
        schema = build_standard_sensor_schema(system)
        system.to_csv(OUTPUT_DIR / "system_capability_audit.csv", index=False, encoding="utf-8-sig")
        schema.to_csv(OUTPUT_DIR / "standard_sensor_schema.csv", index=False, encoding="utf-8-sig")
        print("schema/system audit complete")
    elif stage == "model":
        write_outputs()
        print("model selection outputs complete")
    elif stage == "stress":
        write_outputs()
        print("stress test/report complete")
    elif stage == "all":
        write_notebooks()
        write_outputs()
        print("all outputs complete")
    elif stage == "write-notebooks":
        write_notebooks()
        print("notebooks written")
    else:
        raise ValueError(stage)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="all", choices=["schema", "model", "stress", "all", "write-notebooks"])
    args = parser.parse_args()
    run_stage(args.stage)


if __name__ == "__main__":
    main()
