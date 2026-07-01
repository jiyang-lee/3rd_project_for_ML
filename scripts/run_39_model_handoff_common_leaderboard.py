from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import traceback
import zipfile
from pathlib import Path
from typing import Any

import joblib
import nbformat as nbf
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, precision_recall_fscore_support


OWNER_ZIP_NAMES = {
    "hsj": "model_handoff_hsj.zip",
    "osj": "model_handoff_osj.zip",
    "nyj": "model_handoff_nyj.zip",
    "ljy": "model_handoff_ljy.zip",
    "ljy2": "model_total_handoff_ljy2.zip",
}

FEATURE_KEYS = {
    "feature_columns",
    "features",
    "input_features",
    "model_feature_columns",
    "required_features",
    "selected_feature_columns",
}

DEFAULT_THRESHOLD = 0.5
HSJ_STATS = {"mean", "std", "min", "max", "first", "last", "delta", "missing_rate", "slope"}
NYJ_STATS = {"mean", "std", "min", "max", "slope"}
COMPACT_STATS = {
    "last_minus_first",
    "last_1d_mean_minus_prev_6d_mean",
    "last_12h_mean_minus_prev_12h_mean",
    "last_6h_mean_minus_prev_6h_mean",
    "last_1d_std_minus_prev_6d_std",
}
DIRECT_META_FEATURES = {"row_count", "feature_row_count", "feature_sensor_count"}
_RUN36 = None


def paths() -> dict[str, Path]:
    root = Path.cwd()
    base = root / "10_모델비교"
    return {
        "root": root,
        "base": base,
        "zip": base / "00_원본ZIP",
        "extract": base / "01_압축해제",
        "dataset": base / "02_공통평가셋",
        "notebook": base / "03_노트북",
        "out": base / "04_산출물",
        "report": base / "05_보고서",
        "source_dataset": root / "09_실험라인" / "m1_m2_standard_pre_event" / "outputs" / "standard_feature_pool.csv",
        "source_front_gate_dataset": root / "07_데이터산출물" / "m1_fault_gate_lock_predictions.csv",
    }


PATHS = paths()


def owner_zip_sources() -> dict[str, list[Path]]:
    return {
        "hsj": [Path(r"C:\Users\Admin\Desktop\model_handoff_hsj.zip")],
        "osj": [Path(r"C:\Users\Admin\Desktop\model_handoff_osj.zip")],
        "nyj": [Path(r"C:\Users\Admin\Desktop\model_handoff_nyj.zip")],
        "ljy": [Path(r"C:\Users\Admin\Desktop\model_handoff_ljy.zip")],
        "ljy2": [
            PATHS["root"] / "08_모델산출물" / "heatgrid_project_total_handoff_ljy2.zip",
            PATHS["zip"] / "model_total_handoff_ljy2.zip",
            Path(r"C:\Users\Admin\Desktop\heatgrid_project_total_handoff_ljy2.zip"),
            Path(r"C:\Users\Admin\Desktop\model_total_handoff_ljy2.zip"),
        ],
    }


def ensure_dirs() -> None:
    for key in ["zip", "extract", "dataset", "notebook", "out", "report"]:
        PATHS[key].mkdir(parents=True, exist_ok=True)


def source_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PATHS["root"], text=True).strip()
    except Exception:
        return "unknown"


def import_run36():
    global _RUN36
    if _RUN36 is not None:
        return _RUN36
    path = PATHS["root"] / "scripts" / "run_36_m1_m2_standard_pre_event.py"
    spec = importlib.util.spec_from_file_location("run36", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    _RUN36 = module
    return module


def copy_and_extract_zips() -> pd.DataFrame:
    rows = []
    for owner, sources in owner_zip_sources().items():
        source = next((candidate for candidate in sources if candidate.exists()), sources[0])
        target_zip = PATHS["zip"] / OWNER_ZIP_NAMES[owner]
        owner_extract = PATHS["extract"] / owner
        if not source.exists():
            rows.append(
                {
                    "owner": owner,
                    "source_zip": str(source),
                    "copied_zip": str(target_zip),
                    "exists": False,
                    "entry_count": 0,
                    "total_uncompressed_bytes": 0,
                    "status": "missing_source_zip",
                }
            )
            continue

        if source.resolve() != target_zip.resolve():
            shutil.copy2(source, target_zip)
        if owner_extract.exists():
            shutil.rmtree(owner_extract)
        owner_extract.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(target_zip) as zf:
            entries = zf.infolist()
            zf.extractall(owner_extract)
        rows.append(
            {
                "owner": owner,
                "source_zip": str(source),
                "copied_zip": str(target_zip),
                "exists": True,
                "entry_count": len(entries),
                "total_uncompressed_bytes": int(sum(item.file_size for item in entries)),
                "status": "copied_and_extracted",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(PATHS["out"] / "zip_inventory.csv", index=False, encoding="utf-8-sig")
    return df


def load_json(path: Path) -> Any:
    for encoding in ["utf-8-sig", "utf-8", "cp949"]:
        try:
            return json.loads(path.read_text(encoding=encoding))
        except UnicodeDecodeError:
            continue
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def iter_feature_lists(obj: Any, path: str = "") -> list[tuple[str, list[str]]]:
    found: list[tuple[str, list[str]]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key in FEATURE_KEYS and isinstance(value, list) and all(isinstance(item, str) for item in value):
                found.append((child_path, list(value)))
            found.extend(iter_feature_lists(value, child_path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            found.extend(iter_feature_lists(value, f"{path}[{idx}]"))
    return found


def iter_thresholds(obj: Any, path: str = "") -> list[tuple[str, float]]:
    found: list[tuple[str, float]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else str(key)
            if "threshold" in str(key).lower() and isinstance(value, (int, float)):
                found.append((child_path, float(value)))
            elif "threshold" in str(key).lower() and isinstance(value, str):
                try:
                    found.append((child_path, float(value)))
                except ValueError:
                    pass
            found.extend(iter_thresholds(value, child_path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            found.extend(iter_thresholds(value, f"{path}[{idx}]"))
    return found


def nearby_json_files(model_path: Path) -> list[Path]:
    candidates = list(model_path.parent.glob("*.json"))
    candidates.extend(model_path.parents[0].glob("*metadata*.json"))
    candidates.extend(model_path.parents[0].glob("*meta*.json"))
    try:
        candidates.extend(model_path.parents[1].glob("*.json"))
    except IndexError:
        pass
    seen = set()
    ordered = []
    model_tokens = set(model_path.stem.lower().replace("-", "_").split("_"))
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        tokens = set(candidate.stem.lower().replace("-", "_").split("_"))
        score = len(model_tokens & tokens)
        ordered.append((score, candidate))
    ordered.sort(key=lambda item: (-item[0], str(item[1])))
    return [candidate for _, candidate in ordered]


def extract_metadata(model_path: Path) -> dict[str, Any]:
    metadata_path = ""
    metadata_feature_source = ""
    required_features: list[str] = []
    threshold = np.nan
    threshold_source = ""

    for json_path in nearby_json_files(model_path):
        try:
            obj = load_json(json_path)
        except Exception:
            continue
        feature_lists = iter_feature_lists(obj)
        if feature_lists and not required_features:
            metadata_feature_source, required_features = max(feature_lists, key=lambda item: len(item[1]))
            metadata_path = str(json_path.relative_to(PATHS["base"]))
        thresholds = iter_thresholds(obj)
        if thresholds and pd.isna(threshold):
            threshold_source, threshold = thresholds[0]
            if not metadata_path:
                metadata_path = str(json_path.relative_to(PATHS["base"]))
        if required_features and not pd.isna(threshold):
            break

    return {
        "metadata_path": metadata_path,
        "metadata_feature_source": metadata_feature_source,
        "metadata_required_features": required_features,
        "declared_threshold": threshold,
        "threshold_source": threshold_source,
    }


def infer_task_family(owner: str, model_path: Path) -> str:
    text = str(model_path).lower()
    if "leadtime" in text:
        return "leadtime"
    if "priority" in text:
        return "priority"
    if "activity_gate" in text:
        return "activity_gate"
    if "task_gate" in text:
        return "task_gate"
    if "front_gate" in text or "fault_gate" in text:
        return "front_gate"
    if "isolation" in text or "mahalanobis" in text or "anomaly" in text:
        return "anomaly"
    if "risk" in text:
        return "risk"
    if owner == "nyj" or "early_detection" in text or "hybrid" in text or "pre_event" in text:
        return "early_detection"
    if owner == "hsj" and ("lightgbm" in text or "random_forest" in text or "baseline" in text):
        return "pre_event_candidate"
    return "unknown"


def discover_models() -> pd.DataFrame:
    rows = []
    for owner in owner_zip_sources():
        owner_root = PATHS["extract"] / owner
        for model_path in sorted(owner_root.rglob("*.joblib")):
            meta = extract_metadata(model_path)
            rows.append(
                {
                    "owner": owner,
                    "model_file": model_path.name,
                    "artifact_path": str(model_path.relative_to(PATHS["base"])),
                    "task_family": infer_task_family(owner, model_path),
                    "metadata_path": meta["metadata_path"],
                    "metadata_feature_source": meta["metadata_feature_source"],
                    "metadata_required_feature_count": len(meta["metadata_required_features"]),
                    "declared_threshold": meta["declared_threshold"],
                    "threshold_source": meta["threshold_source"],
                }
            )
    registry = pd.DataFrame(rows)
    registry.to_csv(PATHS["out"] / "model_registry.csv", index=False, encoding="utf-8-sig")
    return registry


def feature_names_from_model(model: Any) -> list[str]:
    if isinstance(model, dict):
        for key in ["feature_columns", "feature_names", "input_features", "model_feature_columns", "selected_feature_columns"]:
            value = model.get(key)
            if isinstance(value, list) and all(isinstance(item, (str, np.str_)) for item in value):
                return [str(item) for item in value]
        for key in ["model", "pipeline", "nb_pipeline"]:
            if key in model:
                names = feature_names_from_model(model[key])
                if names:
                    return names

    candidates: list[Any] = []
    candidates.append(model)
    if hasattr(model, "named_steps") and model.named_steps:
        candidates.extend(model.named_steps.values())
        candidates.append(list(model.named_steps.values())[-1])
    for candidate in candidates:
        names = getattr(candidate, "feature_names_in_", None)
        if names is not None:
            return [str(item) for item in list(names)]
        names = getattr(candidate, "feature_name_", None)
        if names is not None:
            return [str(item) for item in list(names)]
        booster = getattr(candidate, "booster_", None)
        if booster is not None and hasattr(booster, "feature_name"):
            return [str(item) for item in list(booster.feature_name())]
    return []


def threshold_from_model_object(model: Any) -> float:
    thresholds = iter_thresholds(model)
    if thresholds:
        return float(thresholds[0][1])
    return np.nan


def unwrap_predictor(model: Any) -> Any:
    if isinstance(model, dict):
        for key in ["model", "pipeline", "nb_pipeline"]:
            value = model.get(key)
            if value is not None and hasattr(value, "predict_proba"):
                return value
    return model


def class_one_probability(model: Any, x: pd.DataFrame) -> np.ndarray:
    model = unwrap_predictor(model)
    if not hasattr(model, "predict_proba"):
        raise ValueError("model_has_no_predict_proba")
    probabilities = model.predict_proba(x)
    classes = getattr(model, "classes_", None)
    if classes is None and hasattr(model, "named_steps") and model.named_steps:
        classes = getattr(list(model.named_steps.values())[-1], "classes_", None)
    if classes is None:
        if probabilities.ndim == 2 and probabilities.shape[1] == 2:
            return probabilities[:, 1]
        raise ValueError("model_classes_unavailable")
    classes_list = list(classes)
    if 1 in classes_list:
        return probabilities[:, classes_list.index(1)]
    if "1" in classes_list:
        return probabilities[:, classes_list.index("1")]
    if True in classes_list:
        return probabilities[:, classes_list.index(True)]
    if probabilities.ndim == 2 and probabilities.shape[1] == 2:
        return probabilities[:, 1]
    raise ValueError(f"positive_class_not_found: {classes_list}")


def metric_row(y_true: pd.Series, probability: np.ndarray, threshold: float) -> dict[str, Any]:
    y = np.asarray(y_true).astype(int)
    pred = (np.asarray(probability).astype(float) >= float(threshold)).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    precision, recall, f1, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    return {
        "rows": int(len(y)),
        "normal_rows": int((y == 0).sum()),
        "pre_event_rows": int((y == 1).sum()),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "normal_fpr": float(fp / (fp + tn)) if (fp + tn) else np.nan,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def load_evaluation_dataset() -> pd.DataFrame:
    source = PATHS["source_dataset"]
    if not source.exists():
        raise FileNotFoundError(source)
    target = PATHS["dataset"] / "common_pre_event_evaluation_dataset.csv"
    df = pd.read_csv(source)
    df.to_csv(target, index=False, encoding="utf-8-sig")

    spec = """# 공통 평가셋 기준

- source: `09_실험라인/m1_m2_standard_pre_event/outputs/standard_feature_pool.csv`
- evaluation filter: `main_eligible == True`
- target: `y`
- label meaning: `normal=0`, `pre_event=1`
- purpose: handoff 모델을 같은 입력 표와 같은 지표로 평가 가능한지 확인한다.
- conservative rule: 필요한 feature가 정확히 모두 있는 모델만 성능 리더보드에 포함한다.
"""
    (PATHS["dataset"] / "label_policy.md").write_text(spec, encoding="utf-8")
    return df


def load_front_gate_evaluation_dataset() -> pd.DataFrame:
    source = PATHS["source_front_gate_dataset"]
    if not source.exists():
        raise FileNotFoundError(source)
    df = pd.read_csv(source)
    df = df.loc[df["dataset"].eq("fault_no_overlap") & df["feature_set"].eq("compact13")].copy()
    df = df.rename(columns={"source_id": "sample_id", "y_true": "y"})
    df["manufacturer"] = "M1"
    df["main_eligible"] = True
    if "expected_sample_count" not in df.columns:
        df["expected_sample_count"] = 1008
    keep_columns = [
        "sample_id",
        "manufacturer",
        "source_event_id",
        "fault_event_id",
        "disturbance_row_id",
        "substation_id",
        "window_policy",
        "window_start",
        "window_end",
        "coverage_rate",
        "main_eligible",
        "expected_sample_count",
        "target_class",
        "y",
    ]
    df = df[[col for col in keep_columns if col in df.columns]].drop_duplicates("sample_id").reset_index(drop=True)
    target = PATHS["dataset"] / "common_front_gate_evaluation_dataset.csv"
    df.to_csv(target, index=False, encoding="utf-8-sig")

    spec = """# Front gate 공통 평가셋 기준

- source: `07_데이터산출물/m1_fault_gate_lock_predictions.csv`
- filter: `dataset == fault_no_overlap`, `feature_set == compact13`
- evaluation rows: M1 normal vs fault 90 rows
- target: `y`
- label meaning: `normal=0`, `fault=1`
- purpose: front gate 모델을 같은 입력 row와 같은 metric으로 평가한다.
- conservative rule: 원본 PreDist 7일 window에서 required feature를 재생성할 수 있는 모델만 포함한다.
"""
    (PATHS["dataset"] / "front_gate_label_policy.md").write_text(spec, encoding="utf-8")
    return df


def bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def clean_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def derived_series(window: pd.DataFrame, signal: str) -> pd.Series | None:
    def col(name: str) -> pd.Series:
        if name in window.columns:
            return clean_numeric(window[name])
        return pd.Series(np.nan, index=window.index, dtype="float64")

    if signal == "dT":
        return col("p_net_supply_temperature") - col("p_net_return_temperature")
    if signal == "dev":
        return col("s_hc1_supply_temperature") - col("s_hc1_supply_temperature_setpoint")
    if signal == "energy_diff":
        return col("p_net_meter_energy").diff()
    if signal == "volume_diff":
        return col("p_net_meter_volume").diff()
    if signal == "dhw_dev":
        return col("s_dhw_supply_temperature") - col("s_dhw_supply_temperature_setpoint")
    if signal == "dhw_strat":
        return col("s_dhw_upper_storage_temperature") - col("s_dhw_lower_storage_temperature")
    return None


def feature_series(window: pd.DataFrame, signal: str) -> pd.Series:
    derived = derived_series(window, signal)
    if derived is not None:
        return derived
    if signal in window.columns:
        return clean_numeric(window[signal])
    return pd.Series(np.nan, index=window.index, dtype="float64")


def slope_value(series: pd.Series) -> float:
    values = clean_numeric(series).to_numpy(dtype=float)
    mask = np.isfinite(values)
    if mask.sum() < 2:
        return np.nan
    x = np.arange(len(values), dtype=float)[mask]
    y = values[mask]
    return float(np.polyfit(x, y, 1)[0])


def stat_value(window: pd.DataFrame, signal: str, stat: str, start: pd.Timestamp | None = None, end: pd.Timestamp | None = None) -> float:
    series = feature_series(window, signal)
    clean = clean_numeric(series).dropna()
    if stat == "missing_rate":
        if len(series) == 0:
            return 1.0
        return float(series.isna().mean())
    if clean.empty:
        return np.nan
    if stat == "mean":
        return float(clean.mean())
    if stat == "std":
        return float(clean.std(ddof=0))
    if stat == "min":
        return float(clean.min())
    if stat == "max":
        return float(clean.max())
    if stat == "first":
        return float(clean.iloc[0])
    if stat == "last":
        return float(clean.iloc[-1])
    if stat == "delta":
        return float(clean.iloc[-1] - clean.iloc[0]) if len(clean) >= 2 else np.nan
    if stat == "slope":
        return slope_value(series)
    if stat == "last_minus_first":
        return float(clean.iloc[-1] - clean.iloc[0]) if len(clean) >= 2 else np.nan
    run36_style = {"last_1d_mean_minus_prev_6d_mean", "last_12h_mean_minus_prev_12h_mean", "last_6h_mean_minus_prev_6h_mean", "last_1d_std_minus_prev_6d_std"}
    if stat in run36_style:
        if signal not in window.columns and derived_series(window, signal) is not None:
            window = window.copy()
            window[signal] = derived_series(window, signal)
        run36 = import_run36()
        if signal not in window.columns:
            return np.nan
        start = pd.Timestamp(start) if start is not None else window["timestamp"].min()
        end = pd.Timestamp(end) if end is not None else window["timestamp"].max() + pd.Timedelta(minutes=10)
        return float(run36.compute_feature(window, signal, stat, start, end))
    return np.nan


def parse_adapter_feature(feature: str) -> tuple[str, str, str] | None:
    if feature in DIRECT_META_FEATURES:
        return ("meta", feature, "")
    if "__" in feature:
        signal, stat = feature.rsplit("__", 1)
        if stat in HSJ_STATS or stat in COMPACT_STATS:
            return ("hsj_stat", signal, stat)
    for stat in NYJ_STATS:
        suffix = f"_{stat}"
        if feature.endswith(suffix):
            signal = feature[: -len(suffix)]
            if signal:
                return ("nyj_stat", signal, stat)
    return None


def adapter_supported_features(features: list[str]) -> tuple[bool, list[str]]:
    unsupported = [feature for feature in features if parse_adapter_feature(feature) is None]
    return (len(unsupported) == 0, unsupported)


def build_adapter_feature_frame(eval_df: pd.DataFrame, required_features: list[str]) -> pd.DataFrame:
    run36 = import_run36()
    rows = []
    parsed = {feature: parse_adapter_feature(feature) for feature in required_features}

    for _, row in eval_df.iterrows():
        manufacturer = str(row["manufacturer"])
        substation_id = int(row["substation_id"])
        start = pd.Timestamp(row["window_start"])
        end = pd.Timestamp(row["window_end"])
        operational = run36.load_operational(manufacturer, substation_id)
        window = run36.window_slice(operational, start, end)

        item: dict[str, Any] = {}
        for feature, parsed_feature in parsed.items():
            if parsed_feature is None:
                item[feature] = np.nan
                continue
            kind, signal, stat = parsed_feature
            if kind == "meta":
                if signal == "row_count":
                    item[feature] = int(row.get("expected_sample_count", len(window)))
                elif signal == "feature_row_count":
                    item[feature] = int(len(window))
                elif signal == "feature_sensor_count":
                    sensor_names = sorted(
                        {
                            parsed_item[1]
                            for parsed_item in parsed.values()
                            if parsed_item is not None and parsed_item[0] in {"hsj_stat", "nyj_stat"}
                        }
                    )
                    item[feature] = int(sum(feature_series(window, sensor).notna().any() for sensor in sensor_names))
                else:
                    item[feature] = np.nan
            else:
                item[feature] = stat_value(window, signal, stat, start=start, end=end)
        rows.append(item)
    return pd.DataFrame(rows, columns=required_features)


def evaluate_front_gate_models(registry: pd.DataFrame, dataset: pd.DataFrame) -> dict[str, pd.DataFrame]:
    eval_df = dataset.copy()
    y = eval_df["y"].astype(int)
    adapter_cache: dict[tuple[str, ...], pd.DataFrame] = {}

    load_audit = pd.read_csv(PATHS["out"] / "model_load_audit.csv") if (PATHS["out"] / "model_load_audit.csv").exists() else pd.DataFrame()
    schema_rows = []
    leaderboard_rows = []
    prediction_rows = []
    include_families = {"front_gate"}

    for _, row in registry.iterrows():
        model_path = PATHS["base"] / row["artifact_path"]
        model = None
        load_status = "not_attempted"
        load_error = ""
        model_features: list[str] = []
        metadata_features: list[str] = []
        model_threshold = np.nan
        multi_window_required = False

        try:
            model = joblib.load(model_path)
            load_status = "loaded"
            model_features = feature_names_from_model(model)
            model_threshold = threshold_from_model_object(model)
            multi_window_required = isinstance(model, dict) and (
                "event_rule" in model or "persub_detectors" in model or "covered_substations" in model
            )
        except Exception as exc:
            load_status = "load_failed"
            load_error = f"{type(exc).__name__}: {exc}"

        if row["metadata_path"]:
            try:
                obj = load_json(PATHS["base"] / row["metadata_path"])
                feature_lists = iter_feature_lists(obj)
                if feature_lists:
                    _, metadata_features = max(feature_lists, key=lambda item: len(item[1]))
            except Exception:
                metadata_features = []

        required_features = model_features or metadata_features
        task_family = row["task_family"]
        threshold = row["declared_threshold"]
        if not pd.isna(threshold):
            threshold_used = float(threshold)
            threshold_source = row["threshold_source"] or "metadata"
        elif not pd.isna(model_threshold):
            threshold_used = float(model_threshold)
            threshold_source = "model_object"
        else:
            threshold_used = DEFAULT_THRESHOLD
            threshold_source = "default_0.5"

        same_pool_fit_candidate = (
            row["owner"] == "ljy2"
            and row["model_file"] == "m1_m2_system_stratified_pre_event_candidate.joblib"
            and isinstance(model, dict)
            and str(model.get("status", "")).startswith("global_not_locked")
        )

        if task_family not in include_families:
            eligibility = "excluded_task_family"
            reason = f"target_mismatch:{task_family}"
        elif load_status != "loaded":
            eligibility = "excluded_load_failed"
            reason = load_error
        elif same_pool_fit_candidate:
            eligibility = "excluded_in_sample_candidate"
            reason = "trained_on_same_standard_feature_pool_main_eligible_rows; use only as reference_not_ranked"
        elif multi_window_required:
            eligibility = "excluded_execution_unit_mismatch"
            reason = "multi_window_k_rule_requires_window_sequence"
        elif not required_features:
            eligibility = "excluded_schema_unavailable"
            reason = "required_features_unavailable_from_model_or_metadata"
        else:
            adapter_ok, unsupported = adapter_supported_features(required_features)
            if adapter_ok:
                eligibility = "eligible_regenerated_raw_7d_features"
                reason = "features_regenerated_from_predist_operational_windows"
            else:
                eligibility = "excluded_schema_mismatch"
                reason = f"unsupported_adapter_features:{len(unsupported)}"

        schema_rows.append(
            {
                "owner": row["owner"],
                "model_file": row["model_file"],
                "artifact_path": row["artifact_path"],
                "task_family": task_family,
                "eligibility": eligibility,
                "reason": reason,
                "required_feature_count": len(required_features),
                "threshold_used": threshold_used,
                "threshold_source": threshold_source,
            }
        )
        if not eligibility.startswith("eligible"):
            continue

        try:
            if (
                task_family == "front_gate"
                and row["owner"] in {"ljy", "ljy2"}
                and row["model_file"] == "m1_fault_gate_rf_depth3.joblib"
            ):
                locked = pd.read_csv(PATHS["source_front_gate_dataset"])
                locked = locked.loc[
                    locked["dataset"].eq("fault_no_overlap")
                    & locked["feature_set"].eq("compact13")
                    & locked["model"].eq("random_forest_balanced_depth3")
                ].copy()
                locked = locked.rename(columns={"source_id": "sample_id"})
                probability = (
                    eval_df[["sample_id"]]
                    .merge(locked[["sample_id", "probability_target"]], on="sample_id", how="left")["probability_target"]
                    .astype(float)
                    .to_numpy()
                )
                eligibility = "eligible_locked_front_gate_oof_predictions"
                schema_rows[-1]["eligibility"] = eligibility
                schema_rows[-1]["reason"] = "canonical_locked_fold_predictions_from_m1_fault_gate_lock_predictions"
            else:
                cache_key = tuple(required_features)
                if cache_key not in adapter_cache:
                    adapter_cache[cache_key] = build_adapter_feature_frame(eval_df, required_features)
                x = adapter_cache[cache_key]
                probability = class_one_probability(model, x)
            metrics = metric_row(y, probability, threshold_used)
            leaderboard_rows.append(
                {
                    "owner": row["owner"],
                    "model_file": row["model_file"],
                    "artifact_path": row["artifact_path"],
                    "task_family": task_family,
                    "evaluation_basis": eligibility,
                    "threshold": threshold_used,
                    "feature_count": len(required_features),
                    **metrics,
                }
            )
            for sample_id, true_y, prob in zip(eval_df["sample_id"], y, probability):
                prediction_rows.append(
                    {
                        "owner": row["owner"],
                        "model_file": row["model_file"],
                        "sample_id": sample_id,
                        "y_true": int(true_y),
                        "probability": float(prob),
                        "threshold": threshold_used,
                        "y_pred": int(float(prob) >= threshold_used),
                        "evaluation_basis": eligibility,
                    }
                )
        except Exception as exc:
            schema_rows[-1]["eligibility"] = "excluded_prediction_failed"
            schema_rows[-1]["reason"] = f"{type(exc).__name__}: {exc}"
            schema_rows[-1]["prediction_traceback"] = traceback.format_exc(limit=3)

    schema_audit = pd.DataFrame(schema_rows)
    leaderboard = pd.DataFrame(leaderboard_rows)
    predictions = pd.DataFrame(prediction_rows)
    leaderboard_columns = [
        "owner",
        "model_file",
        "artifact_path",
        "task_family",
        "evaluation_basis",
        "threshold",
        "feature_count",
        "rows",
        "normal_rows",
        "pre_event_rows",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "normal_fpr",
        "tn",
        "fp",
        "fn",
        "tp",
    ]
    if leaderboard.empty:
        leaderboard = pd.DataFrame(columns=leaderboard_columns)
    else:
        leaderboard = leaderboard.sort_values(["balanced_accuracy", "normal_fpr", "recall"], ascending=[False, True, False])
    if predictions.empty:
        predictions = pd.DataFrame(columns=["owner", "model_file", "sample_id", "y_true", "probability", "threshold", "y_pred", "evaluation_basis"])

    summary = pd.DataFrame(
        [
            {
                "evaluation_rows": int(len(eval_df)),
                "normal_rows": int((y == 0).sum()),
                "fault_rows": int((y == 1).sum()),
                "model_count": int(len(registry)),
                "loaded_model_count": int((load_audit["load_status"] == "loaded").sum()) if not load_audit.empty else np.nan,
                "eligible_model_count": int(schema_audit["eligibility"].astype(str).str.startswith("eligible").sum()),
                "leaderboard_model_count": int(len(leaderboard)),
                "source_commit": source_commit_hash(),
            }
        ]
    )
    schema_audit.to_csv(PATHS["out"] / "front_gate_schema_match_audit.csv", index=False, encoding="utf-8-sig")
    leaderboard.to_csv(PATHS["out"] / "front_gate_leaderboard.csv", index=False, encoding="utf-8-sig")
    predictions.to_csv(PATHS["out"] / "front_gate_predictions.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(PATHS["out"] / "front_gate_evaluation_summary.csv", index=False, encoding="utf-8-sig")
    return {"schema_audit": schema_audit, "leaderboard": leaderboard, "predictions": predictions, "summary": summary}


def evaluate_models(registry: pd.DataFrame, dataset: pd.DataFrame) -> dict[str, pd.DataFrame]:
    eval_df = dataset.loc[bool_series(dataset["main_eligible"])].copy()
    y = eval_df["y"].astype(int)
    adapter_cache: dict[tuple[str, ...], pd.DataFrame] = {}

    load_rows = []
    schema_rows = []
    leaderboard_rows = []
    prediction_rows = []

    include_families = {"risk", "early_detection", "pre_event", "pre_event_candidate"}

    for _, row in registry.iterrows():
        model_path = PATHS["base"] / row["artifact_path"]
        load_status = "not_attempted"
        load_error = ""
        model_type = ""
        model = None
        model_features: list[str] = []
        metadata_features: list[str] = []
        model_threshold = np.nan
        multi_window_required = False

        try:
            model = joblib.load(model_path)
            load_status = "loaded"
            model_type = type(model).__name__
            model_features = feature_names_from_model(model)
            model_threshold = threshold_from_model_object(model)
            multi_window_required = isinstance(model, dict) and (
                "event_rule" in model or "persub_detectors" in model or "covered_substations" in model
            )
        except Exception as exc:
            load_status = "load_failed"
            load_error = f"{type(exc).__name__}: {exc}"

        if row["metadata_path"]:
            try:
                obj = load_json(PATHS["base"] / row["metadata_path"])
                feature_lists = iter_feature_lists(obj)
                if feature_lists:
                    _, metadata_features = max(feature_lists, key=lambda item: len(item[1]))
            except Exception:
                metadata_features = []

        required_features = model_features or metadata_features
        task_family = row["task_family"]
        threshold = row["declared_threshold"]
        if not pd.isna(threshold):
            threshold_used = float(threshold)
            threshold_source = row["threshold_source"] or "metadata"
        elif not pd.isna(model_threshold):
            threshold_used = float(model_threshold)
            threshold_source = "model_object"
        else:
            threshold_used = DEFAULT_THRESHOLD
            threshold_source = "default_0.5"

        if task_family not in include_families:
            eligibility = "excluded_task_family"
            reason = f"target_mismatch:{task_family}"
        elif load_status != "loaded":
            eligibility = "excluded_load_failed"
            reason = load_error
        elif multi_window_required:
            eligibility = "excluded_execution_unit_mismatch"
            reason = "multi_window_k_rule_requires_window_sequence"
        elif not required_features:
            eligibility = "excluded_schema_unavailable"
            reason = "required_features_unavailable_from_model_or_metadata"
        else:
            missing = sorted(set(required_features) - set(eval_df.columns))
            if missing:
                adapter_ok, unsupported = adapter_supported_features(required_features)
                if adapter_ok and task_family in include_families:
                    eligibility = "eligible_regenerated_raw_7d_features"
                    reason = "features_regenerated_from_predist_operational_windows"
                else:
                    eligibility = "excluded_schema_mismatch"
                    if unsupported:
                        reason = f"unsupported_adapter_features:{len(unsupported)}"
                    else:
                        reason = f"missing_features:{len(missing)}"
            else:
                eligibility = "eligible_existing_common_dataset"
                reason = "features_present_in_common_dataset"

        missing_features = sorted(set(required_features) - set(eval_df.columns)) if required_features else []
        extra_dataset_features = sorted(set(eval_df.columns) - set(required_features)) if required_features else []

        load_rows.append(
            {
                "owner": row["owner"],
                "model_file": row["model_file"],
                "artifact_path": row["artifact_path"],
                "task_family": task_family,
                "load_status": load_status,
                "model_type": model_type,
                "load_error": load_error,
            }
        )
        schema_rows.append(
            {
                "owner": row["owner"],
                "model_file": row["model_file"],
                "artifact_path": row["artifact_path"],
                "task_family": task_family,
                "eligibility": eligibility,
                "reason": reason,
                "required_feature_count": len(required_features),
                "metadata_required_feature_count": int(row["metadata_required_feature_count"]),
                "model_feature_count": len(model_features),
                "missing_feature_count": len(missing_features),
                "missing_feature_examples": "; ".join(missing_features[:20]),
                "extra_dataset_feature_count": len(extra_dataset_features),
                "threshold_used": threshold_used,
                "threshold_source": threshold_source,
            }
        )

        if not eligibility.startswith("eligible"):
            continue

        try:
            if eligibility == "eligible_regenerated_raw_7d_features":
                cache_key = tuple(required_features)
                if cache_key not in adapter_cache:
                    adapter_cache[cache_key] = build_adapter_feature_frame(eval_df, required_features)
                x = adapter_cache[cache_key]
            else:
                x = eval_df[required_features]
            probability = class_one_probability(model, x)
            metrics = metric_row(y, probability, threshold_used)
            leaderboard_rows.append(
                {
                    "owner": row["owner"],
                    "model_file": row["model_file"],
                    "artifact_path": row["artifact_path"],
                    "task_family": task_family,
                    "evaluation_basis": eligibility,
                    "threshold": threshold_used,
                    "feature_count": len(required_features),
                    **metrics,
                }
            )
            ids = eval_df["sample_id"] if "sample_id" in eval_df.columns else pd.Series(range(len(eval_df)))
            manufacturers = eval_df["manufacturer"] if "manufacturer" in eval_df.columns else pd.Series([""] * len(eval_df))
            for sample_id, manufacturer, true_y, prob in zip(ids, manufacturers, y, probability):
                prediction_rows.append(
                    {
                        "owner": row["owner"],
                        "model_file": row["model_file"],
                        "sample_id": sample_id,
                        "manufacturer": manufacturer,
                        "y_true": int(true_y),
                        "probability": float(prob),
                        "threshold": threshold_used,
                        "y_pred": int(float(prob) >= threshold_used),
                        "evaluation_basis": eligibility,
                    }
                )
        except Exception as exc:
            schema_rows[-1]["eligibility"] = "excluded_prediction_failed"
            schema_rows[-1]["reason"] = f"{type(exc).__name__}: {exc}"
            schema_rows[-1]["prediction_traceback"] = traceback.format_exc(limit=3)

    load_audit = pd.DataFrame(load_rows)
    schema_audit = pd.DataFrame(schema_rows)
    leaderboard = pd.DataFrame(leaderboard_rows)
    predictions = pd.DataFrame(prediction_rows)

    leaderboard_columns = [
        "owner",
        "model_file",
        "artifact_path",
        "task_family",
        "evaluation_basis",
        "threshold",
        "feature_count",
        "rows",
        "normal_rows",
        "pre_event_rows",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "normal_fpr",
        "tn",
        "fp",
        "fn",
        "tp",
    ]
    prediction_columns = ["owner", "model_file", "sample_id", "manufacturer", "y_true", "probability", "threshold", "y_pred"]
    if leaderboard.empty:
        leaderboard = pd.DataFrame(columns=leaderboard_columns)
    if predictions.empty:
        predictions = pd.DataFrame(columns=prediction_columns)

    if not leaderboard.empty:
        leaderboard = leaderboard.sort_values(["balanced_accuracy", "normal_fpr", "recall"], ascending=[False, True, False])

    load_audit.to_csv(PATHS["out"] / "model_load_audit.csv", index=False, encoding="utf-8-sig")
    schema_audit.to_csv(PATHS["out"] / "feature_schema_match_audit.csv", index=False, encoding="utf-8-sig")
    leaderboard.to_csv(PATHS["out"] / "common_pre_event_leaderboard.csv", index=False, encoding="utf-8-sig")
    predictions.to_csv(PATHS["out"] / "common_pre_event_predictions.csv", index=False, encoding="utf-8-sig")

    summary = pd.DataFrame(
        [
            {
                "evaluation_rows": int(len(eval_df)),
                "normal_rows": int((y == 0).sum()),
                "pre_event_rows": int((y == 1).sum()),
                "model_count": int(len(registry)),
                "loaded_model_count": int((load_audit["load_status"] == "loaded").sum()),
                "eligible_model_count": int(schema_audit["eligibility"].astype(str).str.startswith("eligible").sum()),
                "leaderboard_model_count": int(len(leaderboard)),
                "source_commit": source_commit_hash(),
            }
        ]
    )
    summary.to_csv(PATHS["out"] / "evaluation_summary.csv", index=False, encoding="utf-8-sig")

    return {
        "load_audit": load_audit,
        "schema_audit": schema_audit,
        "leaderboard": leaderboard,
        "predictions": predictions,
        "summary": summary,
    }


def md_table(df: pd.DataFrame, columns: list[str] | None = None, max_rows: int | None = None) -> str:
    if df.empty:
        return "_해당 없음_"
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


def write_report(results: dict[str, pd.DataFrame], front_results: dict[str, pd.DataFrame] | None = None) -> Path:
    leaderboard = results["leaderboard"]
    schema = results["schema_audit"]
    load_audit = results["load_audit"]
    summary = results["summary"].iloc[0].to_dict()
    excluded = schema.loc[schema["eligibility"] != "eligible"].copy()
    excluded = schema.loc[~schema["eligibility"].astype(str).str.startswith("eligible")].copy()
    included = schema.loc[schema["eligibility"].astype(str).str.startswith("eligible")].copy()
    front_leaderboard = pd.DataFrame() if front_results is None else front_results["leaderboard"]
    front_schema = pd.DataFrame() if front_results is None else front_results["schema_audit"]
    front_summary = {} if front_results is None else front_results["summary"].iloc[0].to_dict()
    front_excluded = (
        pd.DataFrame()
        if front_results is None
        else front_schema.loc[~front_schema["eligibility"].astype(str).str.startswith("eligible")].copy()
    )

    title = "모델 handoff 공통 평가 리더보드 보고서"
    body = f"""# {title}

## 개요

모델 handoff ZIP 5개를 `10_모델비교` 아래에 모으고, 같은 공통 평가셋에서 실제 로딩과 예측이 가능한 모델만 `normal vs pre_event` 조기탐지 리더보드에 포함했다.

이번 비교는 모델 목적이 다른 산출물을 억지로 한 순위에 넣지 않기 위해 보수적으로 진행했다. `leadtime`, `priority`, `front_gate`, `task_gate`, `activity_gate`, 순수 anomaly 모델은 target이 달라 pre_event 성능 순위에서 제외했다. 또한 `ljy2`의 system-stratified pre_event 후보는 같은 `standard_feature_pool.csv` main 평가 row로 fit된 candidate라 in-sample 점수로 보고 순위에서 제외했다. 공통 CSV에 feature가 없더라도 raw 7일 window에서 feature 계약을 정확히 재생성할 수 있는 모델은 별도 adapter로 평가했다.

## 무엇을 했는지

| 항목 | 값 |
|---|---:|
| 평가 row | {int(summary["evaluation_rows"])} |
| normal row | {int(summary["normal_rows"])} |
| pre_event row | {int(summary["pre_event_rows"])} |
| 발견 모델 수 | {int(summary["model_count"])} |
| 로딩 성공 모델 수 | {int(summary["loaded_model_count"])} |
| 리더보드 포함 모델 수 | {int(summary["leaderboard_model_count"])} |

## 왜 이렇게 했는지

공통 리더보드는 같은 label, 같은 row, 같은 metric에서만 의미가 있다. 그래서 모든 모델을 같은 112개 row와 같은 `normal/pre_event` label로 평가했다. 필요한 feature가 공통 CSV에 없을 때는 원본 PreDist operational window에서 통계 feature를 다시 계산했고, 재생성 규칙이 없는 feature는 임의로 채우지 않고 제외했다.

```mermaid
flowchart LR
  A["handoff ZIP 5개"] --> B["10_모델비교/00_원본ZIP"]
  B --> C["10_모델비교/01_압축해제"]
  C --> D["model registry"]
  D --> E["joblib load audit"]
  E --> F["feature schema audit"]
  F --> G["raw 7일 window feature 재생성"]
  G --> I["eligible 모델만 공통 평가"]
  I --> H["leaderboard + predictions + report"]
```

## 변경 내용

- 원본 ZIP 복사본과 압축 해제본을 `10_모델비교` 아래에 구성했다.
- `standard_feature_pool.csv`를 공통 평가셋으로 복사하고 label 기준을 문서화했다.
- 모델 registry, 로딩 감사, feature schema 감사, adapter feature 재생성, prediction, leaderboard CSV를 생성했다.
- 재실행 가능한 노트북 `03_노트북/01_model_handoff_common_leaderboard.ipynb`를 생성했다.

## 리더보드 포함 모델

{md_table(leaderboard, ["owner", "model_file", "task_family", "evaluation_basis", "threshold", "rows", "balanced_accuracy", "precision", "recall", "f1", "normal_fpr", "tp", "fp", "fn", "tn"] if not leaderboard.empty else None)}

## Front Gate 리더보드

Front gate는 `normal=0`, `fault=1` 기준의 별도 평가다. 평가 row는 {int(front_summary.get("evaluation_rows", 0)) if front_summary else 0}개이며, 이 표에는 target이 같은 `fault_gate` 모델만 포함했다. `pre_event`, `task_gate`, `activity_gate`는 점수가 계산 가능해도 목적이 달라 제외했다.

{md_table(front_leaderboard, ["owner", "model_file", "task_family", "evaluation_basis", "threshold", "rows", "balanced_accuracy", "precision", "recall", "f1", "normal_fpr", "tp", "fp", "fn", "tn"] if not front_leaderboard.empty else None)}

## 제외 모델 요약

{md_table(excluded, ["owner", "model_file", "task_family", "eligibility", "reason", "required_feature_count", "missing_feature_count", "missing_feature_examples"], max_rows=30)}

## Front Gate 제외 모델 요약

{md_table(front_excluded, ["owner", "model_file", "task_family", "eligibility", "reason", "required_feature_count", "threshold_used"], max_rows=30)}

## 검증

- `model_load_audit.csv`로 각 joblib 로딩 성공/실패를 기록했다.
- `feature_schema_match_audit.csv`로 required feature와 공통 평가셋 column의 정확한 매칭 여부를 기록했다.
- `common_pre_event_predictions.csv`의 prediction row는 리더보드 포함 모델 수와 평가 row 수를 곱한 값이어야 한다.
- `front_gate_predictions.csv`의 prediction row도 front gate 리더보드 포함 모델 수와 평가 row 수를 곱한 값이어야 한다.
- 노트북은 `nbclient`로 실행해 전체 셀이 에러 없이 끝나는지 확인 대상이다.

## 한계와 주의점

- 리더보드에 포함되지 않은 모델이 나쁜 모델이라는 뜻은 아니다. target이 다르거나 공통 feature schema가 맞지 않아 이번 기준에서는 공정 평가가 불가능하다는 뜻이다.
- adapter는 sensor 통계 feature와 직접 계산 가능한 derived feature만 재생성한다. anomaly score, rolling lag, configuration one-hot처럼 현재 handoff만으로 재현 불가능한 feature는 제외했다.
- ZIP별 학습 데이터와 label 정책은 서로 다를 수 있으므로, 이번 결과는 `normal vs pre_event` 공통 평가 기준의 1차 비교로만 해석한다.

## 다음에 볼 것

1. 제외 모델 중 실제로 비교해야 하는 모델은 feature 생성 pipeline 또는 inference contract를 함께 받아야 한다.
2. OSJ risk 모델처럼 feature 수가 큰 모델은 동일 feature table을 재현할 수 있는지 먼저 확인한다.
3. multi-window K-rule 모델은 단일 event-row 모델과 같은 표에 섞지 말고 별도 window-level 평가셋으로 비교한다.
"""
    path = PATHS["report"] / "01_model_handoff_common_leaderboard_보고서.md"
    path.write_text(body, encoding="utf-8")
    return path


def write_notebook() -> Path:
    notebook_path = PATHS["notebook"] / "01_model_handoff_common_leaderboard.ipynb"
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell(
            "# 모델 handoff 공통 평가 리더보드\n\n"
            "이 노트북은 `scripts/run_39_model_handoff_common_leaderboard.py`를 호출해 ZIP 복사/해제, 모델 로딩, "
            "feature schema 감사, 공통 평가 리더보드 생성을 재실행한다."
        ),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import importlib.util\n"
            "import pandas as pd\n\n"
            "ROOT = Path.cwd()\n"
            "SCRIPT = ROOT / 'scripts' / 'run_39_model_handoff_common_leaderboard.py'\n"
            "spec = importlib.util.spec_from_file_location('run39', SCRIPT)\n"
            "run39 = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(run39)\n"
            "results = run39.run_comparison(write_notebook_file=False)\n"
            "results['summary']"
        ),
        nbf.v4.new_markdown_cell("## 공통 평가 리더보드"),
        nbf.v4.new_code_cell(
            "leaderboard = pd.read_csv(ROOT / '10_모델비교' / '04_산출물' / 'common_pre_event_leaderboard.csv')\n"
            "leaderboard"
        ),
        nbf.v4.new_markdown_cell("## 제외 사유"),
        nbf.v4.new_code_cell(
            "schema = pd.read_csv(ROOT / '10_모델비교' / '04_산출물' / 'feature_schema_match_audit.csv')\n"
            "schema.loc[schema['eligibility'] != 'eligible', ['owner', 'model_file', 'task_family', 'eligibility', 'reason', 'missing_feature_count']].head(50)"
        ),
        nbf.v4.new_markdown_cell("## Front Gate 리더보드"),
        nbf.v4.new_code_cell(
            "front_leaderboard = pd.read_csv(ROOT / '10_모델비교' / '04_산출물' / 'front_gate_leaderboard.csv')\n"
            "front_leaderboard"
        ),
        nbf.v4.new_markdown_cell("## Front Gate 제외 사유"),
        nbf.v4.new_code_cell(
            "front_schema = pd.read_csv(ROOT / '10_모델비교' / '04_산출물' / 'front_gate_schema_match_audit.csv')\n"
            "front_schema.loc[~front_schema['eligibility'].str.startswith('eligible'), ['owner', 'model_file', 'task_family', 'eligibility', 'reason']].head(50)"
        ),
        nbf.v4.new_markdown_cell("## 검증"),
        nbf.v4.new_code_cell(
            "summary = pd.read_csv(ROOT / '10_모델비교' / '04_산출물' / 'evaluation_summary.csv').iloc[0]\n"
            "predictions = pd.read_csv(ROOT / '10_모델비교' / '04_산출물' / 'common_pre_event_predictions.csv')\n"
            "expected = int(summary['evaluation_rows']) * int(summary['leaderboard_model_count'])\n"
            "assert len(predictions) == expected, (len(predictions), expected)\n"
            "front_summary = pd.read_csv(ROOT / '10_모델비교' / '04_산출물' / 'front_gate_evaluation_summary.csv').iloc[0]\n"
            "front_predictions = pd.read_csv(ROOT / '10_모델비교' / '04_산출물' / 'front_gate_predictions.csv')\n"
            "front_expected = int(front_summary['evaluation_rows']) * int(front_summary['leaderboard_model_count'])\n"
            "assert len(front_predictions) == front_expected, (len(front_predictions), front_expected)\n"
            "print({'pre_event_prediction_rows': len(predictions), 'pre_event_expected_rows': expected, 'front_gate_prediction_rows': len(front_predictions), 'front_gate_expected_rows': front_expected})"
        ),
    ]
    nbf.write(nb, notebook_path)
    return notebook_path


def run_comparison(write_notebook_file: bool = True) -> dict[str, pd.DataFrame]:
    ensure_dirs()
    copy_and_extract_zips()
    dataset = load_evaluation_dataset()
    front_dataset = load_front_gate_evaluation_dataset()
    registry = discover_models()
    results = evaluate_models(registry, dataset)
    front_results = evaluate_front_gate_models(registry, front_dataset)
    write_report(results, front_results)
    if write_notebook_file:
        write_notebook()
    results["front_gate_summary"] = front_results["summary"]
    results["front_gate_leaderboard"] = front_results["leaderboard"]
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-notebook-write", action="store_true")
    args = parser.parse_args()
    results = run_comparison(write_notebook_file=not args.skip_notebook_write)
    summary = results["summary"].iloc[0].to_dict()
    front_summary = results["front_gate_summary"].iloc[0].to_dict()
    print(json.dumps({"pre_event": summary, "front_gate": front_summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
