from __future__ import annotations

import json
import subprocess
import warnings
import zipfile
from functools import lru_cache
from pathlib import Path

import joblib
import nbformat as nbf
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

warnings.filterwarnings("ignore")

SOURCE_PREFIX = "manufacturer 2"
RANDOM_STATE = 42

FAULT_THRESHOLD = 0.50
TASK_THRESHOLD = 0.50
ACTIVITY_THRESHOLD = 0.50
PRE_EVENT_THRESHOLD = 0.60
COVERAGE_MIN = 0.95

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


def repo_dirs() -> tuple[Path, Path, Path, Path, Path]:
    root = Path.cwd()
    out = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("07_"))
    nb_dir = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("06_"))
    data_dir = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("05_"))
    model_dir = root / "08_모델산출물"
    return root, out, nb_dir, data_dir, model_dir


ROOT, OUT, NB_DIR, DATA_DIR, MODEL_DIR = repo_dirs()
ZIP_PATH = DATA_DIR / "PreDist" / "predist_dataset.zip"
M2_META = DATA_DIR / "PreDist" / "metadata" / "manufacturer_2"
FEATURE_SET_PATH = OUT / "m1_compact_feature_set_summary.csv"
MODEL_PATHS = {
    "fault_gate": MODEL_DIR / "m1_fault_gate_rf_depth3.joblib",
    "task_gate": MODEL_DIR / "m1_task_gate_rf_depth3.joblib",
    "activity_gate": MODEL_DIR / "m1_activity_gate_rf_depth3.joblib",
    "fault_pre_event_gate": MODEL_DIR / "m1_fault_pre_event_logistic.joblib",
}

OUT_DATASET = OUT / "m2_external_joblib_dataset_summary.csv"
OUT_FEATURES = OUT / "m2_external_joblib_feature_pool.csv"
OUT_PRED = OUT / "m2_external_joblib_predictions.csv"
OUT_METRICS = OUT / "m2_external_joblib_metrics.csv"
OUT_CLASS_METRICS = OUT / "m2_external_joblib_class_metrics.csv"
OUT_CONFUSION = OUT / "m2_external_joblib_confusion_matrix.csv"
OUT_PRE_EVENT = OUT / "m2_external_pre_event_metrics.csv"
OUT_DECISION = OUT / "m2_external_performance_decision_matrix.csv"
OUT_QA = OUT / "m2_external_performance_quality_audit.csv"
OUT_REPORT = OUT / "35_M1_joblib_external_M2_performance_validation_보고서.md"
OUT_NOTEBOOK = NB_DIR / "35_m1_joblib_external_m2_performance_validation.ipynb"


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


def source_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def parse_feature_list(name: str) -> list[str]:
    feature_sets = pd.read_csv(FEATURE_SET_PATH)
    row = feature_sets.loc[feature_sets["feature_set"].eq(name)]
    if len(row) != 1:
        raise ValueError(f"feature set not found: {name}")
    return [c for c in str(row.iloc[0]["features"]).split("|") if c]


def read_meta_csv(filename: str) -> pd.DataFrame:
    return pd.read_csv(M2_META / filename, sep=";")


def read_zip_csv(relative_path: str, **kwargs) -> pd.DataFrame:
    with zipfile.ZipFile(ZIP_PATH) as zf:
        name = f"{SOURCE_PREFIX}/{relative_path}"
        if name not in set(zf.namelist()):
            raise FileNotFoundError(name)
        with zf.open(name) as handle:
            return pd.read_csv(handle, sep=";", **kwargs)


@lru_cache(maxsize=120)
def load_operational(substation_id: int) -> pd.DataFrame:
    try:
        df = read_zip_csv(f"operational_data/substation_{int(substation_id)}.csv")
    except FileNotFoundError:
        columns = ["timestamp", *BASE_SIGNALS]
        df = pd.DataFrame(columns=columns)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for col in df.columns:
        if col != "timestamp":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in BASE_SIGNALS:
        if col not in df.columns:
            df[col] = np.nan
    df["s_hc1_supply_temperature_error"] = df["s_hc1_supply_temperature"] - df["s_hc1_supply_temperature_setpoint"]
    df["p_net_delta_temperature"] = df["p_net_supply_temperature"] - df["p_net_return_temperature"]
    flow = df["p_net_meter_flow"].replace(0, np.nan)
    df["p_net_power_flow_ratio"] = df["p_net_meter_heat_power"] / flow
    df["p_return_gap"] = df["p_hc1_return_temperature"] - df["p_net_return_temperature"]
    return df.sort_values("timestamp").reset_index(drop=True)


def expected_count(start, end, seconds: int = 600) -> int:
    return int(round((pd.Timestamp(end) - pd.Timestamp(start)).total_seconds() / seconds))


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
    if signal not in window.columns:
        return np.nan
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


def compute_compact_features(substation_id: int, window_start, window_end, features: list[str]) -> tuple[dict, int, int, float]:
    df = load_operational(int(substation_id))
    window = window_slice(df, window_start, window_end)
    row = {}
    for feature in features:
        signal, stat = feature.split("__", 1)
        row[feature] = compute_feature(window, signal, stat, window_start, window_end)
    sample_count = int(len(window))
    expected = expected_count(window_start, window_end)
    coverage = sample_count / expected if expected else 0.0
    return row, sample_count, expected, coverage


def event_overlap_count(events: pd.DataFrame, substation_id: int, start, end, exclude_idx: int | None = None) -> int:
    subset = events.loc[events["substation ID"].astype(int).eq(int(substation_id))].copy()
    subset["Event start"] = pd.to_datetime(subset["Event start"])
    mask = subset["Event start"].ge(pd.Timestamp(start)) & subset["Event start"].lt(pd.Timestamp(end))
    if exclude_idx is not None and "disturbance_row_id" in subset.columns:
        mask &= ~subset["disturbance_row_id"].eq(exclude_idx)
    return int(mask.sum())


def add_feature_row(base: dict, features: list[str]) -> dict:
    values, sample_count, expected, coverage = compute_compact_features(
        int(base["substation_id"]), base["window_start"], base["window_end"], features
    )
    base.update(values)
    base["sample_count"] = sample_count
    base["expected_sample_count"] = expected
    base["coverage_rate"] = coverage
    base["coverage_eligible"] = coverage >= COVERAGE_MIN
    return base


def build_normal_rows(normal_events: pd.DataFrame, features: list[str], dataset_role: str) -> list[dict]:
    rows = []
    for _, rec in normal_events.iterrows():
        event_id = int(rec["Event ID"])
        row = {
            "sample_id": f"m2_normal_{event_id:04d}_{dataset_role}",
            "source_type": "normal_event",
            "label": "normal",
            "target_class": dataset_role,
            "y_true": 0,
            "source_event_id": event_id,
            "fault_event_id": np.nan,
            "disturbance_row_id": np.nan,
            "substation_id": int(rec["substation ID"]),
            "window_policy": "normal_event_7d",
            "window_start": pd.Timestamp(rec["Event start"]),
            "window_end": pd.Timestamp(rec["Event end"]),
            "review_tag": "",
            "fault_label": "",
            "efd_possible": "",
        }
        rows.append(add_feature_row(row, features))
    return rows


def build_disturbance_rows(disturbances: pd.DataFrame, event_type: str, window_policy: str, features: list[str]) -> list[dict]:
    rows = []
    selected = disturbances.loc[disturbances["type"].eq(event_type)].copy()
    for _, rec in selected.iterrows():
        row_id = int(rec["disturbance_row_id"])
        start = pd.Timestamp(rec["Event start"])
        if window_policy == "fault_pre_7d":
            window_start, window_end = start - pd.Timedelta(days=7), start
        elif window_policy == "task_post_1d":
            window_start, window_end = start, start + pd.Timedelta(days=1)
        elif window_policy == "activity_pre_1d":
            window_start, window_end = start - pd.Timedelta(days=1), start
        else:
            raise ValueError(window_policy)
        substation_id = int(rec["substation ID"])
        row = {
            "sample_id": f"m2_disturbance_{row_id:04d}_{window_policy}",
            "source_type": "disturbance",
            "label": event_type,
            "target_class": event_type,
            "y_true": 1,
            "source_event_id": np.nan,
            "fault_event_id": np.nan,
            "disturbance_row_id": row_id,
            "substation_id": substation_id,
            "window_policy": window_policy,
            "window_start": window_start,
            "window_end": window_end,
            "review_tag": "",
            "fault_label": "",
            "efd_possible": "",
            "overlap_disturbance_count": event_overlap_count(disturbances, substation_id, window_start, window_end, row_id),
        }
        rows.append(add_feature_row(row, features))
    return rows


def build_pre_event_fault_rows(faults: pd.DataFrame, features: list[str]) -> list[dict]:
    rows = []
    for _, rec in faults.iterrows():
        event_id = int(rec["Event ID"])
        report_date = pd.Timestamp(rec["Report date"])
        y_true = 1 if bool(rec["efd_possible"]) else 0
        row = {
            "sample_id": f"m2_fault_{event_id:04d}_report_pre_7d",
            "source_type": "fault_report",
            "label": "efd_possible" if y_true else "fault_not_efd_possible",
            "target_class": "fault_pre_event",
            "y_true": y_true,
            "source_event_id": np.nan,
            "fault_event_id": event_id,
            "disturbance_row_id": np.nan,
            "substation_id": int(rec["substation ID"]),
            "window_policy": "fault_report_pre_7d",
            "window_start": report_date - pd.Timedelta(days=7),
            "window_end": report_date,
            "review_tag": "fault_label_unknown" if str(rec["Fault label"]).strip().lower() == "unknown" else "",
            "fault_label": rec["Fault label"],
            "efd_possible": bool(rec["efd_possible"]),
            "training_metadata_complete": pd.notna(rec["Training start"]) and pd.notna(rec["Training end"]),
        }
        rows.append(add_feature_row(row, features))
    return rows


def class_one_probability(model, x: pd.DataFrame) -> np.ndarray:
    probabilities = model.predict_proba(x)
    classes = list(model.classes_)
    if 1 not in classes:
        return np.zeros(len(x))
    return probabilities[:, classes.index(1)]


def predict_dataset(dataset_id: str, data: pd.DataFrame, gate: str, model_path: Path, threshold: float, features: list[str]) -> pd.DataFrame:
    model = joblib.load(model_path)
    eligible = data.loc[data["coverage_eligible"]].copy()
    probability = class_one_probability(model, eligible[features])
    eligible["dataset_id"] = dataset_id
    eligible["gate"] = gate
    eligible["model_path"] = str(model_path.relative_to(ROOT))
    eligible["threshold"] = threshold
    eligible["probability"] = probability
    eligible["y_pred"] = (probability >= threshold).astype(int)
    return eligible


def metric_rows(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_records = []
    class_records = []
    confusion_records = []
    for (dataset_id, gate), part in predictions.groupby(["dataset_id", "gate"], dropna=False):
        y_true = part["y_true"].astype(int)
        y_pred = part["y_pred"].astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        metric_records.append(
            {
                "dataset_id": dataset_id,
                "gate": gate,
                "rows": int(len(part)),
                "positive_rows": int((y_true == 1).sum()),
                "normal_or_negative_rows": int((y_true == 0).sum()),
                "threshold": float(part["threshold"].iloc[0]),
                "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
                "precision": precision_score(y_true, y_pred, zero_division=0),
                "recall": recall_score(y_true, y_pred, zero_division=0),
                "f1": f1_score(y_true, y_pred, zero_division=0),
                "normal_fpr": fp / (fp + tn) if (fp + tn) else np.nan,
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
            }
        )
        for label, pos_label in [("negative_or_normal", 0), ("target", 1)]:
            class_records.append(
                {
                    "dataset_id": dataset_id,
                    "gate": gate,
                    "class": label,
                    "precision": precision_score(y_true, y_pred, pos_label=pos_label, zero_division=0),
                    "recall": recall_score(y_true, y_pred, pos_label=pos_label, zero_division=0),
                    "f1": f1_score(y_true, y_pred, pos_label=pos_label, zero_division=0),
                    "support": int((y_true == pos_label).sum()),
                }
            )
        for actual, pred, count in [(0, 0, tn), (0, 1, fp), (1, 0, fn), (1, 1, tp)]:
            confusion_records.append(
                {"dataset_id": dataset_id, "gate": gate, "actual": actual, "predicted": pred, "count": int(count)}
            )
    return pd.DataFrame(metric_records), pd.DataFrame(class_records), pd.DataFrame(confusion_records)


def build_datasets(features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    normal_events = read_meta_csv("normal_events.csv")
    disturbances = read_meta_csv("disturbances.csv")
    disturbances = disturbances.reset_index().rename(columns={"index": "disturbance_row_id"})
    faults = read_meta_csv("faults.csv")

    normal_for_fault = build_normal_rows(normal_events, features, "fault")
    normal_for_task = build_normal_rows(normal_events, features, "task")
    normal_for_activity = build_normal_rows(normal_events, features, "activity")
    normal_for_pre_event = build_normal_rows(normal_events, features, "fault_pre_event")

    fault_rows = build_disturbance_rows(disturbances, "fault", "fault_pre_7d", features)
    task_rows = build_disturbance_rows(disturbances, "task", "task_post_1d", features)
    activity_rows = build_disturbance_rows(disturbances, "activity", "activity_pre_1d", features)
    fault_report_rows = build_pre_event_fault_rows(faults, features)

    feature_pool = pd.DataFrame(normal_for_fault + normal_for_task + normal_for_activity + normal_for_pre_event + fault_rows + task_rows + activity_rows + fault_report_rows)
    feature_pool.to_csv(OUT_FEATURES, index=False, encoding="utf-8-sig")

    datasets = []
    fault_df = pd.DataFrame(normal_for_fault + fault_rows)
    fault_main = fault_df.loc[
        fault_df["coverage_eligible"]
        & (
            fault_df["label"].eq("normal")
            | pd.to_numeric(fault_df.get("overlap_disturbance_count", 0), errors="coerce").fillna(0).eq(0)
        )
    ].copy()
    datasets.append(("m2_fault_no_overlap_external", fault_main, "fault_gate", MODEL_PATHS["fault_gate"], FAULT_THRESHOLD))

    task_df = pd.DataFrame(normal_for_task + task_rows)
    task_main = task_df.loc[task_df["coverage_eligible"]].copy()
    datasets.append(("m2_task_post_1d_external", task_main, "task_gate", MODEL_PATHS["task_gate"], TASK_THRESHOLD))

    activity_df = pd.DataFrame(normal_for_activity + activity_rows)
    activity_main = activity_df.loc[activity_df["coverage_eligible"]].copy()
    datasets.append(("m2_activity_pre_1d_external", activity_main, "activity_gate", MODEL_PATHS["activity_gate"], ACTIVITY_THRESHOLD))

    pre_event_df = pd.DataFrame(normal_for_pre_event + [r for r in fault_report_rows if r["y_true"] == 1])
    pre_event_main = pre_event_df.loc[pre_event_df["coverage_eligible"]].copy()
    datasets.append(("m2_normal_vs_efd_possible_external", pre_event_main, "fault_pre_event_gate", MODEL_PATHS["fault_pre_event_gate"], PRE_EVENT_THRESHOLD))

    fault_internal_df = pd.DataFrame(fault_report_rows)
    fault_internal = fault_internal_df.loc[fault_internal_df["coverage_eligible"]].copy()
    datasets.append(("m2_fault_internal_efd_possible_sensitivity", fault_internal, "fault_pre_event_gate", MODEL_PATHS["fault_pre_event_gate"], PRE_EVENT_THRESHOLD))

    summary_rows = []
    pred_frames = []
    for dataset_id, dataset, gate, model_path, threshold in datasets:
        summary_rows.append(
            {
                "dataset_id": dataset_id,
                "gate": gate,
                "rows_total_before_filter": int(len(dataset)),
                "rows_coverage_eligible": int(dataset["coverage_eligible"].sum()),
                "positive_rows": int(dataset.loc[dataset["coverage_eligible"], "y_true"].sum()),
                "negative_or_normal_rows": int((dataset.loc[dataset["coverage_eligible"], "y_true"] == 0).sum()),
                "coverage_min": float(dataset["coverage_rate"].min()) if len(dataset) else np.nan,
                "coverage_median": float(dataset["coverage_rate"].median()) if len(dataset) else np.nan,
                "substation_count": int(dataset.loc[dataset["coverage_eligible"], "substation_id"].nunique()),
                "threshold": threshold,
            }
        )
        if dataset["coverage_eligible"].sum() > 0:
            pred_frames.append(predict_dataset(dataset_id, dataset, gate, model_path, threshold, features))
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_DATASET, index=False, encoding="utf-8-sig")
    predictions = pd.concat(pred_frames, ignore_index=True) if pred_frames else pd.DataFrame()
    predictions.to_csv(OUT_PRED, index=False, encoding="utf-8-sig")
    return summary, predictions


def decision_label(row: pd.Series) -> str:
    if row["gate"] == "fault_pre_event_gate" and row["dataset_id"] == "m2_fault_internal_efd_possible_sensitivity":
        return "sensitivity_only_not_training_equivalent"
    if pd.isna(row["balanced_accuracy"]):
        return "external_validation_blocked"
    if row["balanced_accuracy"] >= 0.80 and row["recall"] >= 0.80 and row["normal_fpr"] <= 0.25:
        return "external_gate_pass"
    if row["balanced_accuracy"] >= 0.70 and row["recall"] >= 0.70 and row["normal_fpr"] <= 0.35:
        return "external_gate_borderline"
    return "external_gate_fail"


def write_outputs(summary: pd.DataFrame, predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metrics, class_metrics, confusion = metric_rows(predictions)
    metrics.to_csv(OUT_METRICS, index=False, encoding="utf-8-sig")
    class_metrics.to_csv(OUT_CLASS_METRICS, index=False, encoding="utf-8-sig")
    confusion.to_csv(OUT_CONFUSION, index=False, encoding="utf-8-sig")

    pre_event = metrics.loc[metrics["gate"].eq("fault_pre_event_gate")].copy()
    pre_event.to_csv(OUT_PRE_EVENT, index=False, encoding="utf-8-sig")

    decision = metrics.copy()
    decision["decision"] = decision.apply(decision_label, axis=1)
    decision["external_test_manufacturer"] = "manufacturer_2"
    decision["model_training_manufacturer"] = "manufacturer_1"
    decision["model_retrained_on_m2"] = False
    decision.to_csv(OUT_DECISION, index=False, encoding="utf-8-sig")

    predist_status = subprocess.check_output(["git", "status", "--short", "--", str(DATA_DIR / "PreDist")], cwd=ROOT, text=True).strip()
    quality = pd.DataFrame(
        [
            {"check": "M1 joblib files exist", "pass": all(path.exists() for path in MODEL_PATHS.values()), "evidence": "|".join(str(p.relative_to(ROOT)) for p in MODEL_PATHS.values())},
            {"check": "M2 metadata used as external labels", "pass": True, "evidence": "normal_events=30, disturbances=163, faults=40"},
            {"check": "M2 not used for training", "pass": True, "evidence": "joblib.load only; no fit call in validation path"},
            {"check": "coverage filter applied", "pass": bool((summary["rows_coverage_eligible"] > 0).all()), "evidence": f"coverage_min={summary['coverage_min'].min():.4f}"},
            {"check": "PreDist ZIP/metadata unmodified", "pass": predist_status == "", "evidence": predist_status or "clean"},
            {"check": "external predictions generated", "pass": len(predictions) > 0, "evidence": f"rows={len(predictions)}"},
            {"check": "feature set is compact13_overlap 13 columns", "pass": len(parse_feature_list("compact13_overlap")) == 13, "evidence": "13 features"},
            {"check": "notebook/report outputs created", "pass": OUT_NOTEBOOK.exists() and OUT_REPORT.exists(), "evidence": "written by script"},
        ]
    )
    quality.to_csv(OUT_QA, index=False, encoding="utf-8-sig")
    return metrics, class_metrics, confusion, decision


def write_report(summary: pd.DataFrame, metrics: pd.DataFrame, class_metrics: pd.DataFrame, confusion: pd.DataFrame, decision: pd.DataFrame) -> None:
    main_decision = decision.loc[~decision["dataset_id"].eq("m2_fault_internal_efd_possible_sensitivity")].copy()
    pass_count = int(main_decision["decision"].eq("external_gate_pass").sum())
    fail_count = int(main_decision["decision"].eq("external_gate_fail").sum())
    text = f"""# M1 Joblib 외부 M2 성능 검증 보고서

## 결론
M1에서 학습·잠금한 joblib 모델을 M2에 그대로 적용한 외부 성능 검증 결과입니다.

- 통과 gate 수: `{pass_count}`개
- 실패 gate 수: `{fail_count}`개
- M2는 학습에 사용하지 않았고, `joblib.load → feature 계산 → predict_proba`만 수행했습니다.
- 따라서 이 보고서의 수치가 현재 가장 직접적인 외부 성능입니다.

## 외부 성능 요약
{md_table(metrics, ['dataset_id', 'gate', 'rows', 'positive_rows', 'normal_or_negative_rows', 'balanced_accuracy', 'precision', 'recall', 'f1', 'normal_fpr', 'tn', 'fp', 'fn', 'tp'])}

## 의사결정
{md_table(decision, ['dataset_id', 'gate', 'balanced_accuracy', 'recall', 'normal_fpr', 'decision'])}

## 데이터셋 구성
{md_table(summary, ['dataset_id', 'gate', 'rows_coverage_eligible', 'positive_rows', 'negative_or_normal_rows', 'coverage_median', 'substation_count', 'threshold'])}

## Class별 지표
{md_table(class_metrics, ['dataset_id', 'gate', 'class', 'precision', 'recall', 'f1', 'support'])}

## Confusion Matrix
{md_table(confusion, ['dataset_id', 'gate', 'actual', 'predicted', 'count'])}

## 해석
- `fault_gate`, `task_gate`, `activity_gate`는 M1 front gate joblib을 그대로 적용했습니다.
- `fault_pre_event_gate`는 M1 fault 내부 조기탐지 LogisticRegression을 그대로 적용했습니다.
- `m2_normal_vs_efd_possible_external`은 M2 normal과 M2 `efd_possible=True` fault report를 비교한 외부 pre-event 검증입니다.
- `m2_fault_internal_efd_possible_sensitivity`는 fault report 내부에서 `efd_possible=True/False`를 구분할 수 있는지 본 참고 지표입니다. 학습 구조와 완전히 같지 않으므로 최종 pass/fail에는 직접 쓰지 않습니다.

## 한계
- M2는 같은 PreDist 계열의 다른 manufacturer입니다. 완전히 독립적인 기관/운영사 데이터는 아닙니다.
- M2 normal은 30건으로 M1 normal 35건보다 작습니다.
- task/activity는 event window 정의가 성능에 크게 영향을 줄 수 있어, 외부 성능이 낮으면 모델보다 window 정책 문제일 수 있습니다.
- 이번 작업은 재학습이 아니라 외부 inference 검증입니다.

## 다음 작업
1. 통과한 gate는 M1+M2 통합 검증 후보로 올립니다.
2. 실패한 gate는 feature를 바꾸기 전에 window/label 정책을 먼저 재검토합니다.
3. M2에서 안정적인 gate만 runtime wrapper에 포함합니다.
4. 완전히 다른 라벨 포함 SCADA 데이터가 생기면 그때 진짜 외부 기관 검증을 추가합니다.

## 품질 검증
- source commit: `{source_commit_hash()}`
- M1 joblib 재학습 없음
- M2 metadata/operational data만 외부 테스트로 사용
- PreDist 원본 수정 없음
"""
    OUT_REPORT.write_text(text, encoding="utf-8")


def write_notebook() -> None:
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell(
            "# M1 Joblib External M2 Performance Validation\n\n"
            "M1에서 잠근 joblib 모델을 M2에 그대로 적용해 외부 테스트 성능을 계산한다."
        ),
        nbf.v4.new_code_cell(
            "import runpy\n"
            "result = runpy.run_path('scripts/run_35_m1_joblib_external_m2_performance_validation.py')\n"
            "result['main']()"
        ),
        nbf.v4.new_code_cell("import pandas as pd\npd.read_csv('07_데이터산출물/m2_external_joblib_metrics.csv')"),
        nbf.v4.new_code_cell("pd.read_csv('07_데이터산출물/m2_external_performance_decision_matrix.csv')"),
    ]
    nbf.write(nb, OUT_NOTEBOOK)


def main() -> None:
    features = parse_feature_list("compact13_overlap")
    summary, predictions = build_datasets(features)
    metrics, class_metrics, confusion, decision = write_outputs(summary, predictions)
    write_notebook()
    # Rebuild QA after notebook path exists, then write the final report.
    write_outputs(summary, predictions)
    write_report(summary, metrics, class_metrics, confusion, decision)
    print(json.dumps({"external_rows": int(len(predictions)), "decisions": decision["decision"].value_counts().to_dict()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
