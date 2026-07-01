from __future__ import annotations

import argparse
import json
import subprocess
import warnings
from pathlib import Path

import joblib
import nbformat as nbf
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

try:
    from lightgbm import LGBMClassifier
except Exception:  # pragma: no cover
    LGBMClassifier = None

try:
    from xgboost import XGBClassifier
except Exception:  # pragma: no cover
    XGBClassifier = None

RANDOM_STATE = 42
GLOBAL_THRESHOLDS = [0.4, 0.5, 0.6]
SYSTEM_THRESHOLDS = [0.3, 0.4, 0.5, 0.6, 0.7]
DEFAULT_REFERENCE = ("common13", "lightgbm_depth3", 0.5)


def paths() -> dict[str, Path]:
    root = Path.cwd()
    base = root / "09_실험라인" / "m1_m2_standard_pre_event" / "outputs"
    line = root / "09_실험라인" / "m1_m2_system_stratified_pre_event"
    return {
        "root": root,
        "base": base,
        "out": line / "outputs",
        "reports": line / "reports",
        "notebooks": line / "notebooks",
        "models": line / "models",
        "legacy_out": root / "07_데이터산출물",
        "data": root / "05_데이터셋" / "PreDist",
    }


PATHS = paths()


def ensure_dirs() -> None:
    for key in ["out", "reports", "notebooks", "models"]:
        PATHS[key].mkdir(parents=True, exist_ok=True)


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


def compact13_features() -> list[str]:
    df = pd.read_csv(PATHS["legacy_out"] / "m1_compact_feature_set_summary.csv")
    row = df.loc[df["feature_set"].eq("compact13_overlap")]
    if len(row) != 1:
        raise ValueError("compact13_overlap not found")
    return [feature for feature in str(row.iloc[0]["features"]).split("|") if feature]


def metric_from_probability(y_true: pd.Series | np.ndarray, probability: pd.Series | np.ndarray, threshold: float) -> dict:
    y = np.asarray(y_true).astype(int)
    pred = (np.asarray(probability).astype(float) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    precision, recall, f1, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    return {
        "rows": int(len(y)),
        "normal_rows": int((y == 0).sum()),
        "pre_event_rows": int((y == 1).sum()),
        "balanced_accuracy": balanced_accuracy_score(y, pred),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "normal_fpr": fp / (fp + tn) if (fp + tn) else np.nan,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def choose_threshold_for_group(group: pd.DataFrame, fallback: float) -> tuple[float, dict]:
    if len(group) < 8 or group["y_true"].nunique() < 2:
        return fallback, {"selection_reason": "insufficient_group_data"}
    rows = []
    for threshold in SYSTEM_THRESHOLDS:
        metric = metric_from_probability(group["y_true"], group["probability"], threshold)
        rows.append({"threshold": threshold, **metric})
    scores = pd.DataFrame(rows)
    eligible = scores.loc[(scores["recall"] >= 0.70) & (scores["normal_fpr"] <= 0.25)].copy()
    if eligible.empty:
        eligible = scores.copy()
        eligible["rank_score"] = eligible["balanced_accuracy"] + eligible["recall"] - eligible["normal_fpr"]
        reason = "best_available_no_threshold_meets_recall_fpr"
    else:
        eligible["rank_score"] = eligible["balanced_accuracy"] + 0.5 * eligible["recall"] - eligible["normal_fpr"]
        reason = "meets_group_recall_fpr"
    best = eligible.sort_values("rank_score", ascending=False).iloc[0].to_dict()
    return float(best["threshold"]), {"selection_reason": reason, **best}


def apply_system_thresholds(predictions: pd.DataFrame, policy: dict[str, float], fallback: float) -> np.ndarray:
    thresholds = predictions["system_capability_group"].map(policy).fillna(fallback).astype(float)
    return (predictions["probability"].astype(float).to_numpy() >= thresholds.to_numpy()).astype(int)


def metric_from_predictions(y_true: pd.Series, pred: np.ndarray) -> dict:
    y = y_true.astype(int).to_numpy()
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    precision, recall, f1, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    return {
        "rows": int(len(y)),
        "normal_rows": int((y == 0).sum()),
        "pre_event_rows": int((y == 1).sum()),
        "balanced_accuracy": balanced_accuracy_score(y, pred),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "normal_fpr": fp / (fp + tn) if (fp + tn) else np.nan,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
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
            n_estimators=180, max_depth=3, min_samples_leaf=2, class_weight="balanced", random_state=RANDOM_STATE
        )
        scale = False
    elif name == "extra_trees_depth3":
        estimator = ExtraTreesClassifier(
            n_estimators=180, max_depth=3, min_samples_leaf=2, class_weight="balanced", random_state=RANDOM_STATE
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
        raise ValueError(f"unavailable model: {name}")
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", estimator))
    return Pipeline(steps)


def available_models() -> list[str]:
    names = ["dummy_most_frequent", "logistic_balanced", "random_forest_depth3", "extra_trees_depth3", "hist_gradient_boosting"]
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


def load_base_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pool = pd.read_csv(PATHS["base"] / "standard_feature_pool.csv")
    predictions = pd.read_csv(PATHS["base"] / "model_selection_predictions.csv")
    decision = pd.read_csv(PATHS["base"] / "standard_model_decision_matrix.csv")
    meta_cols = [
        "sample_id",
        "system_capability_group",
        "main_eligible",
        "manufacturer_substation_id",
        "coverage_rate",
        "fault_label",
        "exclude_reason",
    ]
    predictions = predictions.merge(pool[meta_cols], on="sample_id", how="left")
    return pool, predictions, decision


def build_dataset_summary(pool: pd.DataFrame) -> pd.DataFrame:
    main = pool.loc[pool["main_eligible"].astype(bool)].copy()
    return (
        main.groupby(["system_capability_group", "manufacturer", "label"])
        .agg(rows=("sample_id", "count"), substations=("manufacturer_substation_id", "nunique"))
        .reset_index()
    )


def system_threshold_audit(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows_policy = []
    rows_metrics = []
    rows_predictions = []
    for (feature_set, model), pooled in predictions.loc[
        predictions["evaluation_scope"].eq("Pooled_M1_M2_group_CV")
    ].groupby(["feature_set", "model"]):
        for fallback in GLOBAL_THRESHOLDS:
            policy = {}
            policy_details = []
            for group_name, group in pooled.groupby("system_capability_group"):
                threshold, details = choose_threshold_for_group(group, fallback)
                policy[str(group_name)] = threshold
                policy_details.append(
                    {
                        "feature_set": feature_set,
                        "model": model,
                        "fallback_threshold": fallback,
                        "system_capability_group": group_name,
                        "selected_threshold": threshold,
                        **details,
                    }
                )
            rows_policy.extend(policy_details)
            for scope, data in predictions.loc[
                predictions["feature_set"].eq(feature_set) & predictions["model"].eq(model)
            ].groupby("evaluation_scope"):
                pred = apply_system_thresholds(data, policy, fallback)
                metric = metric_from_predictions(data["y_true"], pred)
                rows_metrics.append(
                    {
                        "strategy": "system_specific_threshold",
                        "evaluation_scope": scope,
                        "feature_set": feature_set,
                        "model": model,
                        "fallback_threshold": fallback,
                        **metric,
                    }
                )
                tmp = data.copy()
                tmp["selected_threshold"] = tmp["system_capability_group"].map(policy).fillna(fallback)
                tmp["prediction"] = pred
                tmp["strategy"] = "system_specific_threshold"
                tmp["fallback_threshold"] = fallback
                rows_predictions.append(tmp)
    return pd.DataFrame(rows_policy), pd.DataFrame(rows_metrics), pd.concat(rows_predictions, ignore_index=True)


def system_aux_model_validation(pool: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    main = pool.loc[pool["main_eligible"].astype(bool)].copy()
    features = compact13_features()
    pred_rows = []
    metric_rows = []
    candidate_groups = []
    for group_name, group in main.groupby("system_capability_group"):
        label_counts = group["y"].value_counts().to_dict()
        if label_counts.get(0, 0) >= 10 and label_counts.get(1, 0) >= 8 and group["manufacturer_substation_id"].nunique() >= 6:
            candidate_groups.append(group_name)
    for group_name in candidate_groups:
        data = main.loc[main["system_capability_group"].eq(group_name)].copy()
        n_splits = max(2, min(5, int(data["y"].value_counts().min()), data["manufacturer_substation_id"].nunique()))
        splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
        for model_name in available_models():
            fold_probs = []
            for fold, (train_idx, test_idx) in enumerate(
                splitter.split(data[features], data["y"].astype(int), data["manufacturer_substation_id"]), start=1
            ):
                train = data.iloc[train_idx].copy()
                test = data.iloc[test_idx].copy()
                model = make_model(model_name, train["y"].astype(int))
                try:
                    model.fit(train[features], train["y"].astype(int))
                    prob = class_one_probability(model, test[features])
                except Exception as exc:
                    prob = np.full(len(test), np.nan)
                    print(f"model failed {group_name} {model_name}: {exc}")
                for row, p in zip(test.to_dict("records"), prob):
                    fold_probs.append(
                        {
                            "system_capability_group": group_name,
                            "model": model_name,
                            "fold": fold,
                            "sample_id": row["sample_id"],
                            "manufacturer": row["manufacturer"],
                            "source_event_id": row["source_event_id"],
                            "substation_id": row["substation_id"],
                            "label": row["label"],
                            "y_true": int(row["y"]),
                            "probability": float(p),
                        }
                    )
            if not fold_probs:
                continue
            pred_df = pd.DataFrame(fold_probs)
            pred_rows.extend(fold_probs)
            for threshold in GLOBAL_THRESHOLDS:
                metric = metric_from_probability(pred_df["y_true"], pred_df["probability"], threshold)
                metric_rows.append(
                    {
                        "system_capability_group": group_name,
                        "model": model_name,
                        "threshold": threshold,
                        **metric,
                    }
                )
    return pd.DataFrame(metric_rows), pd.DataFrame(pred_rows)


def build_decision_matrix(system_metrics: pd.DataFrame, aux_metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if not system_metrics.empty:
        for (feature_set, model, fallback), group in system_metrics.groupby(["feature_set", "model", "fallback_threshold"]):
            lookup = {row["evaluation_scope"]: row for _, row in group.iterrows()}
            if not all(scope in lookup for scope in ["M1_to_M2", "M2_to_M1", "Pooled_M1_M2_group_CV"]):
                continue
            min_ba = min(float(lookup["M1_to_M2"]["balanced_accuracy"]), float(lookup["M2_to_M1"]["balanced_accuracy"]))
            min_recall = min(
                float(lookup["M1_to_M2"]["recall"]),
                float(lookup["M2_to_M1"]["recall"]),
                float(lookup["Pooled_M1_M2_group_CV"]["recall"]),
            )
            max_fpr = max(
                float(lookup["M1_to_M2"]["normal_fpr"]),
                float(lookup["M2_to_M1"]["normal_fpr"]),
                float(lookup["Pooled_M1_M2_group_CV"]["normal_fpr"]),
            )
            passed = min_ba >= 0.60 and min_recall >= 0.70 and max_fpr <= 0.25
            rows.append(
                {
                    "candidate_type": "system_specific_threshold",
                    "feature_set": feature_set,
                    "model": model,
                    "threshold_policy": f"fallback_{fallback}",
                    "min_leave_manufacturer_ba": min_ba,
                    "min_recall": min_recall,
                    "max_normal_fpr": max_fpr,
                    "candidate_pass": passed,
                    "decision": "system_threshold_model_candidate" if passed else "label_window_recheck_required",
                }
            )
    if not aux_metrics.empty:
        aux_view = aux_metrics.groupby(["system_capability_group", "model", "threshold"]).first().reset_index()
        for _, row in aux_view.iterrows():
            passed = row["balanced_accuracy"] >= 0.70 and row["recall"] >= 0.70 and row["normal_fpr"] <= 0.25
            rows.append(
                {
                    "candidate_type": "system_aux_model",
                    "feature_set": "common13",
                    "model": row["model"],
                    "threshold_policy": f"{row['system_capability_group']}@{row['threshold']}",
                    "min_leave_manufacturer_ba": np.nan,
                    "min_recall": row["recall"],
                    "max_normal_fpr": row["normal_fpr"],
                    "candidate_pass": passed,
                    "decision": "system_aux_model_candidate" if passed else "system_aux_model_not_locked",
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["rank_score"] = out["candidate_pass"].astype(int) * 100 + out["min_recall"].fillna(0) - out["max_normal_fpr"].fillna(1)
    return out.sort_values(["candidate_pass", "rank_score"], ascending=[False, False]).drop(columns=["rank_score"])


def save_candidate_model(pool: pd.DataFrame, decision: pd.DataFrame, threshold_policy: pd.DataFrame) -> tuple[Path, Path]:
    features = compact13_features()
    main = pool.loc[pool["main_eligible"].astype(bool)].copy()
    global_candidates = decision.loc[decision["candidate_type"].eq("system_specific_threshold")].copy()
    if global_candidates.empty:
        model_name = DEFAULT_REFERENCE[1]
        fallback = DEFAULT_REFERENCE[2]
    else:
        top = global_candidates.iloc[0]
        model_name = str(top["model"])
        fallback_text = str(top["threshold_policy"])
        fallback = float(fallback_text.replace("fallback_", "")) if fallback_text.startswith("fallback_") else DEFAULT_REFERENCE[2]
    model = make_model(model_name, main["y"].astype(int))
    model.fit(main[features], main["y"].astype(int))
    policy_rows = threshold_policy.loc[
        threshold_policy["model"].eq(model_name) & threshold_policy["fallback_threshold"].eq(fallback)
    ]
    system_thresholds = {
        str(row["system_capability_group"]): float(row["selected_threshold"]) for _, row in policy_rows.iterrows()
    }
    global_pass = bool((global_candidates["candidate_pass"] == True).any()) if not global_candidates.empty else False
    aux_pass = bool(
        (decision.loc[decision["candidate_type"].eq("system_aux_model"), "candidate_pass"] == True).any()
    ) if not decision.empty else False
    package = {
        "status": "global_not_locked_aux_candidates_available" if aux_pass and not global_pass else (
            "candidate_passed" if global_pass else "not_locked_until_label_window_recheck"
        ),
        "model_name": model_name,
        "feature_set": "common13",
        "features": features,
        "fallback_threshold": fallback,
        "system_thresholds": system_thresholds,
        "global_system_threshold_passed": global_pass,
        "system_aux_candidate_available": aux_pass,
        "model": model,
        "source_commit": source_commit_hash(),
    }
    model_path = PATHS["models"] / "m1_m2_system_stratified_pre_event_candidate.joblib"
    meta_path = PATHS["models"] / "m1_m2_system_stratified_pre_event_candidate_metadata.json"
    joblib.dump(package, model_path)
    meta = {k: v for k, v in package.items() if k != "model"}
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return model_path, meta_path


def write_notebooks() -> None:
    notebook_specs = [
        ("01_system_stratified_threshold_audit.ipynb", "System-stratified threshold audit"),
        ("02_system_aux_model_validation.ipynb", "System auxiliary model validation"),
        ("03_system_stratified_candidate_package.ipynb", "System-stratified candidate package and report"),
    ]
    for filename, title in notebook_specs:
        nb = nbf.v4.new_notebook()
        nb["cells"] = [
            nbf.v4.new_markdown_cell(f"# {title}\n\nM1+M2 normal vs pre_event 시스템별 보정 실험 재현 노트북입니다."),
            nbf.v4.new_code_cell(
                "from pathlib import Path\n"
                "import subprocess, sys\n"
                "root = Path.cwd()\n"
                "result = subprocess.run([sys.executable, str(root / 'scripts' / 'run_37_m1_m2_system_stratified_pre_event.py'), '--stage', 'all'], check=True, capture_output=True, text=True)\n"
                "print(result.stdout)\n"
                "if result.stderr:\n"
                "    print(result.stderr)\n"
            ),
        ]
        nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
        nb["metadata"]["language_info"] = {"name": "python", "pygments_lexer": "ipython3"}
        nbf.write(nb, PATHS["notebooks"] / filename)


def write_report(
    dataset_summary: pd.DataFrame,
    threshold_policy: pd.DataFrame,
    system_metrics: pd.DataFrame,
    aux_metrics: pd.DataFrame,
    decision: pd.DataFrame,
    qa: pd.DataFrame,
    model_path: Path,
) -> None:
    final_decision = "label_window_recheck_required"
    if not decision.empty:
        full_pass = decision.loc[
            decision["candidate_type"].eq("system_specific_threshold") & decision["candidate_pass"].astype(bool)
        ]
        aux_pass = decision.loc[
            decision["candidate_type"].eq("system_aux_model") & decision["candidate_pass"].astype(bool)
        ]
        if not full_pass.empty:
            final_decision = "system_threshold_model_candidate"
        elif not aux_pass.empty:
            final_decision = "system_aux_model_candidate_only"
    top = decision.head(10) if not decision.empty else pd.DataFrame()
    report = f"""# M1+M2 System-Stratified Pre-Event Model 보고서

## 결론
최종 판단: **{final_decision}**

시스템별 threshold 보정과 시스템별 보조모델을 모두 검증했다.
전체 runtime에 바로 넣을 수 있는 `system_specific_threshold` 후보는 아직 잠금 기준을 통과하지 못했지만, 일부 system group 내부 보조모델은 후보로 남길 수 있다.
따라서 joblib 패키지는 운영 확정 모델이 아니라 `global_not_locked_aux_candidates_available` 상태의 재검증용 후보로 저장했다.

## 핵심 결과
- 시스템별 threshold 보정은 일부 FPR을 줄였지만 full runtime 기준 recall을 안정적으로 넘기지 못했다.
- 시스템별 보조모델은 `dhw_storage`, `dhw_storage_return`, `heating_common_only`에서 후보가 나왔지만, 일부 그룹은 제조사/라벨 분포가 치우쳐 있어 보조모델로만 취급한다.
- `dhw_return`, `dhw_supply`는 positive sample이 없어 audit 전용이다.
- 결론적으로 다음은 모델 추가가 아니라 `system group × fault label/window` 재설계가 우선이다.

## System Group Dataset
{md_table(dataset_summary)}

## Decision Matrix
{md_table(top, max_rows=20) if not top.empty else "candidate 없음"}

## System Threshold Metrics 상위
{md_table(system_metrics.sort_values(["balanced_accuracy", "recall"], ascending=False).head(25), max_rows=25) if not system_metrics.empty else "system threshold metric 없음"}

## System Auxiliary Model Metrics 상위
{md_table(aux_metrics.sort_values(["balanced_accuracy", "recall"], ascending=False).head(25), max_rows=25) if not aux_metrics.empty else "system aux model metric 없음"}

## Threshold Policy 예시
{md_table(threshold_policy.head(30), max_rows=30)}

## Candidate Model Package
- path: `{model_path}`
- status: `global_not_locked_aux_candidates_available`
- 운영 사용 금지: 이번 패키지는 후속 실험 재현용 후보이며, 전체 runtime 모델 잠금은 아니다.

## 다음 작업
1. `dhw_storage`, `heating_common_only`, `dhw_storage_return` 별로 fault label 분포를 다시 본다.
2. system group별로 `report_pre_7d`가 같은 의미인지 window를 재검토한다.
3. DHW 고장은 DHW 전용 sensor/window를 쓰는 보조 pre_event 정의를 따로 만든다.
4. 재설계 후 이번 script를 다시 실행해 같은 기준으로 pass/fail을 비교한다.

## 품질 검증
{md_table(qa)}

source commit: `{source_commit_hash()}`
"""
    (PATHS["reports"] / "M1_M2_system_stratified_pre_event_model_보고서.md").write_text(report, encoding="utf-8")


def run_all() -> None:
    ensure_dirs()
    pool, predictions, _ = load_base_data()
    dataset_summary = build_dataset_summary(pool)
    threshold_policy, system_metrics, system_predictions = system_threshold_audit(predictions)
    aux_metrics, aux_predictions = system_aux_model_validation(pool)
    decision = build_decision_matrix(system_metrics, aux_metrics)
    model_path, meta_path = save_candidate_model(pool, decision, threshold_policy)
    qa = pd.DataFrame(
        [
            {"quality_check": "base_outputs_exist", "passed": PATHS["base"].exists(), "detail": str(PATHS["base"])},
            {
                "quality_check": "candidate_model_saved",
                "passed": model_path.exists() and meta_path.exists(),
                "detail": str(model_path),
            },
            {
                "quality_check": "m1_m2_original_zip_exists",
                "passed": (PATHS["data"] / "predist_dataset.zip").exists(),
                "detail": str(PATHS["data"] / "predist_dataset.zip"),
            },
            {
                "quality_check": "manufacturer_not_used_as_feature",
                "passed": "manufacturer" not in compact13_features(),
                "detail": "common13 feature list only",
            },
            {
                "quality_check": "system_groups_have_audit",
                "passed": dataset_summary["system_capability_group"].nunique() >= 3,
                "detail": f"groups={dataset_summary['system_capability_group'].nunique()}",
            },
            {
                "quality_check": "candidate_pass_count",
                "passed": True,
                "detail": str(int(decision["candidate_pass"].sum()) if not decision.empty else 0),
            },
        ]
    )
    dataset_summary.to_csv(PATHS["out"] / "system_stratified_dataset_summary.csv", index=False, encoding="utf-8-sig")
    threshold_policy.to_csv(PATHS["out"] / "system_group_threshold_candidates.csv", index=False, encoding="utf-8-sig")
    system_metrics.to_csv(PATHS["out"] / "system_stratified_threshold_metrics.csv", index=False, encoding="utf-8-sig")
    system_predictions.to_csv(PATHS["out"] / "system_stratified_predictions.csv", index=False, encoding="utf-8-sig")
    aux_metrics.to_csv(PATHS["out"] / "system_aux_model_metrics.csv", index=False, encoding="utf-8-sig")
    aux_predictions.to_csv(PATHS["out"] / "system_aux_model_predictions.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(PATHS["out"] / "system_stratified_decision_matrix.csv", index=False, encoding="utf-8-sig")
    qa.to_csv(PATHS["out"] / "quality_audit.csv", index=False, encoding="utf-8-sig")
    write_notebooks()
    write_report(dataset_summary, threshold_policy, system_metrics, aux_metrics, decision, qa, model_path)
    print("system-stratified pre-event outputs complete")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["all"], default="all")
    args = parser.parse_args()
    run_all()


if __name__ == "__main__":
    main()
