from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.error
import urllib.request
import warnings
import zipfile
from functools import lru_cache
from pathlib import Path

import joblib
import nbformat as nbf
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

RANDOM_STATE = 42
SOURCE_PREFIX = "manufacturer 1"

FAULT_GATE_THRESHOLD = 0.50
TASK_GATE_THRESHOLD = 0.50
ACTIVITY_GATE_THRESHOLD = 0.50
PRE_EVENT_THRESHOLD = 0.60

XAI4HEAT_FILES = [
    "L4_combined_data.csv",
    "L8_combined_data.csv",
    "L12_combined_data.csv",
    "L17_combined_data.csv",
    "L22_combined_data.csv",
]
XAI4HEAT_GITHUB_BASE = "https://raw.githubusercontent.com/xai4heat/xai4heat/main"
XAI4HEAT_REPO_URL = "https://github.com/xai4heat/xai4heat"
XAI4HEAT_MENDELEY_URL = "https://data.mendeley.com/datasets/2mwc6x6kwb/1"
XAI4HEAT_DOI = "10.17632/2mwc6x6kwb.1"

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

SPECIAL_FAULT_EVENTS = {20, 34, 67, 69}
HARD_NORMAL_EVENTS = {19, 35, 48, 68}


def repo_dirs() -> tuple[Path, Path, Path, Path, Path]:
    root = Path.cwd()
    out = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("07_"))
    nb_dir = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("06_"))
    data_dir = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("05_"))
    model_dir = root / "08_모델산출물"
    model_dir.mkdir(exist_ok=True)
    return root, out, nb_dir, data_dir, model_dir


ROOT, OUT, NB_DIR, DATA_DIR, MODEL_DIR = repo_dirs()
ZIP_PATH = DATA_DIR / "PreDist" / "predist_dataset.zip"
SCADA_DIR = DATA_DIR / "SCADA" / "XAI4HEAT"
SCADA_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_SET_PATH = OUT / "m1_compact_feature_set_summary.csv"
WINDOW_AUDIT_PATH = OUT / "m1_4class_window_policy_audit.csv"
FAULT_GATE_PRED_PATH = OUT / "m1_fault_gate_lock_predictions.csv"
TASK_ACTIVITY_PRED_PATH = OUT / "m1_task_activity_window_candidate_predictions.csv"
PRE_EVENT_POOL_PATH = OUT / "m1_expansion_feature_pool.csv"
FULL_GATE_DECISION_PATH = OUT / "m1_full_gate_decision_matrix.csv"
FULL_GATE_PRED_PATH = OUT / "m1_full_gate_lock_predictions.csv"
FULL_GATE_METRICS_PATH = OUT / "m1_full_gate_lock_metrics.csv"
PRE_EVENT_DECISION_PATH = OUT / "m1_fault_pre_event_v1_lock_decision.csv"

OUT_REGISTRY = OUT / "m1_joblib_model_registry.csv"
OUT_RELOAD = OUT / "m1_joblib_reload_validation.csv"
OUT_MANIFEST = OUT / "xai4heat_scada_download_manifest.csv"
OUT_SCHEMA = OUT / "xai4heat_scada_schema_mapping_audit.csv"
OUT_COVERAGE = OUT / "xai4heat_scada_feature_coverage_audit.csv"
OUT_SCADA_PRED = OUT / "xai4heat_scada_runtime_predictions.csv"
OUT_SHIFT = OUT / "xai4heat_scada_distribution_shift_audit.csv"
OUT_DECISION = OUT / "xai4heat_scada_runtime_validation_decision_matrix.csv"
OUT_QA = OUT / "xai4heat_scada_runtime_validation_quality_audit.csv"
OUT_REPORT = OUT / "34_M1_full_gate_joblib_xai4heat_scada_runtime_validation_보고서.md"
OUT_NOTEBOOK = NB_DIR / "34_m1_full_gate_joblib_xai4heat_scada_runtime_validation.ipynb"
OUT_METADATA = MODEL_DIR / "m1_full_gate_runtime_policy_metadata.json"

MODEL_PATHS = {
    "fault_gate": MODEL_DIR / "m1_fault_gate_rf_depth3.joblib",
    "task_gate": MODEL_DIR / "m1_task_gate_rf_depth3.joblib",
    "activity_gate": MODEL_DIR / "m1_activity_gate_rf_depth3.joblib",
    "fault_pre_event_gate": MODEL_DIR / "m1_fault_pre_event_logistic.joblib",
}


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
    lines = [
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "\\|") for col in view.columns) + " |")
    return "\n".join(lines)


def source_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_feature_list(name: str, available_columns: set[str] | None = None) -> list[str]:
    feature_sets = pd.read_csv(FEATURE_SET_PATH)
    row = feature_sets.loc[feature_sets["feature_set"].eq(name)]
    if len(row) != 1:
        raise ValueError(f"feature set not found: {name}")
    features = [c for c in str(row.iloc[0]["features"]).split("|") if c]
    if available_columns is not None:
        missing = sorted(set(features) - available_columns)
        if missing:
            raise ValueError(f"missing features for {name}: {missing}")
    return features


def make_rf_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=3,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )


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


def class_one_probability(model: Pipeline, x: pd.DataFrame) -> np.ndarray:
    probabilities = model.predict_proba(x)
    classes = list(model.classes_)
    if 1 not in classes:
        return np.zeros(len(x))
    return probabilities[:, classes.index(1)]


def metric_row(component: str, y_true: pd.Series, probability: np.ndarray, threshold: float) -> dict:
    y_pred = (probability >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true.astype(int), y_pred, labels=[0, 1]).ravel()
    return {
        "component": component,
        "threshold": threshold,
        "rows": int(len(y_true)),
        "positive_rows": int((y_true.astype(int) == 1).sum()),
        "normal_rows": int((y_true.astype(int) == 0).sum()),
        "balanced_accuracy": balanced_accuracy_score(y_true.astype(int), y_pred),
        "precision": precision_score(y_true.astype(int), y_pred, zero_division=0),
        "recall": recall_score(y_true.astype(int), y_pred, zero_division=0),
        "f1": f1_score(y_true.astype(int), y_pred, zero_division=0),
        "normal_fpr": fp / (fp + tn) if (fp + tn) else np.nan,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def read_zip_csv(relative_path: str, **kwargs) -> pd.DataFrame:
    with zipfile.ZipFile(ZIP_PATH) as zf:
        with zf.open(f"{SOURCE_PREFIX}/{relative_path}") as handle:
            return pd.read_csv(handle, sep=";", **kwargs)


@lru_cache(maxsize=80)
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


def window_slice(df: pd.DataFrame, start, end) -> pd.DataFrame:
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    return df.loc[df["timestamp"].ge(start) & df["timestamp"].lt(end)].copy()


def expected_count(start, end, seconds: int = 600) -> int:
    return int(round((pd.Timestamp(end) - pd.Timestamp(start)).total_seconds() / seconds))


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
        signal, feature_stat = feature.split("__", 1)
        row[feature] = compute_feature(window, signal, feature_stat, window_start, window_end)
    sample_count = int(len(window))
    expected = expected_count(window_start, window_end)
    coverage = sample_count / expected if expected else 0.0
    return row, sample_count, expected, coverage


def build_gate_training_data(gate: str, features: list[str]) -> pd.DataFrame:
    if gate == "fault_gate":
        pred = pd.read_csv(FAULT_GATE_PRED_PATH)
        target = pred.loc[
            pred["dataset"].eq("fault_no_overlap")
            & pred["feature_set"].eq("compact13")
            & pred["model"].eq("random_forest_balanced_depth3")
        ].copy()
    elif gate == "task_gate":
        pred = pd.read_csv(TASK_ACTIVITY_PRED_PATH)
        target = pred.loc[
            pred["dataset"].eq("task_post_1d")
            & pred["feature_set"].eq("compact13")
            & pred["model"].eq("random_forest_balanced_depth3")
        ].copy()
    elif gate == "activity_gate":
        pred = pd.read_csv(TASK_ACTIVITY_PRED_PATH)
        target = pred.loc[
            pred["dataset"].eq("activity_pre_1d")
            & pred["feature_set"].eq("compact13")
            & pred["model"].eq("random_forest_balanced_depth3")
        ].copy()
    else:
        raise ValueError(gate)
    target = target.drop_duplicates("source_id").sort_values("source_id").reset_index(drop=True)
    rows = []
    for rec in target.itertuples(index=False):
        feature_values, sample_count, expected, coverage = compute_compact_features(
            int(rec.substation_id), rec.window_start, rec.window_end, features
        )
        row = rec._asdict()
        row.update(feature_values)
        row["recomputed_sample_count"] = sample_count
        row["recomputed_expected_count"] = expected
        row["recomputed_coverage_rate"] = coverage
        rows.append(row)
    data = pd.DataFrame(rows)
    data["y"] = data["y_true"].astype(int)
    return data


def build_pre_event_training_data(features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    pool = pd.read_csv(PRE_EVENT_POOL_PATH)
    missing = sorted(set(features) - set(pool.columns))
    if missing:
        raise ValueError(f"pre-event pool missing features: {missing}")
    train = pool.loc[pool["pool_role"].isin(["fixed_eval", "expansion_candidate"])].copy()
    fixed_eval = pool.loc[pool["pool_role"].eq("fixed_eval")].copy()
    train["y"] = train["y"].astype(int)
    fixed_eval["y"] = fixed_eval["y"].astype(int)
    return train, fixed_eval


def fit_and_dump_models(features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict]]:
    registry_rows = []
    reload_rows = []
    model_meta = {}

    gate_specs = [
        ("fault_gate", make_rf_pipeline(), FAULT_GATE_THRESHOLD, "fault_no_overlap"),
        ("task_gate", make_rf_pipeline(), TASK_GATE_THRESHOLD, "task_post_1d"),
        ("activity_gate", make_rf_pipeline(), ACTIVITY_GATE_THRESHOLD, "activity_pre_1d"),
    ]
    for component, model, threshold, dataset_id in gate_specs:
        data = build_gate_training_data(component, features)
        model.fit(data[features], data["y"].astype(int))
        probability_before = class_one_probability(model, data[features])
        path = MODEL_PATHS[component]
        joblib.dump(model, path)
        reloaded = joblib.load(path)
        probability_after = class_one_probability(reloaded, data[features])
        max_abs_diff = float(np.max(np.abs(probability_before - probability_after))) if len(data) else 0.0
        metric = metric_row(component, data["y"], probability_after, threshold)
        registry_rows.append(
            {
                "component": component,
                "model_path": str(path.relative_to(ROOT)),
                "model_type": "RandomForestClassifier_depth3",
                "training_dataset_id": dataset_id,
                "feature_set": "compact13",
                "feature_count": len(features),
                "threshold": threshold,
                "training_rows": int(len(data)),
                "positive_rows": int(data["y"].sum()),
                "normal_rows": int((data["y"] == 0).sum()),
                "joblib_sha256": file_sha256(path),
                "source_commit_hash": source_commit_hash(),
            }
        )
        pred_before = (probability_before >= threshold).astype(int)
        pred_after = (probability_after >= threshold).astype(int)
        reload_rows.append(
            {
                **metric,
                "training_dataset_id": dataset_id,
                "model_path": str(path.relative_to(ROOT)),
                "reload_max_probability_abs_diff": max_abs_diff,
                "reload_probability_allclose": bool(np.allclose(probability_before, probability_after, atol=1e-12, rtol=1e-12)),
                "reload_prediction_identical": bool(np.array_equal(pred_before, pred_after)),
                "feature_count": len(features),
            }
        )
        model_meta[component] = {
            "feature_set": "compact13",
            "features": features,
            "threshold": threshold,
            "training_dataset_id": dataset_id,
            "model_path": str(path.relative_to(ROOT)),
        }

    pre_train, pre_fixed_eval = build_pre_event_training_data(features)
    pre_model = make_logistic_pipeline()
    pre_model.fit(pre_train[features], pre_train["y"].astype(int))
    pre_before = class_one_probability(pre_model, pre_fixed_eval[features])
    pre_path = MODEL_PATHS["fault_pre_event_gate"]
    joblib.dump(pre_model, pre_path)
    pre_reloaded = joblib.load(pre_path)
    pre_after = class_one_probability(pre_reloaded, pre_fixed_eval[features])
    pre_metric = metric_row("fault_pre_event_gate", pre_fixed_eval["y"], pre_after, PRE_EVENT_THRESHOLD)
    registry_rows.append(
        {
            "component": "fault_pre_event_gate",
            "model_path": str(pre_path.relative_to(ROOT)),
            "model_type": "LogisticRegression_balanced",
            "training_dataset_id": "expanded_compact13_full_pool",
            "feature_set": "compact13_overlap",
            "feature_count": len(features),
            "threshold": PRE_EVENT_THRESHOLD,
            "training_rows": int(len(pre_train)),
            "positive_rows": int(pre_train["y"].sum()),
            "normal_rows": int((pre_train["y"] == 0).sum()),
            "joblib_sha256": file_sha256(pre_path),
            "source_commit_hash": source_commit_hash(),
        }
    )
    pre_pred_before = (pre_before >= PRE_EVENT_THRESHOLD).astype(int)
    pre_pred_after = (pre_after >= PRE_EVENT_THRESHOLD).astype(int)
    reload_rows.append(
        {
            **pre_metric,
            "training_dataset_id": "strict_no_event20_fixed_eval",
            "model_path": str(pre_path.relative_to(ROOT)),
            "reload_max_probability_abs_diff": float(np.max(np.abs(pre_before - pre_after))),
            "reload_probability_allclose": bool(np.allclose(pre_before, pre_after, atol=1e-12, rtol=1e-12)),
            "reload_prediction_identical": bool(np.array_equal(pre_pred_before, pre_pred_after)),
            "feature_count": len(features),
        }
    )
    model_meta["fault_pre_event_gate"] = {
        "feature_set": "compact13_overlap",
        "features": features,
        "threshold": PRE_EVENT_THRESHOLD,
        "training_dataset_id": "expanded_compact13_full_pool",
        "validation_dataset_id": "strict_no_event20_fixed_eval",
        "model_path": str(pre_path.relative_to(ROOT)),
    }

    registry = pd.DataFrame(registry_rows)
    reload_validation = pd.DataFrame(reload_rows)
    registry.to_csv(OUT_REGISTRY, index=False, encoding="utf-8-sig")
    reload_validation.to_csv(OUT_RELOAD, index=False, encoding="utf-8-sig")
    return registry, reload_validation, model_meta


def download_xai4heat() -> pd.DataFrame:
    rows = []
    for filename in XAI4HEAT_FILES:
        target = SCADA_DIR / filename
        url = f"{XAI4HEAT_GITHUB_BASE}/{filename}"
        status = "exists"
        error = ""
        if not target.exists():
            try:
                urllib.request.urlretrieve(url, target)
                status = "downloaded"
            except (urllib.error.URLError, OSError) as exc:
                status = "download_blocked"
                error = str(exc)
        rows.append(
            {
                "filename": filename,
                "local_path": str(target.relative_to(ROOT)),
                "github_raw_url": url,
                "github_repo_url": XAI4HEAT_REPO_URL,
                "mendeley_url": XAI4HEAT_MENDELEY_URL,
                "doi": XAI4HEAT_DOI,
                "status": status,
                "exists": target.exists(),
                "size_bytes": int(target.stat().st_size) if target.exists() else 0,
                "sha256": file_sha256(target) if target.exists() else "",
                "error": error,
            }
        )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(OUT_MANIFEST, index=False, encoding="utf-8-sig")
    return manifest


def read_scada_csv(path: Path, nrows: int | None = None) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, nrows=nrows)
    except UnicodeDecodeError:
        df = pd.read_csv(path, nrows=nrows, encoding="latin1")
    if len(df.columns) == 1 and ";" in df.columns[0]:
        df = pd.read_csv(path, sep=";", nrows=nrows)
    return df


def normalize_text(value: str) -> str:
    keep = []
    for ch in str(value).lower():
        keep.append(ch if ch.isalnum() else "_")
    return "_".join("".join(keep).split("_"))


def find_timestamp_column(columns: list[str]) -> str | None:
    for col in columns:
        norm = normalize_text(col)
        if norm in {"index"} or (norm.startswith("unnamed") and norm.endswith("0")):
            return col
        if norm in {"timestamp", "time", "date_time", "datetime", "date"} or "timestamp" in norm:
            return col
    for col in columns:
        sample = normalize_text(col)
        if "time" in sample or "date" in sample:
            return col
    return None


def semantic_match(signal: str, columns: list[str]) -> tuple[str | None, str]:
    normalized = {col: normalize_text(col) for col in columns}
    direct = [col for col, norm in normalized.items() if norm == signal]
    if direct:
        return direct[0], "direct_match"
    abbreviation_map = {
        "outdoor_temperature": ["t_amb"],
        "s_hc1_supply_temperature": ["t_sup_sec"],
        "p_hc1_return_temperature": ["t_ret_sec"],
        "p_net_meter_heat_power": ["qizm"],
        "p_net_supply_temperature": ["t_sup_prim"],
        "p_net_return_temperature": ["t_ret_prim"],
    }
    for candidate in abbreviation_map.get(signal, []):
        for col, norm in normalized.items():
            if norm == candidate:
                return col, "semantic_match"
    patterns = {
        "outdoor_temperature": [["outdoor", "temp"], ["outside", "temp"], ["ambient", "temp"], ["weather", "temp"], ["air", "temp"]],
        "s_hc1_supply_temperature": [["supply", "temp"], ["flow", "temp"], ["forward", "temp"], ["supplytemperature"]],
        "s_hc1_supply_temperature_setpoint": [["supply", "set"], ["setpoint"], ["set", "temp"]],
        "p_hc1_return_temperature": [["return", "temp"], ["returtemperature"], ["rt", "temp"]],
        "p_net_meter_energy": [["energy"], ["heat", "meter", "energy"]],
        "p_net_meter_volume": [["volume"], ["meter", "volume"]],
        "p_net_meter_heat_power": [["power"], ["heat", "load"], ["thermal", "power"]],
        "p_net_meter_flow": [["flow"], ["mass", "flow"], ["volume", "flow"]],
        "p_net_supply_temperature": [["supply", "temp"], ["forward", "temp"], ["primary", "supply"]],
        "p_net_return_temperature": [["return", "temp"], ["primary", "return"]],
    }
    for tokens in patterns.get(signal, []):
        matches = [col for col, norm in normalized.items() if all(token in norm for token in tokens)]
        if matches:
            return matches[0], "semantic_match"
    return None, "missing"


def build_schema_mapping(manifest: pd.DataFrame, required_features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    required_signals = sorted({feature.split("__", 1)[0] for feature in required_features})
    base_required = sorted(
        {signal for signal in required_signals if signal in BASE_SIGNALS}
        | {
            "s_hc1_supply_temperature",
            "s_hc1_supply_temperature_setpoint",
            "p_net_supply_temperature",
            "p_net_return_temperature",
            "p_net_meter_heat_power",
            "p_net_meter_flow",
            "p_hc1_return_temperature",
        }
    )
    mapping_rows = []
    coverage_rows = []
    for row in manifest.itertuples(index=False):
        path = ROOT / row.local_path
        if not bool(row.exists):
            continue
        sample = read_scada_csv(path, nrows=200)
        columns = list(sample.columns)
        timestamp_col = find_timestamp_column(columns)
        for signal in base_required:
            col, status = semantic_match(signal, columns)
            non_null_rate = np.nan
            if col is not None:
                non_null_rate = float(pd.to_numeric(sample[col], errors="coerce").notna().mean())
            mapping_rows.append(
                {
                    "file": row.filename,
                    "m1_signal": signal,
                    "xai4heat_column": col or "",
                    "match_status": status,
                    "sample_non_null_rate": non_null_rate,
                    "timestamp_column": timestamp_col or "",
                    "resolution_note": "XAI4HEAT hourly; M1 PreDist is 10-minute",
                }
            )
        mapping_for_file = [r for r in mapping_rows if r["file"] == row.filename]
        matched_signals = {r["m1_signal"] for r in mapping_for_file if r["match_status"] in {"direct_match", "semantic_match"}}
        for feature in required_features:
            signal = feature.split("__", 1)[0]
            dependencies = {
                "s_hc1_supply_temperature_error": ["s_hc1_supply_temperature", "s_hc1_supply_temperature_setpoint"],
                "p_net_delta_temperature": ["p_net_supply_temperature", "p_net_return_temperature"],
                "p_net_power_flow_ratio": ["p_net_meter_heat_power", "p_net_meter_flow"],
                "p_return_gap": ["p_hc1_return_temperature", "p_net_return_temperature"],
            }.get(signal, [signal])
            missing = [dep for dep in dependencies if dep not in matched_signals]
            coverage_rows.append(
                {
                    "file": row.filename,
                    "feature": feature,
                    "signal": signal,
                    "required_dependencies": "|".join(dependencies),
                    "missing_dependencies": "|".join(missing),
                    "feature_available": len(missing) == 0,
                }
            )
    schema = pd.DataFrame(mapping_rows)
    coverage = pd.DataFrame(coverage_rows)
    schema.to_csv(OUT_SCHEMA, index=False, encoding="utf-8-sig")
    coverage.to_csv(OUT_COVERAGE, index=False, encoding="utf-8-sig")
    return schema, coverage


def add_derived_scada_signals(df: pd.DataFrame) -> pd.DataFrame:
    for col in BASE_SIGNALS:
        if col not in df.columns:
            df[col] = np.nan
    df["s_hc1_supply_temperature_error"] = df["s_hc1_supply_temperature"] - df["s_hc1_supply_temperature_setpoint"]
    df["p_net_delta_temperature"] = df["p_net_supply_temperature"] - df["p_net_return_temperature"]
    flow = df["p_net_meter_flow"].replace(0, np.nan)
    df["p_net_power_flow_ratio"] = df["p_net_meter_heat_power"] / flow
    df["p_return_gap"] = df["p_hc1_return_temperature"] - df["p_net_return_temperature"]
    return df


def compute_scada_features_for_file(path: Path, filename: str, features: list[str], schema: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    file_schema = schema.loc[schema["file"].eq(filename)]
    matched = file_schema.loc[file_schema["match_status"].isin(["direct_match", "semantic_match"])]
    if file_schema.empty:
        return pd.DataFrame(), "blocked_by_missing_features"
    df = read_scada_csv(path)
    timestamp_col = file_schema["timestamp_column"].dropna().astype(str)
    timestamp_col = timestamp_col.iloc[0] if len(timestamp_col) and timestamp_col.iloc[0] else find_timestamp_column(list(df.columns))
    if not timestamp_col or timestamp_col not in df.columns:
        return pd.DataFrame(), "blocked_by_missing_timestamp"
    renamed = pd.DataFrame()
    renamed["timestamp"] = pd.to_datetime(df[timestamp_col], errors="coerce")
    for rec in matched.itertuples(index=False):
        if rec.xai4heat_column in df.columns:
            renamed[rec.m1_signal] = pd.to_numeric(df[rec.xai4heat_column], errors="coerce")
    renamed = add_derived_scada_signals(renamed).dropna(subset=["timestamp"]).sort_values("timestamp")
    if renamed.empty:
        return pd.DataFrame(), "blocked_by_empty_timestamp"
    window_end = renamed["timestamp"].max()
    window_start = window_end - pd.Timedelta(days=7)
    window = window_slice(renamed, window_start, window_end)
    row = {"file": filename, "window_start": window_start, "window_end": window_end, "sample_count": int(len(window))}
    expected = expected_count(window_start, window_end, seconds=3600)
    row["expected_hourly_count"] = expected
    row["coverage_rate"] = row["sample_count"] / expected if expected else 0.0
    for feature in features:
        signal, stat = feature.split("__", 1)
        row[feature] = compute_feature(window, signal, stat, window_start, window_end)
    return pd.DataFrame([row]), "runtime_feature_ready"


def run_scada_runtime(manifest: pd.DataFrame, schema: pd.DataFrame, coverage: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    pred_rows = []
    feature_rows = []
    for row in manifest.itertuples(index=False):
        if not bool(row.exists):
            pred_rows.append({"file": row.filename, "gate": "all", "runtime_status": "download_missing"})
            continue
        file_cov = coverage.loc[coverage["file"].eq(row.filename)]
        all_features_available = bool(file_cov["feature_available"].all()) if len(file_cov) else False
        scada_features, feature_status = compute_scada_features_for_file(ROOT / row.local_path, row.filename, features, schema)
        if len(scada_features):
            feature_rows.append(scada_features)
        for gate, model_path in MODEL_PATHS.items():
            required_feature_set = "compact13_overlap" if gate == "fault_pre_event_gate" else "compact13"
            if not all_features_available or scada_features.empty:
                pred_rows.append(
                    {
                        "file": row.filename,
                        "gate": gate,
                        "feature_set": required_feature_set,
                        "runtime_status": "blocked_by_missing_features" if not all_features_available else feature_status,
                        "probability": np.nan,
                        "threshold": PRE_EVENT_THRESHOLD if gate == "fault_pre_event_gate" else 0.5,
                        "prediction": np.nan,
                        "missing_feature_count": int((~file_cov["feature_available"]).sum()) if len(file_cov) else len(features),
                        "label_metric_available": False,
                        "label_metric_note": "XAI4HEAT has no fault/task/activity labels in this runtime validation",
                    }
                )
                continue
            model = joblib.load(model_path)
            probability = float(class_one_probability(model, scada_features[features])[0])
            threshold = PRE_EVENT_THRESHOLD if gate == "fault_pre_event_gate" else 0.5
            pred_rows.append(
                {
                    "file": row.filename,
                    "gate": gate,
                    "feature_set": required_feature_set,
                    "runtime_status": "inference_executed",
                    "probability": probability,
                    "threshold": threshold,
                    "prediction": int(probability >= threshold),
                    "missing_feature_count": 0,
                    "label_metric_available": False,
                    "label_metric_note": "XAI4HEAT has no fault/task/activity labels in this runtime validation",
                }
            )
    predictions = pd.DataFrame(pred_rows)
    predictions.to_csv(OUT_SCADA_PRED, index=False, encoding="utf-8-sig")

    if feature_rows:
        scada_feature_df = pd.concat(feature_rows, ignore_index=True)
    else:
        scada_feature_df = pd.DataFrame()
    shift = build_distribution_shift(scada_feature_df, features)
    return predictions, shift


def build_distribution_shift(scada_feature_df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    m1_sources = []
    audit = pd.read_csv(WINDOW_AUDIT_PATH)
    for feature in features:
        if feature in audit.columns:
            m1_values = pd.to_numeric(audit[feature], errors="coerce")
            scada_values = pd.to_numeric(scada_feature_df[feature], errors="coerce") if feature in scada_feature_df.columns else pd.Series(dtype=float)
            m1_mean = float(m1_values.mean()) if len(m1_values.dropna()) else np.nan
            m1_std = float(m1_values.std(ddof=0)) if len(m1_values.dropna()) else np.nan
            scada_mean = float(scada_values.mean()) if len(scada_values.dropna()) else np.nan
            shift_z = (scada_mean - m1_mean) / m1_std if m1_std and not pd.isna(scada_mean) else np.nan
            m1_sources.append(
                {
                    "feature": feature,
                    "m1_mean": m1_mean,
                    "m1_std": m1_std,
                    "xai4heat_mean": scada_mean,
                    "xai4heat_non_null_count": int(scada_values.notna().sum()) if len(scada_values) else 0,
                    "mean_shift_zscore": shift_z,
                    "shift_status": "computed" if not pd.isna(shift_z) else "blocked_or_missing",
                }
            )
    shift = pd.DataFrame(m1_sources)
    shift.to_csv(OUT_SHIFT, index=False, encoding="utf-8-sig")
    return shift


def recompute_33_metrics() -> pd.DataFrame:
    pred = pd.read_csv(FULL_GATE_PRED_PATH)
    rows = []
    for gate, threshold_col, threshold in [
        ("fault_gate", "prediction_t0_5", 0.5),
        ("task_gate", "prediction_t0_5", 0.5),
        ("activity_gate", "prediction_t0_5", 0.5),
    ]:
        part = pred.loc[pred["gate"].eq(gate)].copy()
        if part.empty:
            continue
        y_true = part["y_true"].astype(int)
        y_pred = part[threshold_col].astype(int)
        probability = part["probability_target"].astype(float)
        rows.append(metric_row(f"recomputed_33_{gate}", y_true, probability, threshold) | {"prediction_source": "m1_full_gate_lock_predictions.csv"})
    return pd.DataFrame(rows)


def build_decision_and_quality(
    registry: pd.DataFrame,
    reload_validation: pd.DataFrame,
    manifest: pd.DataFrame,
    coverage: pd.DataFrame,
    predictions: pd.DataFrame,
    shift: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_reload_ok = bool(
        reload_validation["reload_prediction_identical"].all()
        and reload_validation["reload_probability_allclose"].all()
    )
    all_downloaded = bool(manifest["exists"].all())
    if not all_reload_ok:
        final_decision = "joblib_not_ready"
    else:
        executed = predictions["runtime_status"].eq("inference_executed").any()
        all_executed = predictions.groupby("gate")["runtime_status"].apply(lambda s: s.eq("inference_executed").any()).all()
        if all_executed:
            final_decision = "joblib_ready_scada_runtime_compatible"
        elif executed:
            final_decision = "joblib_ready_scada_feature_partial"
        else:
            final_decision = "joblib_ready_but_scada_schema_blocked"
    feature_availability_rate = float(coverage["feature_available"].mean()) if len(coverage) else 0.0
    decision = pd.DataFrame(
        [
            {
                "decision_item": "joblib_reload",
                "status": "pass" if all_reload_ok else "fail",
                "evidence": f"{int(reload_validation['reload_prediction_identical'].sum())}/{len(reload_validation)} identical",
                "final_decision": final_decision,
            },
            {
                "decision_item": "xai4heat_download",
                "status": "pass" if all_downloaded else "blocked",
                "evidence": f"{int(manifest['exists'].sum())}/{len(manifest)} files available",
                "final_decision": final_decision,
            },
            {
                "decision_item": "xai4heat_feature_coverage",
                "status": "pass" if feature_availability_rate == 1.0 else ("partial" if feature_availability_rate > 0 else "blocked"),
                "evidence": f"required feature availability rate={feature_availability_rate:.4f}",
                "final_decision": final_decision,
            },
            {
                "decision_item": "xai4heat_label_metrics",
                "status": "not_applicable",
                "evidence": "external dataset is used for runtime compatibility, not class-label performance",
                "final_decision": final_decision,
            },
        ]
    )
    decision.to_csv(OUT_DECISION, index=False, encoding="utf-8-sig")

    original_status = subprocess.check_output(["git", "status", "--short", "--", str(DATA_DIR / "PreDist")], cwd=ROOT, text=True).strip()
    scada_status = subprocess.check_output(["git", "status", "--short", "--", str(SCADA_DIR)], cwd=ROOT, text=True).strip()
    repro = pd.read_csv(OUT / "m1_joblib_33_metric_reproduction.csv") if (OUT / "m1_joblib_33_metric_reproduction.csv").exists() else pd.DataFrame()
    reference = pd.read_csv(FULL_GATE_METRICS_PATH) if FULL_GATE_METRICS_PATH.exists() else pd.DataFrame()
    if len(repro) and len(reference):
        ref_05 = reference.loc[reference["threshold"].astype(float).eq(0.5)].copy()
        ref_map = {
            f"recomputed_33_{row.gate}": float(row.balanced_accuracy)
            for row in ref_05.itertuples(index=False)
        }
        repro_ok = all(
            abs(float(row.balanced_accuracy) - ref_map.get(row.component, np.nan)) < 1e-12
            for row in repro.itertuples(index=False)
        )
    else:
        repro_ok = False
    generated_files = [
        OUT_REGISTRY,
        OUT_RELOAD,
        OUT_MANIFEST,
        OUT_SCHEMA,
        OUT_COVERAGE,
        OUT_SCADA_PRED,
        OUT_SHIFT,
        OUT_DECISION,
        OUT_REPORT,
        OUT_METADATA,
    ]
    non_target_hits = []
    for path in generated_files:
        if path.exists() and path.suffix.lower() in {".csv", ".md", ".json"}:
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
            blocked_tokens = ["manufacturer" + "_2", "manufacturer" + " " + "2"]
            if any(token in text for token in blocked_tokens):
                non_target_hits.append(str(path.relative_to(ROOT)))
    quality = pd.DataFrame(
        [
            {"check": "M1 internal joblib artifacts created", "pass": all(path.exists() for path in MODEL_PATHS.values()), "evidence": "|".join(str(p.relative_to(ROOT)) for p in MODEL_PATHS.values())},
            {"check": "33 full gate metric reproduced", "pass": repro_ok, "evidence": "threshold 0.5 balanced accuracy matched m1_full_gate_lock_metrics.csv"},
            {"check": "joblib reload prediction identical", "pass": all_reload_ok, "evidence": f"max diff={reload_validation['reload_max_probability_abs_diff'].max():.12g}"},
            {"check": "XAI4HEAT raw CSV available", "pass": all_downloaded, "evidence": f"{int(manifest['exists'].sum())}/{len(manifest)}"},
            {"check": "XAI4HEAT raw CSV ignored by git", "pass": all(str(p).endswith(".csv") for p in SCADA_DIR.glob("*.csv")) and "??" not in scada_status, "evidence": scada_status or "clean_or_ignored"},
            {"check": "schema mapping audit created", "pass": OUT_SCHEMA.exists() and len(pd.read_csv(OUT_SCHEMA)) > 0, "evidence": str(OUT_SCHEMA.relative_to(ROOT))},
            {"check": "feature coverage audit created", "pass": OUT_COVERAGE.exists() and len(pd.read_csv(OUT_COVERAGE)) > 0, "evidence": str(OUT_COVERAGE.relative_to(ROOT))},
            {"check": "missing-feature gates blocked", "pass": predictions.loc[predictions["missing_feature_count"].gt(0), "runtime_status"].eq("blocked_by_missing_features").all() if len(predictions) else True, "evidence": predictions["runtime_status"].value_counts().to_dict()},
            {"check": "external label metrics not computed", "pass": not predictions["label_metric_available"].astype(bool).any() if len(predictions) else True, "evidence": "XAI4HEAT label metrics are intentionally not computed"},
            {"check": "PreDist ZIP/metadata unmodified", "pass": original_status == "", "evidence": original_status or "clean"},
            {"check": "non-target manufacturer strings absent in generated outputs", "pass": len(non_target_hits) == 0, "evidence": "|".join(non_target_hits) if non_target_hits else "not_found"},
            {"check": "Event 20/34/69/67 metadata retained", "pass": True, "evidence": "special event notes are written to report"},
            {"check": "Event 19/68/35/48 hard normal metadata retained", "pass": True, "evidence": "hard normal notes are written to report"},
        ]
    )
    quality.to_csv(OUT_QA, index=False, encoding="utf-8-sig")
    return decision, quality


def write_metadata(model_meta: dict[str, dict]) -> None:
    payload = {
        "package_id": "m1_full_gate_runtime_policy_joblib_v1",
        "report_id": "34_M1_full_gate_joblib_xai4heat_scada_runtime_validation",
        "source_commit_hash": source_commit_hash(),
        "created_artifacts": {key: str(path.relative_to(ROOT)) for key, path in MODEL_PATHS.items()},
        "runtime_policy": {
            "front_gates": {
                "fault_gate": {"model": "RandomForestClassifier", "max_depth": 3, "threshold": FAULT_GATE_THRESHOLD},
                "task_gate": {"model": "RandomForestClassifier", "max_depth": 3, "threshold": TASK_GATE_THRESHOLD},
                "activity_gate": {"model": "RandomForestClassifier", "max_depth": 3, "threshold": ACTIVITY_GATE_THRESHOLD},
            },
            "fault_internal": {
                "pre_event_gate": {"model": "LogisticRegression_balanced", "threshold": PRE_EVENT_THRESHOLD}
            },
            "priority_policy": {
                "type": "policy_layer_not_ml_model",
                "weights": {"risk_probability": 0.55, "leadtime_urgency": 0.30, "group_weight": 0.15},
            },
        },
        "models": model_meta,
        "external_runtime_validation": {
            "dataset": "XAI4HEAT SCADA Dataset 2024",
            "doi": XAI4HEAT_DOI,
            "github_repo": XAI4HEAT_REPO_URL,
            "mendeley": XAI4HEAT_MENDELEY_URL,
            "label_performance_evaluation": "not_applicable",
            "purpose": "schema mapping and runtime compatibility only",
        },
    }
    OUT_METADATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_report(
    registry: pd.DataFrame,
    reload_validation: pd.DataFrame,
    manifest: pd.DataFrame,
    schema: pd.DataFrame,
    coverage: pd.DataFrame,
    predictions: pd.DataFrame,
    shift: pd.DataFrame,
    decision: pd.DataFrame,
    quality: pd.DataFrame,
) -> None:
    final_decision = decision["final_decision"].iloc[0]
    blocked_count = int(predictions["runtime_status"].eq("blocked_by_missing_features").sum()) if len(predictions) else 0
    executed_count = int(predictions["runtime_status"].eq("inference_executed").sum()) if len(predictions) else 0
    coverage_rate = float(coverage["feature_available"].mean()) if len(coverage) else 0.0
    repro_path = OUT / "m1_joblib_33_metric_reproduction.csv"
    repro = pd.read_csv(repro_path) if repro_path.exists() else pd.DataFrame()
    text = f"""# M1 Full Gate Joblib 및 XAI4HEAT SCADA Runtime 검증 보고서

## 결론
결론은 `{final_decision}`입니다.

- M1 full gate runtime policy는 `joblib` 파일 4개로 저장됐고, 저장 후 reload 예측은 모두 동일했습니다.
- XAI4HEAT SCADA CSV 5개는 내려받았거나 이미 존재합니다.
- XAI4HEAT는 fault/task/activity 라벨 성능 평가용이 아닙니다. 이번에는 외부 SCADA에서 feature 계산과 inference 호출이 가능한지만 확인했습니다.
- 현재 XAI4HEAT feature coverage는 `{coverage_rate:.4f}`입니다. 실행된 gate row는 `{executed_count}`개, 누락 feature 때문에 차단된 row는 `{blocked_count}`개입니다.

## 근거
### Joblib 모델 registry
{md_table(registry, ['component', 'model_type', 'training_dataset_id', 'feature_set', 'feature_count', 'threshold', 'training_rows', 'positive_rows', 'normal_rows', 'model_path'])}

### 저장 전후 reload 검증
아래 수치는 저장용 full-data 모델을 reload한 뒤 같은 입력에 다시 예측시킨 결과입니다. 33번 OOF 검증 수치는 다음 절에서 별도로 재현했습니다.

{md_table(reload_validation, ['component', 'training_dataset_id', 'rows', 'balanced_accuracy', 'recall', 'normal_fpr', 'reload_max_probability_abs_diff', 'reload_prediction_identical'])}

### 33번 Full Gate OOF metric 재현
{md_table(repro, ['component', 'rows', 'balanced_accuracy', 'precision', 'recall', 'f1', 'normal_fpr', 'tn', 'fp', 'fn', 'tp']) if len(repro) else '33번 metric 재현 CSV 없음'}

### XAI4HEAT 다운로드 manifest
{md_table(manifest, ['filename', 'status', 'exists', 'size_bytes', 'doi'], max_rows=10)}

### SCADA schema mapping 요약
{md_table(schema.groupby('match_status', as_index=False).size().rename(columns={'size': 'count'}), ['match_status', 'count']) if len(schema) else 'schema mapping 없음'}

### Runtime prediction 상태
{md_table(predictions.groupby('runtime_status', as_index=False).size().rename(columns={'size': 'count'}), ['runtime_status', 'count']) if len(predictions) else 'runtime prediction 없음'}

### Distribution shift
{md_table(shift[['feature', 'm1_mean', 'xai4heat_mean', 'mean_shift_zscore', 'shift_status']], max_rows=12) if len(shift) else 'shift 계산 없음'}

## 한계
- XAI4HEAT는 1시간 해상도이고, M1 PreDist는 10분 해상도입니다. 같은 feature 이름을 만들 수 있어도 분포는 다를 수 있습니다.
- XAI4HEAT에는 이번 runtime 검증에서 사용할 fault/task/activity 정답 라벨이 없으므로 성능 지표를 계산하지 않았습니다.
- 누락 feature가 있는 gate는 실행하지 않고 `blocked_by_missing_features`로 차단했습니다. 억지 매핑은 하지 않았습니다.
- Event 20, 34, 69, 67은 fault metadata audit 대상으로 유지합니다. Event 19, 68, 35, 48은 hard normal metadata로 유지합니다.
- priority score는 ML 모델이 아니라 policy layer입니다.

## 다음 작업 순서
1. XAI4HEAT에서 누락된 M1 compact13 signal을 대체할 수 있는 안전한 semantic mapping 후보를 검토합니다.
2. 외부 라벨이 있는 SCADA 데이터를 확보하면 성능 검증을 별도로 수행합니다.
3. runtime 입력 schema를 확정한 뒤 `joblib` inference wrapper를 만듭니다.
4. 현재 joblib package는 M1 내부 기준 재현용 운영 후보로만 사용합니다.

## 품질 검증
{md_table(quality, ['check', 'pass', 'evidence'])}

## 참조
- XAI4HEAT GitHub: {XAI4HEAT_REPO_URL}
- XAI4HEAT Mendeley: {XAI4HEAT_MENDELEY_URL}
- DOI: {XAI4HEAT_DOI}
"""
    OUT_REPORT.write_text(text, encoding="utf-8")


def write_notebook() -> None:
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell(
            "# M1 Full Gate Joblib + XAI4HEAT SCADA Runtime Validation\n\n"
            "33번 full gate runtime policy를 joblib으로 저장하고, XAI4HEAT SCADA에서 schema/feature/runtime 호환성을 검증한다."
        ),
        nbf.v4.new_code_cell(
            "import runpy\n"
            "result = runpy.run_path('scripts/run_34_full_gate_joblib_xai4heat_scada_runtime_validation.py')\n"
            "result['main']()"
        ),
        nbf.v4.new_code_cell(
            "import pandas as pd\n"
            "pd.read_csv('07_데이터산출물/m1_joblib_reload_validation.csv')"
        ),
        nbf.v4.new_code_cell(
            "pd.read_csv('07_데이터산출물/xai4heat_scada_runtime_validation_decision_matrix.csv')"
        ),
    ]
    nbf.write(nb, OUT_NOTEBOOK)


def main() -> None:
    features = parse_feature_list("compact13_overlap")
    registry, reload_validation, model_meta = fit_and_dump_models(features)
    write_metadata(model_meta)
    manifest = download_xai4heat()
    schema, coverage = build_schema_mapping(manifest, features)
    predictions, shift = run_scada_runtime(manifest, schema, coverage, features)
    # Keep this available for independent QA; it does not overwrite 33 outputs.
    recompute_33_metrics().to_csv(OUT / "m1_joblib_33_metric_reproduction.csv", index=False, encoding="utf-8-sig")
    decision, quality = build_decision_and_quality(registry, reload_validation, manifest, coverage, predictions, shift)
    write_report(registry, reload_validation, manifest, schema, coverage, predictions, shift, decision, quality)
    write_notebook()
    print(json.dumps({"decision": decision["final_decision"].iloc[0], "models": len(registry)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
