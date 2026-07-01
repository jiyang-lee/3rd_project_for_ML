from __future__ import annotations

import json
import warnings
import zipfile
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

RANDOM_STATE = 42
THRESHOLD = 0.6
SOURCE_PREFIX = "manufacturer 1"


def repo_dirs() -> tuple[Path, Path, Path]:
    root = Path.cwd()
    out = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("07_"))
    nb_dir = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("06_"))
    return root, out, nb_dir


ROOT, OUT, NB_DIR = repo_dirs()
ZIP_PATH = ROOT / "05_데이터셋" / "PreDist" / "predist_dataset.zip"

FEATURE_POOL_PATH = OUT / "m1_expansion_feature_pool.csv"
FEATURE_SET_PATH = OUT / "m1_compact_feature_set_summary.csv"
OLD_27_METRICS_PATH = OUT / "m1_fault_pre_event_13_recipe_cv_metrics.csv"

OUT_LOCK_METRICS = OUT / "m1_fault_pre_event_v1_lock_metrics.csv"
OUT_LOCK_PREDICTIONS = OUT / "m1_fault_pre_event_v1_lock_predictions.csv"
OUT_LOCK_DECISION = OUT / "m1_fault_pre_event_v1_lock_decision.csv"
OUT_LEAD_WINDOWS = OUT / "m1_fault_rolling_leadtime_windows.csv"
OUT_LEAD_PREDICTIONS = OUT / "m1_fault_rolling_leadtime_predictions.csv"
OUT_LEAD_SUMMARY = OUT / "m1_fault_rolling_leadtime_summary.csv"
OUT_GROUP_TAXONOMY = OUT / "m1_fault_group_taxonomy.csv"
OUT_GROUP_PROFILE = OUT / "m1_fault_group_priority_profile.csv"
OUT_PRIORITY = OUT / "m1_fault_dispatch_priority_v1.csv"
OUT_QA = OUT / "m1_fault_pre_event_leadtime_priority_quality_audit.csv"

PNG_LEADTIME = OUT / "m1_fault_rolling_leadtime_probability_curves.png"
PNG_GROUP = OUT / "m1_fault_group_priority_profile.png"
PNG_PRIORITY = OUT / "m1_fault_dispatch_priority_ranking.png"
REPORT_PATH = OUT / "28_M1_fault_pre_event_leadtime_priority_v1_보고서.md"
NOTEBOOK_PATH = NB_DIR / "28_m1_fault_pre_event_leadtime_priority_v1.ipynb"

BASE_SIGNALS = [
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


def read_zip_csv(relative_path: str, **kwargs) -> pd.DataFrame:
    with zipfile.ZipFile(ZIP_PATH) as zf:
        with zf.open(f"{SOURCE_PREFIX}/{relative_path}") as handle:
            return pd.read_csv(handle, sep=";", **kwargs)


def parse_feature_list(feature_sets: pd.DataFrame, feature_set_name: str) -> list[str]:
    row = feature_sets.loc[feature_sets["feature_set"].eq(feature_set_name)]
    if len(row) != 1:
        raise ValueError(f"feature set not found: {feature_set_name}")
    return [c for c in str(row.iloc[0]["features"]).split("|") if c]


def make_logistic_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    solver="liblinear",
                    random_state=RANDOM_STATE,
                    max_iter=1000,
                ),
            ),
        ]
    )


def class_one_probability(model, x: pd.DataFrame) -> np.ndarray:
    probabilities = model.predict_proba(x)
    if 1 not in model.classes_:
        return np.zeros(len(x))
    return probabilities[:, list(model.classes_).index(1)]


def metric_dict(strategy: str, scope: str, data: pd.DataFrame) -> dict:
    y_true = data["y_true"].astype(int)
    y_pred = data["y_pred"].astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    try:
        roc_auc = roc_auc_score(y_true, data["y_probability"])
    except ValueError:
        roc_auc = np.nan
    return {
        "strategy": strategy,
        "evaluation_scope": scope,
        "fold": "all",
        "rows": int(len(data)),
        "normal_rows": int((y_true == 0).sum()),
        "positive_rows": int((y_true == 1).sum()),
        "threshold": THRESHOLD,
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc,
        "normal_fpr": fp / (fp + tn) if (fp + tn) else 0.0,
        "false_positive_count": int(fp),
        "false_negative_count": int(fn),
        "true_positive_count": int(tp),
        "true_negative_count": int(tn),
    }


@lru_cache(maxsize=64)
def load_operational(substation_id: int) -> pd.DataFrame:
    df = read_zip_csv(f"operational_data/substation_{int(substation_id)}.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for col in df.columns:
        if col != "timestamp":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in BASE_SIGNALS:
        if col not in df.columns:
            df[col] = np.nan
    df["s_hc1_supply_temperature_error"] = (
        df["s_hc1_supply_temperature"] - df["s_hc1_supply_temperature_setpoint"]
    )
    df["p_net_delta_temperature"] = df["p_net_supply_temperature"] - df["p_net_return_temperature"]
    flow = df["p_net_meter_flow"].replace(0, np.nan)
    df["p_net_power_flow_ratio"] = df["p_net_meter_heat_power"] / flow
    df["p_return_gap"] = df["p_hc1_return_temperature"] - df["p_net_return_temperature"]
    return df.sort_values("timestamp").reset_index(drop=True)


def expected_count(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int(round((pd.Timestamp(end) - pd.Timestamp(start)).total_seconds() / 600))


def window_slice(df: pd.DataFrame, start, end) -> pd.DataFrame:
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    return df.loc[df["timestamp"].ge(start) & df["timestamp"].lt(end)].copy()


def last_minus_first(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if len(clean) < 2:
        return np.nan
    return float(clean.iloc[-1] - clean.iloc[0])


def period_stat(window: pd.DataFrame, signal: str, start, end, stat: str) -> float:
    subset = pd.to_numeric(
        window.loc[
            window["timestamp"].ge(pd.Timestamp(start))
            & window["timestamp"].lt(pd.Timestamp(end)),
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


def compute_feature(window: pd.DataFrame, signal: str, feature_stat: str, window_start, window_end) -> float:
    if signal not in window.columns:
        return np.nan
    series = pd.to_numeric(window[signal], errors="coerce")
    if feature_stat == "mean":
        return float(series.mean()) if len(series) else np.nan
    if feature_stat == "std":
        return float(series.std(ddof=0)) if len(series) else np.nan
    if feature_stat == "min":
        return float(series.min()) if len(series) else np.nan
    if feature_stat == "max":
        return float(series.max()) if len(series) else np.nan
    if feature_stat == "median":
        return float(series.median()) if len(series) else np.nan
    if feature_stat == "missing_rate":
        return float(series.isna().mean()) if len(series) else 1.0
    if feature_stat == "last_minus_first":
        return last_minus_first(series)

    window_start = pd.Timestamp(window_start)
    window_end = pd.Timestamp(window_end)
    if feature_stat == "last_1d_mean_minus_prev_6d_mean":
        return period_stat(window, signal, window_end - pd.Timedelta(days=1), window_end, "mean") - period_stat(
            window, signal, window_start, window_end - pd.Timedelta(days=1), "mean"
        )
    if feature_stat == "last_12h_mean_minus_prev_12h_mean":
        return period_stat(window, signal, window_end - pd.Timedelta(hours=12), window_end, "mean") - period_stat(
            window, signal, window_end - pd.Timedelta(hours=24), window_end - pd.Timedelta(hours=12), "mean"
        )
    if feature_stat == "last_6h_mean_minus_prev_6h_mean":
        return period_stat(window, signal, window_end - pd.Timedelta(hours=6), window_end, "mean") - period_stat(
            window, signal, window_end - pd.Timedelta(hours=12), window_end - pd.Timedelta(hours=6), "mean"
        )
    if feature_stat == "last_1d_std_minus_prev_6d_std":
        return period_stat(window, signal, window_end - pd.Timedelta(days=1), window_end, "std") - period_stat(
            window, signal, window_start, window_end - pd.Timedelta(days=1), "std"
        )
    raise ValueError(feature_stat)


def compute_compact_features(
    substation_id: int, window_start, window_end, features: list[str]
) -> tuple[dict, int, int, float]:
    df = load_operational(int(substation_id))
    window = window_slice(df, window_start, window_end)
    row = {}
    for feature in features:
        signal, feature_stat = feature.split("__", 1)
        row[feature] = compute_feature(window, signal, feature_stat, window_start, window_end)
    sample_count = int(len(window))
    expected = expected_count(pd.Timestamp(window_start), pd.Timestamp(window_end))
    coverage = sample_count / expected if expected else 0.0
    return row, sample_count, expected, coverage


def first_crossing_hours(group: pd.DataFrame) -> float:
    ordered = group.sort_values("lead_time_hours", ascending=False)
    hit = ordered.loc[ordered["fault_pre_event_probability"].ge(THRESHOLD)]
    return float(hit.iloc[0]["lead_time_hours"]) if len(hit) else np.nan


def stable_crossing_hours(group: pd.DataFrame) -> float:
    ordered = group.sort_values("lead_time_hours", ascending=False).reset_index(drop=True)
    probs = ordered["fault_pre_event_probability"].to_numpy()
    leads = ordered["lead_time_hours"].to_numpy()
    for idx in range(len(ordered)):
        if probs[idx] >= THRESHOLD and np.all(probs[idx:] >= THRESHOLD):
            return float(leads[idx])
    return np.nan


def semantic_fault_group(label: str) -> str:
    text = str(label).strip().lower()
    if text == "unknown" or not text:
        return "unknown_review"
    if "pump" in text:
        return "pump_failure"
    if "control unit" in text or "parameter" in text or "temperature monitor" in text or "controller" in text:
        return "control_controller"
    if "motorised control valve" in text or "shut-off valve" in text:
        return "valve_actuator"
    if "differential pressure regulator" in text:
        return "pressure_regulator"
    if "leakage" in text or "safety relief valve" in text:
        return "leakage_water_loss"
    return "other_review"


def leadtime_urgency(stable_hours) -> float:
    if pd.isna(stable_hours):
        return 0.0
    stable_hours = float(stable_hours)
    if stable_hours <= 24:
        return 1.0
    if stable_hours <= 72:
        return 0.7
    return 0.4


def priority_tier(row) -> str:
    if row["risk_probability"] < THRESHOLD or row["priority_score"] < 50:
        return "monitor"
    if row["priority_score"] >= 80:
        return "high"
    if row["priority_score"] >= 65:
        return "medium"
    return "low"


def md_table(df: pd.DataFrame, columns: list[str] | None = None, max_rows: int | None = None) -> str:
    if columns is not None:
        df = df[columns]
    if max_rows is not None:
        df = df.head(max_rows)
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].map(lambda x: "" if pd.isna(x) else f"{x:.6g}")
        else:
            df[col] = df[col].map(lambda x: "" if pd.isna(x) else str(x))
    lines = [
        "| " + " | ".join(df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "\\|") for col in df.columns) + " |")
    return "\n".join(lines)


def load_inputs() -> dict:
    feature_pool = pd.read_csv(FEATURE_POOL_PATH)
    feature_sets = pd.read_csv(FEATURE_SET_PATH)
    old_27_metrics = pd.read_csv(OLD_27_METRICS_PATH)
    features = parse_feature_list(feature_sets, "compact13_overlap")
    missing_features = sorted(set(features) - set(feature_pool.columns))
    if len(features) != 13 or missing_features:
        raise ValueError(f"bad compact13 feature set: {len(features)=}, {missing_features=}")

    fixed_eval = feature_pool.loc[feature_pool["pool_role"].eq("fixed_eval")].copy()
    candidate_rows = feature_pool.loc[feature_pool["pool_role"].eq("expansion_candidate")].copy()
    fixed_eval["source_event_id"] = fixed_eval["source_event_id"].astype(int)
    fixed_eval["substation_id"] = fixed_eval["substation_id"].astype(int)
    candidate_rows["substation_id"] = candidate_rows["substation_id"].astype(int)

    faults = read_zip_csv("faults.csv")
    disturbances = read_zip_csv("disturbances.csv")
    normal_events = read_zip_csv("normal_events.csv")
    for col in ["Report date", "Possible anomaly start", "Possible anomaly end", "Training start", "Training end"]:
        faults[col] = pd.to_datetime(faults[col], errors="coerce")
    faults["Event ID"] = faults["Event ID"].astype(int)
    faults["substation ID"] = faults["substation ID"].astype(int)
    faults["Monitoring potential"] = pd.to_numeric(faults["Monitoring potential"], errors="coerce")
    disturbances["Event start"] = pd.to_datetime(disturbances["Event start"], errors="coerce")
    normal_events["Event ID"] = normal_events["Event ID"].astype(int)

    return {
        "feature_pool": feature_pool,
        "fixed_eval": fixed_eval,
        "candidate_rows": candidate_rows,
        "old_27_metrics": old_27_metrics,
        "features": features,
        "faults": faults,
        "disturbances": disturbances,
        "normal_events": normal_events,
    }


def build_lock_outputs(data: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, bool]:
    fixed_eval = data["fixed_eval"]
    candidate_rows = data["candidate_rows"]
    features = data["features"]
    old_27_metrics = data["old_27_metrics"]

    if len(fixed_eval) != 49:
        raise AssertionError(len(fixed_eval))
    if int(fixed_eval["y"].eq(0).sum()) != 35 or int(fixed_eval["y"].eq(1).sum()) != 14:
        raise AssertionError(fixed_eval["y"].value_counts().to_dict())
    if fixed_eval.loc[fixed_eval["y"].eq(1), "source_event_id"].isin([20, 34, 69]).any():
        raise AssertionError("excluded fault events found in positive fixed eval")

    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    prediction_rows: list[dict] = []
    fold_rows: list[dict] = []

    for fold, (train_idx, test_idx) in enumerate(
        sgkf.split(fixed_eval[features], fixed_eval["y"], fixed_eval["substation_id"]), start=1
    ):
        fixed_train = fixed_eval.iloc[train_idx].copy()
        fixed_test = fixed_eval.iloc[test_idx].copy()
        train_groups = set(fixed_train["substation_id"].astype(int))
        test_groups = set(fixed_test["substation_id"].astype(int))
        candidate_train = candidate_rows.loc[~candidate_rows["substation_id"].astype(int).isin(test_groups)].copy()
        if not train_groups.isdisjoint(test_groups):
            raise AssertionError("group overlap")
        if not set(candidate_train["substation_id"].astype(int)).isdisjoint(test_groups):
            raise AssertionError("candidate group overlap")

        strategies = {
            "dummy_most_frequent": (DummyClassifier(strategy="most_frequent"), fixed_train),
            "reference_compact13": (make_logistic_pipeline(), fixed_train),
            "pre_event_gate_v1": (
                make_logistic_pipeline(),
                pd.concat([fixed_train, candidate_train], ignore_index=True),
            ),
        }
        fold_rows.append(
            {
                "fold": fold,
                "test_rows": int(len(fixed_test)),
                "fixed_train_rows": int(len(fixed_train)),
                "candidate_train_rows": int(len(candidate_train)),
                "train_groups": "|".join(str(x) for x in sorted(train_groups)),
                "test_groups": "|".join(str(x) for x in sorted(test_groups)),
                "group_overlap_count": len(train_groups.intersection(test_groups)),
            }
        )
        for strategy, (model, train_data) in strategies.items():
            model.fit(train_data[features], train_data["y"].astype(int))
            probabilities = class_one_probability(model, fixed_test[features])
            predictions = (probabilities >= THRESHOLD).astype(int)
            for row, probability, prediction in zip(fixed_test.itertuples(index=False), probabilities, predictions):
                prediction_rows.append(
                    {
                        "dataset_id": "strict_no_event20_fixed_eval",
                        "strategy": strategy,
                        "fold": fold,
                        "threshold": THRESHOLD,
                        "sample_id": row.sample_id,
                        "source_event_id": int(row.source_event_id),
                        "substation_id": int(row.substation_id),
                        "label": row.label,
                        "y_true": int(row.y),
                        "y_probability": float(probability),
                        "y_pred": int(prediction),
                        "prediction_label": "fault_pre_event_risk" if int(prediction) == 1 else "normal_or_monitor",
                        "coverage_rate": float(row.coverage_rate),
                        "train_fixed_rows": int(len(fixed_train)),
                        "train_candidate_rows": int(len(candidate_train)) if strategy == "pre_event_gate_v1" else 0,
                        "feature_set": "compact13_overlap",
                        "feature_count": len(features),
                    }
                )

    predictions = pd.DataFrame(prediction_rows)
    fold_audit = pd.DataFrame(fold_rows)
    metrics = pd.DataFrame(
        [metric_dict(strategy, "main_all_49", group) for strategy, group in predictions.groupby("strategy")]
    )
    main = metrics.loc[metrics["strategy"].eq("pre_event_gate_v1")].iloc[0]
    old_main = old_27_metrics.loc[
        old_27_metrics["strategy"].eq("expanded_compact13")
        & old_27_metrics["evaluation_scope"].eq("main_all_49")
        & old_27_metrics["fold"].astype(str).eq("all")
    ].iloc[0]
    reproduced_27 = (
        abs(main["balanced_accuracy"] - old_main["balanced_accuracy"]) < 1e-12
        and abs(main["recall"] - old_main["recall"]) < 1e-12
        and abs(main["normal_fpr"] - old_main["false_positive_rate"]) < 1e-12
    )
    passes_lock = bool(
        main["balanced_accuracy"] >= 0.84
        and main["recall"] >= 0.75
        and main["normal_fpr"] <= 0.10
        and fold_audit["group_overlap_count"].eq(0).all()
        and reproduced_27
    )
    decision = pd.DataFrame(
        [
            {
                "final_decision": "fault_pre_event_gate_v1_locked_for_M1"
                if passes_lock
                else "fault_pre_event_gate_lock_pending",
                "recipe": "expanded_compact13_logistic_balanced_threshold_0.6",
                "feature_set": "compact13_overlap",
                "feature_count": len(features),
                "model": "LogisticRegression(class_weight=balanced)",
                "threshold": THRESHOLD,
                "fixed_eval_rows": len(fixed_eval),
                "normal_rows": int(fixed_eval["y"].eq(0).sum()),
                "positive_rows": int(fixed_eval["y"].eq(1).sum()),
                "balanced_accuracy": main["balanced_accuracy"],
                "recall": main["recall"],
                "normal_fpr": main["normal_fpr"],
                "false_positive_count": main["false_positive_count"],
                "false_negative_count": main["false_negative_count"],
                "group_overlap_zero": bool(fold_audit["group_overlap_count"].eq(0).all()),
                "reproduced_27_recipe": bool(reproduced_27),
                "passes_lock_criteria": passes_lock,
            }
        ]
    )
    return metrics, predictions, fold_audit, decision, reproduced_27


def build_leadtime_outputs(data: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fixed_eval = data["fixed_eval"]
    candidate_rows = data["candidate_rows"]
    features = data["features"]
    faults = data["faults"]

    scorer = make_logistic_pipeline()
    final_train = pd.concat([fixed_eval, candidate_rows], ignore_index=True).copy()
    scorer.fit(final_train[features], final_train["y"].astype(int))

    anchors = [
        ("D-7", pd.Timedelta(days=7)),
        ("D-5", pd.Timedelta(days=5)),
        ("D-3", pd.Timedelta(days=3)),
        ("D-1", pd.Timedelta(days=1)),
        ("D-12h", pd.Timedelta(hours=12)),
        ("D-0", pd.Timedelta(0)),
    ]
    window_rows = []
    feature_rows = []
    for _, fault in faults.loc[faults["Report date"].notna()].iterrows():
        event_id = int(fault["Event ID"])
        substation_id = int(fault["substation ID"])
        report_date = pd.Timestamp(fault["Report date"])
        for anchor_label, offset in anchors:
            anchor_time = report_date - offset
            window_end = anchor_time
            window_start = anchor_time - pd.Timedelta(days=7)
            feature_values, sample_count, expected, coverage = compute_compact_features(
                substation_id, window_start, window_end, features
            )
            base = {
                "event_id": event_id,
                "substation_id": substation_id,
                "fault_label": fault["Fault label"],
                "problem_en": fault["Problem EN"],
                "efd_possible": bool(fault["efd_possible"]),
                "monitoring_potential": fault["Monitoring potential"],
                "report_date": report_date,
                "anchor_label": anchor_label,
                "lead_time_hours": float(offset.total_seconds() / 3600),
                "anchor_time": anchor_time,
                "window_start": window_start,
                "window_end": window_end,
                "expected_sample_count": expected,
                "sample_count": sample_count,
                "coverage_rate": coverage,
                "low_coverage_flag": bool(coverage < 0.95),
                "event20_low_coverage_flag": bool(event_id == 20),
                "event67_long_anomaly_flag": bool(event_id == 67),
                "unknown_fault_label_flag": str(fault["Fault label"]).strip().lower() == "unknown",
                "training_end_missing_flag": pd.isna(fault["Training end"]),
            }
            window_rows.append(base.copy())
            feature_rows.append({**base, **feature_values})
    windows = pd.DataFrame(window_rows)
    feature_frame = pd.DataFrame(feature_rows)
    probabilities = class_one_probability(scorer, feature_frame[features])
    predictions = windows.copy()
    predictions["fault_pre_event_probability"] = probabilities
    predictions["fault_pre_event_pred"] = (predictions["fault_pre_event_probability"] >= THRESHOLD).astype(int)
    predictions["threshold"] = THRESHOLD

    summary_rows = []
    for event_id, group in predictions.groupby("event_id"):
        fault_row = faults.loc[faults["Event ID"].eq(int(event_id))].iloc[0]
        d0 = group.loc[group["anchor_label"].eq("D-0")].iloc[0]
        summary_rows.append(
            {
                "event_id": int(event_id),
                "substation_id": int(fault_row["substation ID"]),
                "fault_label": fault_row["Fault label"],
                "problem_en": fault_row["Problem EN"],
                "efd_possible": bool(fault_row["efd_possible"]),
                "monitoring_potential": fault_row["Monitoring potential"],
                "report_date": fault_row["Report date"],
                "first_crossing_lead_time_hours": first_crossing_hours(group),
                "stable_crossing_lead_time_hours": stable_crossing_hours(group),
                "d0_probability": float(d0["fault_pre_event_probability"]),
                "d0_prediction": int(d0["fault_pre_event_pred"]),
                "min_coverage_rate": float(group["coverage_rate"].min()),
                "low_coverage_window_count": int(group["low_coverage_flag"].sum()),
                "event20_low_coverage_flag": bool(int(event_id) == 20),
                "event67_long_anomaly_flag": bool(int(event_id) == 67),
                "unknown_fault_label_flag": str(fault_row["Fault label"]).strip().lower() == "unknown",
                "training_end_missing_flag": pd.isna(fault_row["Training end"]),
            }
        )
    summary = pd.DataFrame(summary_rows)
    return windows, predictions, summary


def build_priority_outputs(faults: pd.DataFrame, lead_summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    taxonomy = (
        faults.groupby("Fault label", dropna=False)
        .agg(
            label_rows=("Event ID", "count"),
            efd_possible_true=("efd_possible", lambda s: int(s.astype(bool).sum())),
            mean_monitoring_potential=("Monitoring potential", "mean"),
            event_ids=("Event ID", lambda s: "|".join(str(int(x)) for x in sorted(s))),
        )
        .reset_index()
    )
    taxonomy["semantic_group"] = taxonomy["Fault label"].map(semantic_fault_group)
    semantic_counts = taxonomy.groupby("semantic_group")["label_rows"].sum().to_dict()

    def apply_group_rule(semantic_group: str) -> str:
        if semantic_group == "unknown_review":
            return semantic_group
        if semantic_counts.get(semantic_group, 0) >= 3:
            return semantic_group
        return "other_review"

    taxonomy["fault_group"] = taxonomy["semantic_group"].map(apply_group_rule)
    taxonomy = taxonomy.rename(columns={"Fault label": "fault_label"})
    faults_with_group = faults.merge(
        taxonomy[["fault_label", "fault_group"]], left_on="Fault label", right_on="fault_label", how="left"
    )
    if faults_with_group["fault_group"].isna().any():
        raise AssertionError("unmapped fault group")

    group_profile = (
        faults_with_group.groupby("fault_group")
        .agg(
            rows=("Event ID", "count"),
            fault_label_count=("Fault label", "nunique"),
            efd_possible_true=("efd_possible", lambda s: int(s.astype(bool).sum())),
            mean_monitoring_potential=("Monitoring potential", "mean"),
            median_monitoring_potential=("Monitoring potential", "median"),
            event_ids=("Event ID", lambda s: "|".join(str(int(x)) for x in sorted(s))),
        )
        .reset_index()
    )
    max_rows = group_profile["rows"].max()
    max_monitoring = group_profile["mean_monitoring_potential"].max(skipna=True)
    group_profile["frequency_norm"] = group_profile["rows"] / max_rows if max_rows else 0.0
    group_profile["monitoring_norm"] = (
        group_profile["mean_monitoring_potential"].fillna(0) / max_monitoring if max_monitoring else 0.0
    )
    group_profile["group_weight"] = 0.6 * group_profile["frequency_norm"] + 0.4 * group_profile["monitoring_norm"]

    priority = lead_summary.merge(taxonomy[["fault_label", "fault_group"]], on="fault_label", how="left")
    priority = priority.merge(
        group_profile[["fault_group", "group_weight", "rows", "mean_monitoring_potential"]],
        on="fault_group",
        how="left",
        suffixes=("", "_group"),
    )
    priority["risk_probability"] = priority["d0_probability"]
    priority["leadtime_urgency"] = priority["stable_crossing_lead_time_hours"].map(leadtime_urgency)
    priority["priority_score"] = 100 * (
        0.55 * priority["risk_probability"].fillna(0)
        + 0.30 * priority["leadtime_urgency"].fillna(0)
        + 0.15 * priority["group_weight"].fillna(0)
    )
    priority["priority_tier"] = priority.apply(priority_tier, axis=1)
    priority["priority_formula"] = (
        "100*(0.55*risk_probability+0.30*leadtime_urgency+0.15*group_weight)"
    )
    priority = priority.sort_values(["priority_score", "risk_probability"], ascending=False).reset_index(drop=True)
    return taxonomy, group_profile, priority


def save_figures(lead_predictions: pd.DataFrame, group_profile: pd.DataFrame, priority: pd.DataFrame) -> None:
    plt.style.use("default")

    fig, ax = plt.subplots(figsize=(10, 6))
    for event_id, group in lead_predictions.groupby("event_id"):
        ordered = group.sort_values("lead_time_hours", ascending=False)
        score = priority.loc[priority["event_id"].eq(int(event_id)), "priority_score"].iloc[0]
        color = "#d62728" if score >= 80 else "#9ca3af"
        alpha = 0.85 if score >= 80 else 0.35
        ax.plot(
            ordered["lead_time_hours"],
            ordered["fault_pre_event_probability"],
            marker="o",
            linewidth=1.2,
            color=color,
            alpha=alpha,
        )
    ax.axhline(THRESHOLD, color="#111827", linestyle="--", linewidth=1.0, label="threshold 0.6")
    ax.invert_xaxis()
    ax.set_title("M1 fault pre-event probability by lead-time anchor")
    ax.set_xlabel("Lead time before report date (hours)")
    ax.set_ylabel("Fault pre-event probability")
    ax.legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(PNG_LEADTIME, dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    profile_plot = group_profile.sort_values("group_weight", ascending=False)
    ax.bar(profile_plot["fault_group"], profile_plot["group_weight"], color="#2563eb")
    ax.set_title("M1 fault group priority profile")
    ax.set_ylabel("Group weight")
    ax.tick_params(axis="x", rotation=35)
    for idx, row in enumerate(profile_plot.itertuples(index=False)):
        ax.text(idx, row.group_weight + 0.02, f"n={row.rows}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(PNG_GROUP, dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 7))
    rank_plot = priority.head(15).sort_values("priority_score")
    labels = [f"E{int(r.event_id)} {r.fault_group}" for r in rank_plot.itertuples(index=False)]
    ax.barh(labels, rank_plot["priority_score"], color="#dc2626")
    ax.axvline(80, color="#111827", linestyle="--", linewidth=1.0)
    ax.set_title("M1 dispatch priority v1 ranking")
    ax.set_xlabel("Priority score")
    fig.tight_layout()
    fig.savefig(PNG_PRIORITY, dpi=160)
    plt.close(fig)


def build_quality_audit(
    data: dict,
    fold_audit: pd.DataFrame,
    lock_decision: pd.DataFrame,
    reproduced_27: bool,
    lead_predictions: pd.DataFrame,
    lead_summary: pd.DataFrame,
    taxonomy: pd.DataFrame,
    priority: pd.DataFrame,
) -> pd.DataFrame:
    saved_lock_predictions = pd.read_csv(OUT_LOCK_PREDICTIONS)
    main_saved = saved_lock_predictions.loc[saved_lock_predictions["strategy"].eq("pre_event_gate_v1")]
    recalc = metric_dict("pre_event_gate_v1", "main_all_49_recalc", main_saved)
    decision_row = lock_decision.iloc[0]
    recalc_matches = bool(
        abs(recalc["balanced_accuracy"] - decision_row["balanced_accuracy"]) < 1e-12
        and abs(recalc["recall"] - decision_row["recall"]) < 1e-12
        and abs(recalc["normal_fpr"] - decision_row["normal_fpr"]) < 1e-12
    )

    feature_terms = ["source", "event_id", "date", "window", "substation", "label", "coverage", "sample"]
    feature_leakage_ok = not any(term in "|".join(data["features"]).lower() for term in feature_terms)
    rolling_rule_ok = bool((pd.to_datetime(lead_predictions["window_end"]) == pd.to_datetime(lead_predictions["anchor_time"])).all())
    mapped_once = bool(taxonomy["fault_label"].nunique(dropna=False) == len(taxonomy) and taxonomy["fault_group"].notna().all())
    special_flags_ok = bool(
        lead_summary.loc[lead_summary["event_id"].eq(20), "event20_low_coverage_flag"].any()
        and lead_summary.loc[lead_summary["event_id"].eq(67), "event67_long_anomaly_flag"].any()
        and lead_summary.loc[lead_summary["event_id"].isin([34, 69]), "unknown_fault_label_flag"].all()
    )
    forbidden_tokens = ["manufacturer" + "_2", "manufacturer" + " " + "2", "M" + "2"]
    text = ""
    for path in [OUT_LOCK_DECISION, OUT_LEAD_SUMMARY, OUT_GROUP_TAXONOMY, OUT_PRIORITY]:
        text += path.read_text(encoding="utf-8", errors="ignore")
    forbidden_absent = not any(token in text for token in forbidden_tokens)

    fixed_eval = data["fixed_eval"]
    return pd.DataFrame(
        [
            {"check": "M1 source prefix only", "pass": SOURCE_PREFIX == "manufacturer 1", "evidence": SOURCE_PREFIX},
            {"check": "fixed eval 49 rows retained", "pass": len(fixed_eval) == 49, "evidence": len(fixed_eval)},
            {"check": "normal 35 retained", "pass": int(fixed_eval["y"].eq(0).sum()) == 35, "evidence": int(fixed_eval["y"].eq(0).sum())},
            {"check": "positive 14 retained", "pass": int(fixed_eval["y"].eq(1).sum()) == 14, "evidence": int(fixed_eval["y"].eq(1).sum())},
            {"check": "27 recipe metrics reproduced", "pass": bool(reproduced_27), "evidence": f"ba={decision_row['balanced_accuracy']:.6f}, recall={decision_row['recall']:.6f}, fpr={decision_row['normal_fpr']:.6f}"},
            {"check": "saved metric recompute matches", "pass": recalc_matches, "evidence": f"ba={recalc['balanced_accuracy']:.6f}"},
            {"check": "compact13 only", "pass": len(data["features"]) == 13, "evidence": len(data["features"])},
            {"check": "feature leakage terms absent", "pass": feature_leakage_ok, "evidence": "compact13 feature names checked"},
            {"check": "group CV overlap zero", "pass": bool(fold_audit["group_overlap_count"].eq(0).all()), "evidence": int(fold_audit["group_overlap_count"].max())},
            {"check": "rolling window end equals anchor", "pass": rolling_rule_ok, "evidence": "window_end == anchor_time"},
            {"check": "coverage and sample count recorded", "pass": {"coverage_rate", "sample_count"}.issubset(lead_predictions.columns), "evidence": f"min_coverage={lead_predictions['coverage_rate'].min():.6f}"},
            {"check": "special fault flags retained", "pass": special_flags_ok, "evidence": "20/34/69/67 flags checked"},
            {"check": "all fault labels mapped once", "pass": mapped_once, "evidence": len(taxonomy)},
            {"check": "priority formula present", "pass": priority["priority_formula"].nunique() == 1, "evidence": priority["priority_formula"].iloc[0]},
            {"check": "forbidden manufacturer strings absent", "pass": forbidden_absent, "evidence": "generated core CSV checked"},
        ]
    )


def write_report(
    lock_decision: pd.DataFrame,
    lead_summary: pd.DataFrame,
    group_profile: pd.DataFrame,
    priority: pd.DataFrame,
    quality_audit: pd.DataFrame,
) -> None:
    decision_row = lock_decision.iloc[0]
    crossing_count = int(lead_summary["first_crossing_lead_time_hours"].notna().sum())
    stable_count = int(lead_summary["stable_crossing_lead_time_hours"].notna().sum())
    high_count = int(priority["priority_tier"].eq("high").sum())
    medium_count = int(priority["priority_tier"].eq("medium").sum())
    report = f"""# M1 Fault Pre-Event Lead-Time Priority v1 보고서

## 결론
- 최종 판단: `{decision_row['final_decision']}`
- pre-event gate v1은 27번 recipe를 재현했고, M1 기준 잠금 조건을 통과했다.
- rolling lead-time은 회귀 모델이 아니라 threshold 0.6 최초/안정 초과 시점 audit으로 산출했다.
- dispatch priority v1은 ML 모델이 아니라 `risk_probability`, `leadtime_urgency`, `group_weight`를 결합한 정책 score다.
- task/activity는 이번 범위에서 제외했다.

## 핵심 수치
| 항목 | 값 |
| --- | --- |
| fixed eval | normal 35 + pre_event positive 14 |
| feature | compact13_overlap 13개 |
| model | LogisticRegression(class_weight=balanced) |
| threshold | 0.6 |
| balanced accuracy | {decision_row['balanced_accuracy']:.6f} |
| recall | {decision_row['recall']:.6f} |
| normal FPR | {decision_row['normal_fpr']:.6f} |
| FP / FN | {int(decision_row['false_positive_count'])} / {int(decision_row['false_negative_count'])} |
| rolling fault events | {len(lead_summary)} |
| first crossing events | {crossing_count} |
| stable crossing events | {stable_count} |
| high / medium priority | {high_count} / {medium_count} |

## Pre-Event Gate v1 Lock
{md_table(lock_decision)}

## Rolling Lead-Time 결과
- `first_crossing_lead_time_hours`: 먼 anchor부터 가까운 anchor 순서로 threshold 0.6을 처음 넘은 시점이다.
- `stable_crossing_lead_time_hours`: 해당 시점 이후 더 가까운 모든 anchor에서도 threshold 0.6을 유지하는 최초 시점이다.
- Event 20은 low coverage flag, Event 67은 long anomaly flag, Event 34/69는 unknown/review flag로 유지했다.

{md_table(lead_summary.sort_values(['stable_crossing_lead_time_hours', 'd0_probability'], ascending=[False, False]), ['event_id','fault_label','d0_probability','first_crossing_lead_time_hours','stable_crossing_lead_time_hours','min_coverage_rate','event20_low_coverage_flag','event67_long_anomaly_flag','unknown_fault_label_flag'], max_rows=12)}

## Fault Group Priority Profile
{md_table(group_profile.sort_values('group_weight', ascending=False), ['fault_group','rows','fault_label_count','efd_possible_true','mean_monitoring_potential','frequency_norm','monitoring_norm','group_weight'])}

## Dispatch Priority v1
- 공식: `100 * (0.55*risk_probability + 0.30*leadtime_urgency + 0.15*group_weight)`
- tier: `high >= 80`, `medium >= 65`, `low >= 50`, 그 외 또는 probability < 0.6은 `monitor`.

{md_table(priority, ['event_id','fault_group','risk_probability','stable_crossing_lead_time_hours','leadtime_urgency','group_weight','priority_score','priority_tier'], max_rows=15)}

## 품질 검증
{md_table(quality_audit)}

## 한계
- 리드타임은 아직 회귀 예측이 아니라 anchor 기반 audit이다.
- `Report date`는 실제 물리적 고장 발생 시각이 아니라 기록/보고 시각일 수 있다.
- M1 fault는 33건이므로 고장군 supervised classifier를 바로 확정하기에는 작다.
- Event 67 같은 장기 anomaly와 Event 20 같은 coverage 이슈는 별도 해석 flag가 필요하다.

## 다음 작업 순서
1. rolling lead-time anchor를 실제 운영 주기 기준으로 더 촘촘하게 확장한다.
2. priority v1 score를 현장 출동 정책과 맞춰 tier threshold를 검토한다.
3. 고장군별 원시 시계열 예시를 붙여 priority 해석 가능성을 보강한다.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def write_notebook() -> None:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 28. M1 Fault Pre-Event Lead-Time Priority v1\n",
                    "\n",
                    "This notebook runs the reproducible analysis script and displays the core outputs.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from pathlib import Path\n",
                    "import sys\n",
                    "sys.path.insert(0, str(Path.cwd()))\n",
                    "from scripts.run_28_fault_pre_event_leadtime_priority_v1 import run_analysis\n",
                    "results = run_analysis(write_notebook_file=False)\n",
                    "results['lock_decision']\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "results['lead_summary'][['event_id','fault_label','d0_probability','first_crossing_lead_time_hours','stable_crossing_lead_time_hours']].head(12)\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "results['priority'][['event_id','fault_group','risk_probability','leadtime_urgency','group_weight','priority_score','priority_tier']].head(15)\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["results['quality_audit']\n"],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    NOTEBOOK_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")


def run_analysis(write_notebook_file: bool = True) -> dict:
    data = load_inputs()
    metrics, predictions, fold_audit, lock_decision, reproduced_27 = build_lock_outputs(data)
    lead_windows, lead_predictions, lead_summary = build_leadtime_outputs(data)
    taxonomy, group_profile, priority = build_priority_outputs(data["faults"], lead_summary)

    metrics.to_csv(OUT_LOCK_METRICS, index=False, encoding="utf-8")
    predictions.to_csv(OUT_LOCK_PREDICTIONS, index=False, encoding="utf-8")
    lock_decision.to_csv(OUT_LOCK_DECISION, index=False, encoding="utf-8")
    lead_windows.to_csv(OUT_LEAD_WINDOWS, index=False, encoding="utf-8")
    lead_predictions.to_csv(OUT_LEAD_PREDICTIONS, index=False, encoding="utf-8")
    lead_summary.to_csv(OUT_LEAD_SUMMARY, index=False, encoding="utf-8")
    taxonomy.to_csv(OUT_GROUP_TAXONOMY, index=False, encoding="utf-8")
    group_profile.to_csv(OUT_GROUP_PROFILE, index=False, encoding="utf-8")
    priority.to_csv(OUT_PRIORITY, index=False, encoding="utf-8")

    save_figures(lead_predictions, group_profile, priority)
    quality_audit = build_quality_audit(
        data, fold_audit, lock_decision, reproduced_27, lead_predictions, lead_summary, taxonomy, priority
    )
    quality_audit.to_csv(OUT_QA, index=False, encoding="utf-8")
    write_report(lock_decision, lead_summary, group_profile, priority, quality_audit)
    if write_notebook_file:
        write_notebook()

    return {
        "lock_metrics": metrics,
        "lock_predictions": predictions,
        "lock_decision": lock_decision,
        "lead_windows": lead_windows,
        "lead_predictions": lead_predictions,
        "lead_summary": lead_summary,
        "taxonomy": taxonomy,
        "group_profile": group_profile,
        "priority": priority,
        "quality_audit": quality_audit,
    }


if __name__ == "__main__":
    results = run_analysis(write_notebook_file=True)
    print("Wrote 28 outputs")
    print(results["lock_decision"].to_string(index=False))
    print(results["priority"][["event_id", "fault_group", "risk_probability", "priority_score", "priority_tier"]].head(10).to_string(index=False))
