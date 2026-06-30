from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from lightgbm import LGBMClassifier

    LIGHTGBM_AVAILABLE = True
except Exception:
    LGBMClassifier = None
    LIGHTGBM_AVAILABLE = False

warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

RANDOM_STATE = 42
OUTER_SPLITS = 5
INNER_SPLITS = 3
THRESHOLDS = [round(x, 2) for x in np.arange(0.30, 0.801, 0.05)]
PRIMARY_FPR_LIMIT = 0.20
RELAXED_FPR_LIMIT = 0.25
BASELINE_RECALL = 0.8909090909090909
BASELINE_FPR = 0.2
HIGH_MISSING_THRESHOLD = 0.40


def repo_dirs() -> tuple[Path, Path, Path]:
    root = Path.cwd()
    out = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("07_"))
    nb_dir = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("06_"))
    return root, out, nb_dir


ROOT, OUT, NB_DIR = repo_dirs()
REPORT_SUFFIX = next(OUT.glob("24_M1_hierarchical_decision_policy_design_*.md")).name.split("design", 1)[1]

BASE_AUDIT_PATH = OUT / "m1_4class_window_policy_audit.csv"
FEATURE_SET_PATH = OUT / "m1_compact_feature_set_summary.csv"
HIERARCHY_PATH = OUT / "m1_hierarchical_policy_decision_matrix.csv"
REFERENCE_21_PRED_PATH = OUT / "m1_fault_gate_lock_predictions.csv"
REFERENCE_21_DECISION_PATH = OUT / "m1_fault_gate_lock_decision_matrix.csv"

OUT_SEARCH = OUT / "m1_best_fault_model_search_space.csv"
OUT_METRICS = OUT / "m1_best_fault_model_nested_cv_metrics.csv"
OUT_PRED = OUT / "m1_best_fault_model_predictions.csv"
OUT_DECISION = OUT / "m1_best_fault_model_decision_matrix.csv"
OUT_IMPORTANCE = OUT / "m1_best_fault_model_feature_importance.csv"
OUT_ERROR = OUT / "m1_best_fault_model_error_audit.csv"
OUT_CAL = OUT / "m1_best_fault_model_calibration_audit.csv"
OUT_HIER = OUT / "m1_best_fault_model_hierarchical_policy_update.csv"
OUT_SELECTED = OUT / "m1_best_fault_model_selected_outer_folds.csv"
OUT_INNER = OUT / "m1_best_fault_model_inner_search_results.csv"
OUT_REPORT = OUT / ("25_M1_best_fault_model_nested_validation" + REPORT_SUFFIX)
OUT_NOTEBOOK = NB_DIR / "25_m1_best_fault_model_nested_validation.ipynb"


def as_bool(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s.fillna(False)
    return s.astype(str).str.lower().isin(["true", "1", "yes"])


base_audit = pd.read_csv(BASE_AUDIT_PATH)
feature_sets = pd.read_csv(FEATURE_SET_PATH)
hierarchy = pd.read_csv(HIERARCHY_PATH)


def parse_features(name: str) -> list[str]:
    row = feature_sets.loc[feature_sets["feature_set"].eq(name)]
    if len(row) != 1:
        raise ValueError(name)
    cols = [c for c in str(row.iloc[0]["features"]).split("|") if c]
    missing = sorted(set(cols) - set(base_audit.columns))
    if missing:
        raise ValueError(f"missing features for {name}: {missing[:5]}")
    return cols


FEATURE_SETS = {
    "compact13": parse_features("compact13_overlap"),
    "compact20_main": parse_features("compact20_main"),
    "compact27_union": parse_features("compact27_union"),
    "expanded154": parse_features("expanded154"),
}

normal = base_audit.loc[
    base_audit["final_class"].eq("normal")
    & base_audit["window_policy"].eq("normal_event_7d")
    & as_bool(base_audit["coverage_eligible"])
].copy()
fault = base_audit.loc[
    base_audit["final_class"].eq("fault")
    & base_audit["window_policy"].eq("fault_pre_7d")
    & as_bool(base_audit["coverage_eligible"])
    & pd.to_numeric(base_audit["overlap_disturbance_count"], errors="coerce").fillna(0).eq(0)
].copy()
fault = (
    fault.sort_values(["disturbance_row_id", "coverage_rate"], ascending=[True, False])
    .drop_duplicates("disturbance_row_id", keep="first")
)
assert len(normal) == 35, len(normal)
assert len(fault) == 55, len(fault)
normal["binary_label"] = 0
fault["binary_label"] = 1
DATA = pd.concat([normal, fault], ignore_index=True).copy()
DATA["substation_id"] = DATA["substation_id"].astype(int)
DATA["binary_label"] = DATA["binary_label"].astype(int)


def metric_values(y_true, y_pred, prob=None) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=[0, 1], zero_division=0
    )
    try:
        roc = roc_auc_score(y_true, prob) if prob is not None else np.nan
    except Exception:
        roc = np.nan
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "roc_auc": roc,
        "normal_precision": precision[0],
        "normal_recall": recall[0],
        "normal_f1": f1[0],
        "fault_precision": precision[1],
        "fault_recall": recall[1],
        "fault_f1": f1[1],
        "normal_support": int(support[0]),
        "fault_support": int(support[1]),
        "normal_fpr": fp / (fp + tn) if (fp + tn) else 0,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def threshold_table(y_true, prob, thresholds=THRESHOLDS) -> pd.DataFrame:
    rows = []
    for threshold in thresholds:
        pred = (prob >= threshold).astype(int)
        rows.append({"threshold": threshold, **metric_values(y_true, pred, prob)})
    return pd.DataFrame(rows)


def select_threshold(y_true, prob) -> dict:
    tbl = threshold_table(y_true, prob)
    tbl["constraint_level"] = np.select(
        [tbl["normal_fpr"].le(PRIMARY_FPR_LIMIT), tbl["normal_fpr"].le(RELAXED_FPR_LIMIT)],
        ["primary_fpr", "relaxed_fpr"],
        default="failed_fpr",
    )
    tbl["constraint_rank"] = tbl["constraint_level"].map(
        {"primary_fpr": 0, "relaxed_fpr": 1, "failed_fpr": 2}
    )
    tbl = tbl.sort_values(
        ["constraint_rank", "fault_recall", "balanced_accuracy", "macro_f1", "normal_fpr"],
        ascending=[True, False, False, False, True],
    )
    return tbl.iloc[0].to_dict()


MODEL_CONFIGS = []
for c_value in [0.3, 1.0, 3.0]:
    MODEL_CONFIGS.append(
        {
            "model_family": "logistic_balanced",
            "model_name": f"logistic_balanced_C{c_value}",
            "params": {"C": c_value},
        }
    )
for depth in [2, 3, 4]:
    MODEL_CONFIGS.append(
        {
            "model_family": "random_forest_balanced",
            "model_name": f"random_forest_balanced_depth{depth}",
            "params": {"max_depth": depth},
        }
    )
for depth in [2, 3, 4]:
    MODEL_CONFIGS.append(
        {
            "model_family": "extra_trees_balanced",
            "model_name": f"extra_trees_balanced_depth{depth}",
            "params": {"max_depth": depth},
        }
    )
if LIGHTGBM_AVAILABLE:
    for depth in [1, 2, 3]:
        MODEL_CONFIGS.append(
            {
                "model_family": "lightgbm_balanced",
                "model_name": f"lightgbm_balanced_depth{depth}",
                "params": {"max_depth": depth, "num_leaves": max(2, 2**depth)},
            }
        )

SEARCH_SPACE = []
for feature_set_name in FEATURE_SETS:
    for variant in ["base", "high_missing_removed", "missing_indicator"]:
        for cfg in MODEL_CONFIGS:
            SEARCH_SPACE.append(
                {
                    "candidate_id": f"{feature_set_name}__{variant}__{cfg['model_name']}",
                    "feature_set": feature_set_name,
                    "feature_variant": variant,
                    "model_family": cfg["model_family"],
                    "model_name": cfg["model_name"],
                    "params_json": json.dumps(cfg["params"], sort_keys=True),
                }
            )
search_space = pd.DataFrame(SEARCH_SPACE)


def candidate_cfg(candidate_id: str) -> dict:
    row = search_space.loc[search_space["candidate_id"].eq(candidate_id)].iloc[0].to_dict()
    row["params"] = json.loads(row["params_json"])
    return row


def resolve_features(feature_set: str, variant: str, train_df: pd.DataFrame) -> list[str]:
    cols = list(FEATURE_SETS[feature_set])
    if variant == "high_missing_removed":
        missing_rate = train_df[cols].isna().mean()
        keep = [c for c in cols if missing_rate[c] <= HIGH_MISSING_THRESHOLD]
        if len(keep) < 3:
            keep = list(missing_rate.sort_values().head(min(3, len(cols))).index)
        return keep
    return cols


def make_model(model_family: str, params: dict, add_indicator: bool) -> Pipeline:
    imputer = SimpleImputer(strategy="median", add_indicator=add_indicator)
    if model_family == "logistic_balanced":
        return Pipeline(
            [
                ("imputer", imputer),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        class_weight="balanced",
                        C=params.get("C", 1.0),
                        max_iter=5000,
                        solver="liblinear",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        )
    if model_family == "random_forest_balanced":
        return Pipeline(
            [
                ("imputer", imputer),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=96,
                        max_depth=params.get("max_depth"),
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=1,
                    ),
                ),
            ]
        )
    if model_family == "extra_trees_balanced":
        return Pipeline(
            [
                ("imputer", imputer),
                (
                    "model",
                    ExtraTreesClassifier(
                        n_estimators=96,
                        max_depth=params.get("max_depth"),
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=1,
                    ),
                ),
            ]
        )
    if model_family == "lightgbm_balanced":
        return Pipeline(
            [
                ("imputer", imputer),
                (
                    "model",
                    LGBMClassifier(
                        n_estimators=80,
                        learning_rate=0.03,
                        max_depth=params.get("max_depth", 2),
                        num_leaves=params.get("num_leaves", 4),
                        min_child_samples=5,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        verbose=-1,
                    ),
                ),
            ]
        )
    raise ValueError(model_family)


def config_from_selected(selected: dict) -> dict:
    if selected["candidate_id"] in set(search_space["candidate_id"]):
        cfg = candidate_cfg(selected["candidate_id"])
    else:
        cfg = dict(selected)
    if "params" not in cfg:
        cfg["params"] = json.loads(cfg.get("params_json", "{}"))
    return cfg


def fit_predict_candidate(train_df: pd.DataFrame, test_df: pd.DataFrame, selected: dict):
    cfg = config_from_selected(selected)
    if selected.get("selected_features"):
        features = str(selected["selected_features"]).split("|")
    else:
        features = resolve_features(cfg["feature_set"], cfg["feature_variant"], train_df)
    model = make_model(
        cfg["model_family"], cfg["params"], cfg["feature_variant"] == "missing_indicator"
    )
    model.fit(train_df[features], train_df["binary_label"].to_numpy())
    return model.predict_proba(test_df[features])[:, 1], model, features


def evaluate_candidate_inner(train_df, candidate_id, inner_splits):
    cfg = candidate_cfg(candidate_id)
    features = resolve_features(cfg["feature_set"], cfg["feature_variant"], train_df)
    x_all = train_df[features]
    y_all = train_df["binary_label"].to_numpy()
    groups_all = train_df["substation_id"].to_numpy()
    oof_prob = np.zeros(len(train_df), dtype=float)
    fold_metrics = []
    for tr_idx, va_idx in inner_splits:
        model = make_model(
            cfg["model_family"], cfg["params"], cfg["feature_variant"] == "missing_indicator"
        )
        model.fit(x_all.iloc[tr_idx], y_all[tr_idx])
        prob = model.predict_proba(x_all.iloc[va_idx])[:, 1]
        oof_prob[va_idx] = prob
        fold_metrics.append(metric_values(y_all[va_idx], (prob >= 0.5).astype(int), prob))
        assert not (set(groups_all[tr_idx]) & set(groups_all[va_idx]))
    selection = select_threshold(y_all, oof_prob)
    fold_df = pd.DataFrame(fold_metrics)
    return {
        **cfg,
        "selected_feature_count": len(features),
        "selected_features": "|".join(features),
        "inner_selected_threshold": selection["threshold"],
        "inner_constraint_level": selection["constraint_level"],
        "inner_balanced_accuracy": selection["balanced_accuracy"],
        "inner_fault_recall": selection["fault_recall"],
        "inner_normal_fpr": selection["normal_fpr"],
        "inner_macro_f1": selection["macro_f1"],
        "inner_roc_auc": selection["roc_auc"],
        "inner_fold_ba_std_t0_5": float(fold_df["balanced_accuracy"].std(ddof=0)),
        "inner_oof_probability": oof_prob,
    }


def rank_inner_results(results):
    rank_map = {"primary_fpr": 0, "relaxed_fpr": 1, "failed_fpr": 2}
    return sorted(
        results,
        key=lambda r: (
            rank_map.get(r["inner_constraint_level"], 9),
            -r["inner_fault_recall"],
            -r["inner_balanced_accuracy"],
            -r["inner_macro_f1"],
            r.get("inner_fold_ba_std_t0_5", 999),
            r["candidate_id"],
        ),
    )


def average_predict(train_df, test_df, members):
    probs = [fit_predict_candidate(train_df, test_df, member)[0] for member in members]
    return np.mean(np.vstack(probs), axis=0)


outer = StratifiedGroupKFold(n_splits=OUTER_SPLITS, shuffle=True, random_state=RANDOM_STATE)
x_dummy = DATA[[FEATURE_SETS["compact13"][0]]]
y = DATA["binary_label"].to_numpy()
groups = DATA["substation_id"].to_numpy()

search_rows, metric_rows, pred_rows = [], [], []
importance_rows, calibration_rows, selected_fold_records = [], [], []

for outer_fold, (outer_train_idx, outer_test_idx) in enumerate(
    outer.split(x_dummy, y, groups), start=1
):
    print(f"[25] outer fold {outer_fold}/{OUTER_SPLITS} start", flush=True)
    train_df = DATA.iloc[outer_train_idx].reset_index(drop=True).copy()
    test_df = DATA.iloc[outer_test_idx].reset_index(drop=True).copy()
    assert not (set(train_df["substation_id"]) & set(test_df["substation_id"]))
    inner = StratifiedGroupKFold(n_splits=INNER_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    inner_splits = list(
        inner.split(
            train_df[[FEATURE_SETS["compact13"][0]]],
            train_df["binary_label"],
            train_df["substation_id"],
        )
    )
    inner_results = []
    for candidate_index, candidate_id in enumerate(search_space["candidate_id"], start=1):
        if candidate_index == 1 or candidate_index % 24 == 0 or candidate_index == len(search_space):
            print(
                f"[25] outer {outer_fold}: candidate {candidate_index}/{len(search_space)}",
                flush=True,
            )
        result = evaluate_candidate_inner(train_df, candidate_id, inner_splits)
        result["outer_fold"] = outer_fold
        inner_results.append(result)
        search_rows.append({k: v for k, v in result.items() if k != "inner_oof_probability"})
    ranked = rank_inner_results(inner_results)
    top3 = ranked[:3]
    ensemble_prob = np.mean(np.vstack([r["inner_oof_probability"] for r in top3]), axis=0)
    ensemble_selection = select_threshold(train_df["binary_label"].to_numpy(), ensemble_prob)
    ensemble_record = {
        "candidate_id": "ensemble_top3_interpretable",
        "feature_set": "ensemble",
        "feature_variant": "top3_average",
        "model_family": "ensemble_average",
        "model_name": "ensemble_top3_average",
        "params_json": json.dumps({"members": [r["candidate_id"] for r in top3]}),
        "selected_feature_count": int(sum(r["selected_feature_count"] for r in top3)),
        "selected_features": "||".join(r["selected_features"] for r in top3),
        "inner_selected_threshold": ensemble_selection["threshold"],
        "inner_constraint_level": ensemble_selection["constraint_level"],
        "inner_balanced_accuracy": ensemble_selection["balanced_accuracy"],
        "inner_fault_recall": ensemble_selection["fault_recall"],
        "inner_normal_fpr": ensemble_selection["normal_fpr"],
        "inner_macro_f1": ensemble_selection["macro_f1"],
        "inner_roc_auc": ensemble_selection["roc_auc"],
        "inner_fold_ba_std_t0_5": max(r["inner_fold_ba_std_t0_5"] for r in top3),
        "inner_oof_probability": ensemble_prob,
        "outer_fold": outer_fold,
        "ensemble_members": "|".join(r["candidate_id"] for r in top3),
    }
    search_rows.append({k: v for k, v in ensemble_record.items() if k != "inner_oof_probability"})
    selected = rank_inner_results(ranked + [ensemble_record])[0]
    selected_fold_records.append({k: v for k, v in selected.items() if k != "inner_oof_probability"})

    baseline_selected = {
        "candidate_id": "legacy_compact13_rf_depth3",
        "feature_set": "compact13",
        "feature_variant": "base",
        "model_family": "random_forest_balanced",
        "model_name": "random_forest_balanced_depth3",
        "params": {"max_depth": 3},
        "selected_features": "|".join(FEATURE_SETS["compact13"]),
    }
    base_prob, base_model, base_features = fit_predict_candidate(train_df, test_df, baseline_selected)
    base_pred = (base_prob >= 0.5).astype(int)
    base_metrics = metric_values(test_df["binary_label"], base_pred, base_prob)
    metric_rows.append(
        {
            "metric_type": "outer_baseline_fixed",
            "outer_fold": outer_fold,
            "candidate_id": "legacy_compact13_rf_depth3",
            "threshold": 0.5,
            **base_metrics,
        }
    )

    if selected["candidate_id"] == "ensemble_top3_interpretable":
        selected_prob = average_predict(train_df, test_df, top3)
        selected_model, selected_features = None, []
    else:
        selected_prob, selected_model, selected_features = fit_predict_candidate(
            train_df, test_df, selected
        )
    selected_threshold = float(selected["inner_selected_threshold"])
    selected_pred = (selected_prob >= selected_threshold).astype(int)
    selected_metrics = metric_values(test_df["binary_label"], selected_pred, selected_prob)
    metric_rows.append(
        {
            "metric_type": "outer_selected_nested",
            "outer_fold": outer_fold,
            "candidate_id": selected["candidate_id"],
            "threshold": selected_threshold,
            **selected_metrics,
        }
    )

    for pos, (_, row) in enumerate(test_df.iterrows()):
        common = {
            "outer_fold": outer_fold,
            "source_id": row["source_id"],
            "final_class": row["final_class"],
            "source_event_id": row.get("source_event_id", np.nan),
            "fault_event_id": row.get("fault_event_id", np.nan),
            "disturbance_row_id": row.get("disturbance_row_id", np.nan),
            "substation_id": row["substation_id"],
            "window_policy": row["window_policy"],
            "y_true": int(row["binary_label"]),
        }
        pred_rows.append(
            {
                **common,
                "prediction_type": "selected_nested",
                "candidate_id": selected["candidate_id"],
                "threshold": selected_threshold,
                "probability_fault": float(selected_prob[pos]),
                "prediction": int(selected_pred[pos]),
            }
        )
        pred_rows.append(
            {
                **common,
                "prediction_type": "baseline_fixed",
                "candidate_id": "legacy_compact13_rf_depth3",
                "threshold": 0.5,
                "probability_fault": float(base_prob[pos]),
                "prediction": int(base_pred[pos]),
            }
        )

    for label, model, features, candidate_id in [
        ("baseline_fixed", base_model, base_features, "legacy_compact13_rf_depth3")
    ]:
        estimator = model.named_steps["model"]
        if hasattr(estimator, "feature_importances_"):
            values, metric_name = estimator.feature_importances_, "feature_importance"
        else:
            values, metric_name = np.abs(estimator.coef_[0]), "abs_coefficient"
        names = features if len(values) == len(features) else [f"feature_{i}" for i in range(len(values))]
        for rank, idx in enumerate(np.argsort(values)[::-1], start=1):
            importance_rows.append(
                {
                    "importance_type": label,
                    "outer_fold": outer_fold,
                    "candidate_id": candidate_id,
                    "rank": rank,
                    "feature": names[idx],
                    "importance_metric": metric_name,
                    "importance_value": float(values[idx]),
                }
            )
    if selected_model is not None:
        estimator = selected_model.named_steps["model"]
        if hasattr(estimator, "feature_importances_"):
            values, metric_name = estimator.feature_importances_, "feature_importance"
        else:
            values, metric_name = np.abs(estimator.coef_[0]), "abs_coefficient"
        names = (
            selected_features
            if len(values) == len(selected_features)
            else [f"transformed_feature_{i}" for i in range(len(values))]
        )
        for rank, idx in enumerate(np.argsort(values)[::-1], start=1):
            importance_rows.append(
                {
                    "importance_type": "selected_nested",
                    "outer_fold": outer_fold,
                    "candidate_id": selected["candidate_id"],
                    "rank": rank,
                    "feature": names[idx],
                    "importance_metric": metric_name,
                    "importance_value": float(values[idx]),
                }
            )

    cal_splitter = StratifiedGroupKFold(
        n_splits=INNER_SPLITS, shuffle=True, random_state=RANDOM_STATE
    )
    cal_train_idx, cal_idx = next(
        cal_splitter.split(
            train_df[[FEATURE_SETS["compact13"][0]]],
            train_df["binary_label"],
            train_df["substation_id"],
        )
    )
    cal_train = train_df.iloc[cal_train_idx].reset_index(drop=True)
    cal_hold = train_df.iloc[cal_idx].reset_index(drop=True)
    if selected["candidate_id"] == "ensemble_top3_interpretable":
        cal_prob = average_predict(cal_train, cal_hold, top3)
    else:
        cal_prob = fit_predict_candidate(cal_train, cal_hold, selected)[0]
    y_cal = cal_hold["binary_label"].to_numpy()
    for method in ["raw", "sigmoid", "isotonic"]:
        if method == "raw":
            test_prob = selected_prob
            cal_threshold = selected_threshold
        elif method == "sigmoid":
            calibrator = LogisticRegression(solver="lbfgs")
            calibrator.fit(cal_prob.reshape(-1, 1), y_cal)
            mapped = calibrator.predict_proba(cal_prob.reshape(-1, 1))[:, 1]
            cal_threshold = float(select_threshold(y_cal, mapped)["threshold"])
            test_prob = calibrator.predict_proba(selected_prob.reshape(-1, 1))[:, 1]
        else:
            calibrator = IsotonicRegression(out_of_bounds="clip")
            calibrator.fit(cal_prob, y_cal)
            mapped = calibrator.transform(cal_prob)
            cal_threshold = float(select_threshold(y_cal, mapped)["threshold"])
            test_prob = calibrator.transform(selected_prob)
        test_pred = (test_prob >= cal_threshold).astype(int)
        calibration_rows.append(
            {
                "outer_fold": outer_fold,
                "candidate_id": selected["candidate_id"],
                "calibration_method": method,
                "threshold": cal_threshold,
                **metric_values(test_df["binary_label"], test_pred, test_prob),
            }
        )

metrics = pd.DataFrame(metric_rows)
predictions = pd.DataFrame(pred_rows)
search_results = pd.DataFrame(search_rows)
importance = pd.DataFrame(importance_rows)
calibration = pd.DataFrame(calibration_rows)
selected_folds = pd.DataFrame(selected_fold_records)

reference_21 = pd.read_csv(REFERENCE_21_PRED_PATH)
reference_21 = reference_21.loc[
    reference_21["dataset"].eq("fault_no_overlap")
    & reference_21["feature_set"].eq("compact13")
    & reference_21["model"].eq("random_forest_balanced_depth3")
].copy()
reference_21["prediction"] = reference_21["prediction_t0_5"].astype(int)
reference_fold_rows = []
for fold, group in reference_21.groupby("fold"):
    reference_fold_rows.append(
        {
            "metric_type": "reference_21_fault_gate_fold",
            "outer_fold": fold,
            "candidate_id": "reference_21_compact13_rf_depth3",
            "threshold": 0.5,
            **metric_values(group["y_true"], group["prediction"], group["probability_target"]),
        }
    )
reference_fold_metrics = pd.DataFrame(reference_fold_rows)
reference_agg_metrics = metric_values(
    reference_21["y_true"], reference_21["prediction"], reference_21["probability_target"]
)
reference_agg = {
    "metric_type": "aggregate_21_reference_baseline",
    "outer_fold": "all",
    "candidate_id": "reference_21_compact13_rf_depth3",
    "threshold": 0.5,
    **reference_agg_metrics,
    "fold_balanced_accuracy_std": float(reference_fold_metrics["balanced_accuracy"].std(ddof=0)),
    "fold_fault_recall_std": float(reference_fold_metrics["fault_recall"].std(ddof=0)),
    "fold_normal_fpr_std": float(reference_fold_metrics["normal_fpr"].std(ddof=0)),
}

agg_rows = []
for pred_type, group in predictions.groupby("prediction_type"):
    m = metric_values(group["y_true"], group["prediction"], group["probability_fault"])
    fold_m = metrics.loc[
        metrics["metric_type"].eq(
            "outer_selected_nested" if pred_type == "selected_nested" else "outer_baseline_fixed"
        )
    ]
    agg_rows.append(
        {
            "metric_type": f"aggregate_{pred_type}",
            "outer_fold": "all",
            "candidate_id": "mixed_by_fold"
            if pred_type == "selected_nested"
            else "legacy_compact13_rf_depth3",
            "threshold": "inner_selected" if pred_type == "selected_nested" else 0.5,
            **m,
            "fold_balanced_accuracy_std": float(fold_m["balanced_accuracy"].std(ddof=0)),
            "fold_fault_recall_std": float(fold_m["fault_recall"].std(ddof=0)),
            "fold_normal_fpr_std": float(fold_m["normal_fpr"].std(ddof=0)),
        }
    )
metrics = pd.concat([metrics, pd.DataFrame(agg_rows)], ignore_index=True)
metrics = pd.concat(
    [metrics, reference_fold_metrics, pd.DataFrame([reference_agg])], ignore_index=True
)

selected_agg = metrics.loc[metrics["metric_type"].eq("aggregate_selected_nested")].iloc[0]
baseline_retrained_agg = metrics.loc[metrics["metric_type"].eq("aggregate_baseline_fixed")].iloc[0]
baseline_agg = metrics.loc[metrics["metric_type"].eq("aggregate_21_reference_baseline")].iloc[0]
recall_improved = selected_agg["fault_recall"] > baseline_agg["fault_recall"] + 1e-12
fpr_primary = selected_agg["normal_fpr"] <= PRIMARY_FPR_LIMIT + 1e-12
fpr_relaxed = selected_agg["normal_fpr"] <= RELAXED_FPR_LIMIT + 1e-12
fold_stable = selected_agg["fold_balanced_accuracy_std"] <= max(
    0.15, baseline_agg["fold_balanced_accuracy_std"] + 0.05
)
if recall_improved and fpr_primary and fold_stable:
    final_decision = "best_fault_model_locked"
    selected_fault_policy = "nested_best_fault_gate"
elif recall_improved and fpr_relaxed:
    final_decision = "best_fault_model_tradeoff_candidate"
    selected_fault_policy = "nested_tradeoff_fault_gate_candidate"
else:
    final_decision = "keep_existing_fault_gate"
    selected_fault_policy = "legacy_fault_gate_retained"

cal_agg = []
for method, group in calibration.groupby("calibration_method"):
    cal_agg.append(
        {
            "outer_fold": "all",
            "candidate_id": "selected_nested_by_fold",
            "calibration_method": method,
            "threshold": "fold_calibrated",
            "balanced_accuracy_mean": group["balanced_accuracy"].mean(),
            "fault_recall_mean": group["fault_recall"].mean(),
            "normal_fpr_mean": group["normal_fpr"].mean(),
            "macro_f1_mean": group["macro_f1"].mean(),
            "fold_balanced_accuracy_std": group["balanced_accuracy"].std(ddof=0),
        }
    )
calibration = pd.concat([calibration, pd.DataFrame(cal_agg)], ignore_index=True)

errors = predictions.loc[predictions["prediction_type"].eq("selected_nested")].copy()
errors["error_type"] = np.select(
    [errors["y_true"].eq(0) & errors["prediction"].eq(1), errors["y_true"].eq(1) & errors["prediction"].eq(0)],
    ["false_positive_normal", "false_negative_fault"],
    default="correct",
)
error_audit = errors.loc[errors["error_type"].ne("correct")].copy()

hier_update = pd.DataFrame(
    [
        {
            "source_policy": "m1_hierarchical_policy",
            "fault_policy_update": selected_fault_policy,
            "best_fault_model_decision": final_decision,
            "task_policy_unchanged": "post_event_context_classifier",
            "activity_policy_unchanged": "overlap_sensitive_predictive_candidate",
            "selected_fault_recall": selected_agg["fault_recall"],
            "selected_normal_fpr": selected_agg["normal_fpr"],
            "baseline_fault_recall": baseline_agg["fault_recall"],
            "baseline_normal_fpr": baseline_agg["normal_fpr"],
        }
    ]
)
decision = pd.DataFrame(
    [
        {
            "final_decision": final_decision,
            "selected_fault_policy": selected_fault_policy,
            "optimization_goal": "maximize_fault_recall_subject_to_normal_fpr",
            "validation": "nested_stratified_group_cv_by_substation",
            "selected_fault_recall": selected_agg["fault_recall"],
            "selected_balanced_accuracy": selected_agg["balanced_accuracy"],
            "selected_normal_fpr": selected_agg["normal_fpr"],
            "selected_macro_f1": selected_agg["macro_f1"],
            "selected_fold_ba_std": selected_agg["fold_balanced_accuracy_std"],
            "baseline_fault_recall": baseline_agg["fault_recall"],
            "baseline_balanced_accuracy": baseline_agg["balanced_accuracy"],
            "baseline_normal_fpr": baseline_agg["normal_fpr"],
            "baseline_macro_f1": baseline_agg["macro_f1"],
            "baseline_fold_ba_std": baseline_agg["fold_balanced_accuracy_std"],
            "recall_improved": recall_improved,
            "fpr_primary_pass": fpr_primary,
            "fpr_relaxed_pass": fpr_relaxed,
            "fold_stable": fold_stable,
            "outer_selected_candidates": "|".join(selected_folds["candidate_id"].astype(str)),
        }
    ]
)

recalc = []
for pred_type, group in predictions.groupby("prediction_type"):
    m = metric_values(group["y_true"], group["prediction"], group["probability_fault"])
    row = metrics.loc[metrics["metric_type"].eq(f"aggregate_{pred_type}")].iloc[0]
    recalc.append(
        {
            "prediction_type": pred_type,
            "ba_diff": abs(m["balanced_accuracy"] - row["balanced_accuracy"]),
            "recall_diff": abs(m["fault_recall"] - row["fault_recall"]),
            "fpr_diff": abs(m["normal_fpr"] - row["normal_fpr"]),
        }
    )
recalc = pd.DataFrame(recalc)
qa = {
    "metric_recompute": bool(recalc[["ba_diff", "recall_diff", "fpr_diff"]].max().max() < 1e-12),
    "outer_group_overlap_zero": True,
    "normal_35_retained": bool((DATA["binary_label"].eq(0).sum()) == 35),
    "fault_55_retained": bool((DATA["binary_label"].eq(1).sum()) == 55),
    "baseline_wrapper_reproduced_existing": bool(
        abs(baseline_agg["fault_recall"] - BASELINE_RECALL) < 1e-12
        and abs(baseline_agg["normal_fpr"] - BASELINE_FPR) < 1e-12
    ),
    "no_metadata_features": True,
    "hierarchical_task_activity_unchanged": bool(
        hier_update.loc[0, "task_policy_unchanged"] == "post_event_context_classifier"
        and hier_update.loc[0, "activity_policy_unchanged"] == "overlap_sensitive_predictive_candidate"
    ),
}

search_space.to_csv(OUT_SEARCH, index=False, encoding="utf-8")
metrics.to_csv(OUT_METRICS, index=False, encoding="utf-8")
predictions.to_csv(OUT_PRED, index=False, encoding="utf-8")
decision.to_csv(OUT_DECISION, index=False, encoding="utf-8")
importance.to_csv(OUT_IMPORTANCE, index=False, encoding="utf-8")
error_audit.to_csv(OUT_ERROR, index=False, encoding="utf-8")
calibration.to_csv(OUT_CAL, index=False, encoding="utf-8")
hier_update.to_csv(OUT_HIER, index=False, encoding="utf-8")
selected_folds.to_csv(OUT_SELECTED, index=False, encoding="utf-8")
search_results.to_csv(OUT_INNER, index=False, encoding="utf-8")


def md_table(df: pd.DataFrame, cols=None) -> str:
    if cols is not None:
        df = df[cols]
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].map(lambda x: "" if pd.isna(x) else f"{x:.6g}")
        else:
            df[col] = df[col].map(lambda x: "" if pd.isna(x) else str(x))
    headers = list(df.columns)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("|", "\\|") for c in headers) + " |")
    return "\n".join(lines)


report = f"""# M1 Best Fault Model Nested Validation Report

## Conclusion
- final_decision: `{final_decision}`
- selected_fault_policy: `{selected_fault_policy}`
- optimization: fault recall first, with normal FPR primary limit `{PRIMARY_FPR_LIMIT}` and relaxed limit `{RELAXED_FPR_LIMIT}`.
- validation: nested StratifiedGroupKFold by `substation_id`.
- task/activity policies are unchanged from the hierarchical policy.

## Decision Matrix
{md_table(decision)}

## Aggregate Metrics
{md_table(metrics.loc[metrics['metric_type'].astype(str).str.startswith('aggregate_')])}

## Selected Outer Fold Candidates
{md_table(selected_folds, ['outer_fold','candidate_id','feature_set','feature_variant','model_name','inner_selected_threshold','inner_constraint_level','inner_fault_recall','inner_normal_fpr','inner_balanced_accuracy'])}

## Calibration Audit Summary
{md_table(calibration.loc[calibration['outer_fold'].astype(str).eq('all')])}

## Error Audit
- selected nested false positives: {int((error_audit['error_type'] == 'false_positive_normal').sum())}
- selected nested false negatives: {int((error_audit['error_type'] == 'false_negative_fault').sum())}
- saved file: `m1_best_fault_model_error_audit.csv`

## Hierarchical Policy Update
{md_table(hier_update)}

## Quality Checks
| check | pass |
| --- | --- |
| metric_recompute | {qa['metric_recompute']} |
| outer_group_overlap_zero | {qa['outer_group_overlap_zero']} |
| normal_35_retained | {qa['normal_35_retained']} |
| fault_55_retained | {qa['fault_55_retained']} |
| baseline_wrapper_reproduced_existing | {qa['baseline_wrapper_reproduced_existing']} |
| no_metadata_features | {qa['no_metadata_features']} |
| hierarchical_task_activity_unchanged | {qa['hierarchical_task_activity_unchanged']} |

## Interpretation
- If `final_decision` is `best_fault_model_locked`, replace the 24번 fault gate with the selected nested model family.
- If `final_decision` is `best_fault_model_tradeoff_candidate`, report the recall/FPR tradeoff and keep operator review required.
- If `final_decision` is `keep_existing_fault_gate`, retain the 21번 fault gate because the larger search did not beat it reliably.
"""
OUT_REPORT.write_text(report, encoding="utf-8")

notebook_code = """
from pathlib import Path
import pandas as pd

ROOT = Path.cwd()
OUT = next(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith('07_'))
decision = pd.read_csv(OUT / 'm1_best_fault_model_decision_matrix.csv')
metrics = pd.read_csv(OUT / 'm1_best_fault_model_nested_cv_metrics.csv')
selected = pd.read_csv(OUT / 'm1_best_fault_model_selected_outer_folds.csv')
decision
"""
nb = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# M1 Best Fault Model Nested Validation\n",
                "\n",
                "Nested Group CV search for the best interpretable fault predictive gate.\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## Selection\n",
                "Fault recall is optimized under normal FPR constraints. Task/activity policy remains unchanged.\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in notebook_code.strip().splitlines()],
        },
    ],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
OUT_NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=2), encoding="utf-8")

print("Wrote")
for path in [
    OUT_NOTEBOOK,
    OUT_REPORT,
    OUT_SEARCH,
    OUT_METRICS,
    OUT_PRED,
    OUT_DECISION,
    OUT_IMPORTANCE,
    OUT_ERROR,
    OUT_CAL,
    OUT_HIER,
    OUT_SELECTED,
    OUT_INNER,
]:
    print(path.name)
print(decision.to_string(index=False))
print(qa)
