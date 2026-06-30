from __future__ import annotations

import json
import warnings
from pathlib import Path

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
REVIEW_REQUIRED_EVENTS = {19, 68}
HARD_NORMAL_EVENTS = {35, 48}


def repo_dirs() -> tuple[Path, Path, Path]:
    root = Path.cwd()
    out = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("07_"))
    nb_dir = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("06_"))
    return root, out, nb_dir


ROOT, OUT, NB_DIR = repo_dirs()
REPORT_SUFFIX = next(OUT.glob("24_M1_hierarchical_decision_policy_design_*.md")).name.split(
    "design", 1
)[1]

FEATURE_POOL_PATH = OUT / "m1_expansion_feature_pool.csv"
CANDIDATE_AUDIT_PATH = OUT / "m1_expansion_candidate_audit.csv"
FEATURE_SET_PATH = OUT / "m1_compact_feature_set_summary.csv"
OLD_13_PRED_PATH = OUT / "m1_expanded_training_fixed_eval_predictions.csv"
OLD_13_METRICS_PATH = OUT / "m1_expanded_training_fixed_eval_cv_metrics.csv"
HIERARCHY_PATH = OUT / "m1_hierarchical_policy_decision_matrix.csv"
BEST25_PATH = OUT / "m1_best_fault_model_decision_matrix.csv"

OUT_SUMMARY = OUT / "m1_fault_pre_event_13_recipe_dataset_summary.csv"
OUT_METRICS = OUT / "m1_fault_pre_event_13_recipe_cv_metrics.csv"
OUT_PRED = OUT / "m1_fault_pre_event_13_recipe_predictions.csv"
OUT_DECISION = OUT / "m1_fault_pre_event_13_recipe_decision_matrix.csv"
OUT_IMPORTANCE = OUT / "m1_fault_pre_event_13_recipe_feature_importance.csv"
OUT_ERROR = OUT / "m1_fault_pre_event_13_recipe_error_audit.csv"
OUT_HIER = OUT / "m1_fault_pre_event_13_recipe_hierarchical_policy_update.csv"
OUT_REPORT = OUT / ("27_M1_fault_pre_event_13_recipe_gate_application" + REPORT_SUFFIX)
OUT_NOTEBOOK = NB_DIR / "27_m1_fault_pre_event_13_recipe_gate_application.ipynb"


def compact13_features(feature_sets: pd.DataFrame, pool: pd.DataFrame) -> list[str]:
    row = feature_sets.loc[feature_sets["feature_set"].eq("compact13_overlap")]
    if len(row) != 1:
        raise ValueError("compact13_overlap feature set not found")
    features = [f for f in str(row.iloc[0]["features"]).split("|") if f]
    missing = sorted(set(features) - set(pool.columns))
    if missing:
        raise ValueError(f"missing compact13 features: {missing}")
    return features


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


def aggregate_metric(strategy: str, evaluation_scope: str, data: pd.DataFrame) -> dict:
    y_true = data["y_true"].astype(int)
    y_pred = data["fault_pre_event_pred_13_recipe"].astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    try:
        roc_auc = roc_auc_score(y_true, data["fault_pre_event_probability_13_recipe"])
    except ValueError:
        roc_auc = np.nan
    return {
        "strategy": strategy,
        "evaluation_scope": evaluation_scope,
        "fold": "all",
        "n": int(len(data)),
        "normal_n": int((y_true == 0).sum()),
        "positive_n": int((y_true == 1).sum()),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc,
        "false_positive_count": int(fp),
        "false_negative_count": int(fn),
        "true_positive_count": int(tp),
        "true_negative_count": int(tn),
        "false_positive_rate": fp / (fp + tn) if (fp + tn) else 0,
        "normal_fpr": fp / (fp + tn) if (fp + tn) else 0,
        "hard_normal_35_48_fp_count": int(
            data.loc[data["source_event_id"].isin(HARD_NORMAL_EVENTS), "fault_pre_event_pred_13_recipe"].sum()
        ),
        "review_required_19_68_fp_count": int(
            data.loc[
                data["source_event_id"].isin(REVIEW_REQUIRED_EVENTS),
                "fault_pre_event_pred_13_recipe",
            ].sum()
        ),
    }


def fold_metric(strategy: str, fold: int, data: pd.DataFrame) -> dict:
    row = aggregate_metric(strategy, "main_all_49", data)
    row["fold"] = fold
    return row


def fit_importance_rows(strategy: str, train_rows: pd.DataFrame, features: list[str]) -> list[dict]:
    model = make_logistic_pipeline()
    model.fit(train_rows[features], train_rows["y"].astype(int))
    coefs = model.named_steps["model"].coef_[0]
    rows = []
    for rank, (feature, coef) in enumerate(
        sorted(zip(features, coefs), key=lambda pair: abs(pair[1]), reverse=True), start=1
    ):
        rows.append(
            {
                "strategy": strategy,
                "feature": feature,
                "coefficient": float(coef),
                "abs_coefficient": float(abs(coef)),
                "train_rows": int(len(train_rows)),
                "train_positive": int(train_rows["y"].eq(1).sum()),
                "train_normal": int(train_rows["y"].eq(0).sum()),
                "importance_rank": rank,
            }
        )
    return rows


def md_table(df: pd.DataFrame, cols: list[str] | None = None) -> str:
    if cols is not None:
        df = df[cols]
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


feature_pool = pd.read_csv(FEATURE_POOL_PATH)
candidate_audit = pd.read_csv(CANDIDATE_AUDIT_PATH)
feature_sets = pd.read_csv(FEATURE_SET_PATH)
hierarchy = pd.read_csv(HIERARCHY_PATH)
best25 = pd.read_csv(BEST25_PATH).iloc[0]
old13_predictions = pd.read_csv(OLD_13_PRED_PATH)
old13_metrics = pd.read_csv(OLD_13_METRICS_PATH)
features = compact13_features(feature_sets, feature_pool)

fixed_eval = feature_pool.loc[feature_pool["pool_role"].eq("fixed_eval")].copy()
candidate_rows = feature_pool.loc[feature_pool["pool_role"].eq("expansion_candidate")].copy()
fixed_eval["source_event_id"] = fixed_eval["source_event_id"].astype(int)
fixed_eval["substation_id"] = fixed_eval["substation_id"].astype(int)
candidate_rows["substation_id"] = candidate_rows["substation_id"].astype(int)

assert len(fixed_eval) == 49
assert fixed_eval["label"].value_counts().to_dict() == {"normal": 35, "efd_possible": 14}
assert len(candidate_rows.loc[candidate_rows["candidate_type"].eq("weak_positive")]) == 12
assert len(candidate_rows.loc[candidate_rows["candidate_type"].eq("candidate_normal")]) == 70
assert len(features) == 13

sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
pred_rows, fold_audit_rows, metric_rows = [], [], []

for fold, (train_idx, test_idx) in enumerate(
    sgkf.split(fixed_eval[features], fixed_eval["y"], fixed_eval["substation_id"]), start=1
):
    fixed_train = fixed_eval.iloc[train_idx].copy()
    fixed_test = fixed_eval.iloc[test_idx].copy()
    test_groups = set(fixed_test["substation_id"].astype(int))
    train_groups = set(fixed_train["substation_id"].astype(int))
    candidate_train = candidate_rows.loc[
        ~candidate_rows["substation_id"].astype(int).isin(test_groups)
    ].copy()
    assert train_groups.isdisjoint(test_groups)
    assert set(candidate_train["substation_id"].astype(int)).isdisjoint(test_groups)

    strategies = {
        "dummy_most_frequent": (DummyClassifier(strategy="most_frequent"), fixed_train),
        "reference_compact13": (make_logistic_pipeline(), fixed_train),
        "expanded_compact13": (
            make_logistic_pipeline(),
            pd.concat([fixed_train, candidate_train], ignore_index=True),
        ),
    }
    fold_audit_rows.append(
        {
            "fold": fold,
            "test_rows": int(len(fixed_test)),
            "test_groups": "|".join(str(g) for g in sorted(test_groups)),
            "fixed_train_rows": int(len(fixed_train)),
            "candidate_train_rows": int(len(candidate_train)),
            "candidate_train_positive": int(candidate_train["y"].eq(1).sum()),
            "candidate_train_normal": int(candidate_train["y"].eq(0).sum()),
            "group_overlap_count": len(train_groups.intersection(test_groups)),
        }
    )

    for strategy_name, (model, train_rows) in strategies.items():
        model.fit(train_rows[features], train_rows["y"].astype(int))
        probability = class_one_probability(model, fixed_test[features])
        pred = (probability >= THRESHOLD).astype(int)
        fold_pred_rows = []
        for row, proba, y_pred in zip(fixed_test.itertuples(index=False), probability, pred):
            prediction_label = "predictive_fault_risk" if int(y_pred) == 1 else "normal_or_monitor"
            output_row = {
                "dataset_id": "strict_no_event20_fixed_eval",
                "strategy": strategy_name,
                "fold": fold,
                "threshold": THRESHOLD,
                "sample_id": row.sample_id,
                "source_event_id": int(row.source_event_id),
                "substation_id": int(row.substation_id),
                "label": row.label,
                "target_interpretation": "fault_pre_event_risk"
                if int(row.y) == 1
                else "normal_reference",
                "review_tag": row.review_tag,
                "y_true": int(row.y),
                "fault_pre_event_probability_13_recipe": float(proba),
                "fault_pre_event_pred_13_recipe": int(y_pred),
                "prediction_label": prediction_label,
                "final_operational_label": prediction_label,
                "policy_reason": "13_expanded_compact13_pre_event_gate_threshold_0.6",
                "coverage_rate": float(row.coverage_rate),
                "train_fixed_rows": int(len(fixed_train)),
                "train_candidate_rows": int(len(candidate_train))
                if strategy_name == "expanded_compact13"
                else 0,
                "train_candidate_positive": int(candidate_train["y"].eq(1).sum())
                if strategy_name == "expanded_compact13"
                else 0,
                "train_candidate_normal": int(candidate_train["y"].eq(0).sum())
                if strategy_name == "expanded_compact13"
                else 0,
            }
            pred_rows.append(output_row)
            fold_pred_rows.append(output_row)
        metric_rows.append(fold_metric(strategy_name, fold, pd.DataFrame(fold_pred_rows)))

predictions = pd.DataFrame(pred_rows)
fold_audit = pd.DataFrame(fold_audit_rows)

for strategy, data in predictions.groupby("strategy"):
    metric_rows.append(aggregate_metric(strategy, "main_all_49", data))
    sensitivity = data.loc[~data["source_event_id"].isin(REVIEW_REQUIRED_EVENTS)].copy()
    row = aggregate_metric(strategy, "sensitivity_exclude_review_required_19_68", sensitivity)
    metric_rows.append(row)
metrics = pd.DataFrame(metric_rows)

expanded_main = metrics.loc[
    metrics["strategy"].eq("expanded_compact13")
    & metrics["evaluation_scope"].eq("main_all_49")
    & metrics["fold"].astype(str).eq("all")
].iloc[0]
expanded_sensitivity = metrics.loc[
    metrics["strategy"].eq("expanded_compact13")
    & metrics["evaluation_scope"].eq("sensitivity_exclude_review_required_19_68")
    & metrics["fold"].astype(str).eq("all")
].iloc[0]
reference_main = metrics.loc[
    metrics["strategy"].eq("reference_compact13")
    & metrics["evaluation_scope"].eq("main_all_49")
    & metrics["fold"].astype(str).eq("all")
].iloc[0]

old13_expanded = old13_metrics.loc[
    old13_metrics["strategy"].eq("expanded_compact13")
    & old13_metrics["evaluation_scope"].eq("main_all_49")
    & old13_metrics["fold"].astype(str).eq("all")
].iloc[0]
old13_sensitivity = old13_metrics.loc[
    old13_metrics["strategy"].eq("expanded_compact13")
    & old13_metrics["evaluation_scope"].eq("sensitivity_exclude_review_required_19_68")
    & old13_metrics["fold"].astype(str).eq("all")
].iloc[0]

accepted_weak = candidate_audit.loc[
    candidate_audit["candidate_kind"].eq("weak_positive")
    & candidate_audit["audit_status"].eq("accepted")
].copy()
accepted_normal = candidate_audit.loc[
    candidate_audit["candidate_kind"].eq("candidate_normal")
    & candidate_audit["audit_status"].eq("accepted")
].copy()

dataset_summary = (
    feature_pool.groupby(["pool_role", "candidate_type", "label", "y"], dropna=False)
    .agg(
        rows=("sample_id", "size"),
        substation_count=("substation_id", "nunique"),
        coverage_min=("coverage_rate", "min"),
        coverage_median=("coverage_rate", "median"),
    )
    .reset_index()
)
dataset_summary["feature_set"] = "compact13_overlap"
dataset_summary["feature_count"] = len(features)
dataset_summary["model_recipe"] = "expanded_compact13_logistic_balanced_threshold_0.6"

importance = pd.DataFrame(
    fit_importance_rows("reference_compact13", fixed_eval, features)
    + fit_importance_rows(
        "expanded_compact13",
        pd.concat([fixed_eval, candidate_rows], ignore_index=True),
        features,
    )
)

expanded_predictions = predictions.loc[predictions["strategy"].eq("expanded_compact13")].copy()
error_audit = expanded_predictions.loc[
    expanded_predictions["y_true"].ne(expanded_predictions["fault_pre_event_pred_13_recipe"])
].copy()
error_audit["error_type"] = np.select(
    [
        error_audit["y_true"].eq(0) & error_audit["fault_pre_event_pred_13_recipe"].eq(1),
        error_audit["y_true"].eq(1) & error_audit["fault_pre_event_pred_13_recipe"].eq(0),
    ],
    ["false_positive_normal", "false_negative_fault_pre_event"],
    default="correct",
)

main_reproduced = (
    abs(expanded_main["balanced_accuracy"] - old13_expanded["balanced_accuracy"]) < 1e-12
    and abs(expanded_main["recall"] - old13_expanded["recall"]) < 1e-12
    and abs(expanded_main["false_positive_rate"] - old13_expanded["false_positive_rate"]) < 1e-12
    and int(expanded_main["false_positive_count"]) == 3
    and int(expanded_main["false_negative_count"]) == 3
)
sensitivity_reproduced = (
    abs(expanded_sensitivity["balanced_accuracy"] - old13_sensitivity["balanced_accuracy"])
    < 1e-12
    and abs(expanded_sensitivity["recall"] - old13_sensitivity["recall"]) < 1e-12
    and abs(expanded_sensitivity["false_positive_rate"] - old13_sensitivity["false_positive_rate"])
    < 1e-12
)
group_overlap_zero = bool(fold_audit["group_overlap_count"].eq(0).all())
hard_normal_ok = int(expanded_main["hard_normal_35_48_fp_count"]) == 0
weak_coverage_ok = bool((pd.to_numeric(accepted_weak["coverage_rate"], errors="coerce") >= 0.95).all())
normal_overlap_ok = bool(
    ~accepted_normal["fault_window_overlap"].fillna(False).astype(bool).any()
    and ~accepted_normal["fixed_eval_window_overlap"].fillna(False).astype(bool).any()
)
metadata_terms = [
    "source_id",
    "event_id",
    "date",
    "window_start",
    "window_end",
    "substation_id",
    "label",
    "target",
]
feature_leakage_ok = not any(term in "|".join(features).lower() for term in metadata_terms)

if (
    main_reproduced
    and sensitivity_reproduced
    and group_overlap_zero
    and hard_normal_ok
    and weak_coverage_ok
    and normal_overlap_ok
    and feature_leakage_ok
):
    final_decision = "fault_pre_event_13_recipe_applied_with_fixed_eval_caveat"
elif main_reproduced and group_overlap_zero:
    final_decision = "fault_pre_event_13_recipe_pending_review"
else:
    final_decision = "keep_25_fault_gate_reference"

hier_row = hierarchy.iloc[0].to_dict()
hier_update = pd.DataFrame(
    [
        {
            "source_policy": "m1_hierarchical_policy",
            "fault_policy_previous": hier_row.get("fault_model", ""),
            "fault_policy_update": "expanded_compact13_logistic_balanced|threshold_0.6",
            "fault_policy_decision": final_decision,
            "fault_probability_column": "fault_pre_event_probability_13_recipe",
            "fault_prediction_column": "fault_pre_event_pred_13_recipe",
            "final_fault_label": "predictive_fault_risk",
            "task_policy_unchanged": "post_event_context_classifier",
            "activity_policy_unchanged": "overlap_sensitive_predictive_candidate",
            "task_activity_pre_event_applied": False,
            "policy_reason": "13_expanded_compact13_pre_event_gate_threshold_0.6",
        }
    ]
)

decision = pd.DataFrame(
    [
        {
            "final_decision": final_decision,
            "fault_gate_recipe": "expanded_compact13_logistic_balanced_threshold_0.6",
            "target_interpretation": "fault_pre_event_risk_from_efd_possible",
            "fixed_eval_rows": len(fixed_eval),
            "normal_rows": int(fixed_eval["y"].eq(0).sum()),
            "positive_rows": int(fixed_eval["y"].eq(1).sum()),
            "expanded_train_rows_full": len(feature_pool),
            "feature_set": "compact13_overlap",
            "feature_count": len(features),
            "threshold": THRESHOLD,
            "balanced_accuracy": expanded_main["balanced_accuracy"],
            "recall": expanded_main["recall"],
            "normal_fpr": expanded_main["false_positive_rate"],
            "false_positive_count": expanded_main["false_positive_count"],
            "false_negative_count": expanded_main["false_negative_count"],
            "sensitivity_balanced_accuracy": expanded_sensitivity["balanced_accuracy"],
            "sensitivity_recall": expanded_sensitivity["recall"],
            "sensitivity_normal_fpr": expanded_sensitivity["false_positive_rate"],
            "reference_13_balanced_accuracy": reference_main["balanced_accuracy"],
            "best25_decision": best25["final_decision"],
            "best25_baseline_recall": best25["baseline_fault_recall"],
            "best25_baseline_normal_fpr": best25["baseline_normal_fpr"],
            "main_13_reproduced": main_reproduced,
            "sensitivity_13_reproduced": sensitivity_reproduced,
            "group_overlap_zero": group_overlap_zero,
            "hard_normal_35_48_fp_zero": hard_normal_ok,
            "weak_positive_coverage_ok": weak_coverage_ok,
            "candidate_normal_overlap_ok": normal_overlap_ok,
            "feature_leakage_ok": feature_leakage_ok,
        }
    ]
)

qa = {
    "main_13_reproduced": main_reproduced,
    "sensitivity_13_reproduced": sensitivity_reproduced,
    "group_overlap_zero": group_overlap_zero,
    "fixed_eval_49_retained": len(fixed_eval) == 49,
    "normal_35_retained": int(fixed_eval["y"].eq(0).sum()) == 35,
    "positive_14_retained": int(fixed_eval["y"].eq(1).sum()) == 14,
    "accepted_weak_positive_coverage_ge_0_95": weak_coverage_ok,
    "accepted_candidate_normal_no_overlap": normal_overlap_ok,
    "compact13_only": len(features) == 13,
    "feature_leakage_ok": feature_leakage_ok,
    "hierarchy_task_activity_unchanged": bool(
        hier_update.loc[0, "task_policy_unchanged"] == "post_event_context_classifier"
        and hier_update.loc[0, "activity_policy_unchanged"]
        == "overlap_sensitive_predictive_candidate"
        and not bool(hier_update.loc[0, "task_activity_pre_event_applied"])
    ),
}

dataset_summary.to_csv(OUT_SUMMARY, index=False, encoding="utf-8")
metrics.to_csv(OUT_METRICS, index=False, encoding="utf-8")
predictions.to_csv(OUT_PRED, index=False, encoding="utf-8")
decision.to_csv(OUT_DECISION, index=False, encoding="utf-8")
importance.to_csv(OUT_IMPORTANCE, index=False, encoding="utf-8")
error_audit.to_csv(OUT_ERROR, index=False, encoding="utf-8")
hier_update.to_csv(OUT_HIER, index=False, encoding="utf-8")

report = f"""# M1 Fault Pre-Event Gate 13번 Recipe 적용 보고서

## 결론
- final_decision: `{final_decision}`
- fault gate recipe: `expanded_compact13_logistic_balanced_threshold_0.6`
- task/activity 정책은 변경하지 않는다.
- 13번은 `strict_no_event20 fixed eval 49행 + 확장학습` 기반이므로, 25번 `fault_no_overlap 90행` nested search와 직접 동일 평가로 비교하지 않는다.

## 적용 Recipe
| 항목 | 값 |
| --- | --- |
| target | fault pre-event risk / efd_possible positive |
| window | report/fault/event 이전 7일 |
| feature | compact13_overlap 13개 |
| model | SimpleImputer(median) + StandardScaler + LogisticRegression(class_weight="balanced") |
| threshold | 0.6 |
| training | fixed_eval + accepted weak_positive + accepted candidate_normal |

## Decision Matrix
{md_table(decision)}

## Dataset Summary
{md_table(dataset_summary)}

## Metric Summary
{md_table(metrics.loc[metrics['fold'].astype(str).eq('all')], ['strategy','evaluation_scope','fold','n','normal_n','positive_n','balanced_accuracy','precision','recall','f1','false_positive_count','false_negative_count','false_positive_rate','hard_normal_35_48_fp_count','review_required_19_68_fp_count'])}

## 25번과의 관계
- 25번 결론은 `{best25['final_decision']}`이며, RF 기준 fault gate를 유지한다는 검증이었다.
- 이번 27번은 사용자가 지정한 13번 pre-event recipe를 fault gate 후보로 적용하는 별도 검증이다.
- 따라서 27번은 25번을 폐기하지 않고, `fault pre-event gate`의 구현 recipe를 13번 방식으로 문서화/검증한다.

## Error Audit
- expanded_compact13 false positives: {int(expanded_main['false_positive_count'])}
- expanded_compact13 false negatives: {int(expanded_main['false_negative_count'])}
- hard normal 35/48 false positives: {int(expanded_main['hard_normal_35_48_fp_count'])}
- saved file: `m1_fault_pre_event_13_recipe_error_audit.csv`

## Hierarchical Policy Update
{md_table(hier_update)}

## Quality Checks
{md_table(pd.DataFrame([{'check': k, 'pass': v} for k, v in qa.items()]))}

## 해석
- fault에는 pre-event gate를 붙인다.
- task는 post-event context classifier로 유지한다.
- activity는 overlap/missingness-sensitive candidate signal로 유지한다.
- 13번 recipe는 fixed eval 기준에서 재현됐고, 운영 적용 전에는 25번 기준 데이터셋과 평가 기준 차이를 caveat로 유지한다.
"""
OUT_REPORT.write_text(report, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 27. M1 Fault Pre-Event Gate 13번 Recipe 적용\n",
                "\n",
                "This notebook is generated from `scripts/run_27_fault_pre_event_13_recipe_gate_application.py`.\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## Summary\n",
                f"- final_decision: `{final_decision}`\n",
                "- fault only uses the 13번 pre-event recipe.\n",
                "- task/activity policies are unchanged.\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from pathlib import Path\n",
                "import pandas as pd\n",
                "out = next(p for p in Path.cwd().iterdir() if p.is_dir() and p.name.startswith('07_'))\n",
                "pd.read_csv(out / 'm1_fault_pre_event_13_recipe_decision_matrix.csv')\n",
            ],
        },
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
OUT_NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")

print("Wrote")
for path in [
    OUT_NOTEBOOK,
    OUT_REPORT,
    OUT_SUMMARY,
    OUT_METRICS,
    OUT_PRED,
    OUT_DECISION,
    OUT_IMPORTANCE,
    OUT_ERROR,
    OUT_HIER,
]:
    print(path.name)
print(decision.to_string(index=False))
print(qa)
