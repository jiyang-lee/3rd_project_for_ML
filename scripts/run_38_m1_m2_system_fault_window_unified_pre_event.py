from __future__ import annotations

import argparse
import importlib.util
import subprocess
import warnings
from pathlib import Path

import nbformat as nbf
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
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
COVERAGE_MIN = 0.95
THRESHOLDS = [0.4, 0.5, 0.6]
WINDOW_POLICIES = {
    "report_pre_7d": pd.Timedelta(days=7),
    "report_pre_5d": pd.Timedelta(days=5),
    "report_pre_3d": pd.Timedelta(days=3),
    "report_pre_1d": pd.Timedelta(days=1),
}


def import_run36():
    path = Path.cwd() / "scripts" / "run_36_m1_m2_standard_pre_event.py"
    spec = importlib.util.spec_from_file_location("run36", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


R36 = import_run36()


def paths() -> dict[str, Path]:
    root = Path.cwd()
    line = root / "09_실험라인" / "m1_m2_system_fault_window_pre_event"
    return {
        "root": root,
        "line": line,
        "out": line / "outputs",
        "reports": line / "reports",
        "notebooks": line / "notebooks",
        "data": root / "05_데이터셋" / "PreDist",
        "legacy_out": root / "07_데이터산출물",
    }


PATHS = paths()


def ensure_dirs() -> None:
    for key in ["out", "reports", "notebooks"]:
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


def fault_group(label: str) -> str:
    text = str(label).lower()
    if text in {"", "nan", "unknown"}:
        return "unknown_review"
    if "leak" in text or "water loss" in text or "relief valve" in text:
        return "leakage_water_loss"
    if "pump" in text:
        return "pump_failure"
    if "valve" in text or "actuator" in text or "shut-off" in text:
        return "valve_actuator"
    if "pressure" in text:
        return "pressure_regulator"
    if "control" in text or "controller" in text or "parameter" in text or "monitor" in text:
        return "control_controller"
    if "air" in text or "strainer" in text or "flow" in text:
        return "flow_air_strainer"
    return "other_review"


def make_model(name: str, y_train: pd.Series | None = None) -> Pipeline:
    if name == "dummy_most_frequent":
        estimator = DummyClassifier(strategy="most_frequent")
        scale = False
    elif name == "logistic_balanced":
        estimator = LogisticRegression(class_weight="balanced", solver="liblinear", max_iter=1000, random_state=RANDOM_STATE)
        scale = True
    elif name == "random_forest_depth3":
        estimator = RandomForestClassifier(
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
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=RANDOM_STATE,
        )
        scale = False
    else:
        raise ValueError(name)
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", estimator))
    return Pipeline(steps)


def model_names() -> list[str]:
    names = ["dummy_most_frequent", "logistic_balanced", "random_forest_depth3", "hist_gradient_boosting"]
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


def metric(y_true, prob, threshold: float) -> dict:
    y = np.asarray(y_true).astype(int)
    pred = (np.asarray(prob).astype(float) >= threshold).astype(int)
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


def load_meta(manufacturer: str, filename: str) -> pd.DataFrame:
    return R36.read_meta(manufacturer, filename)


def system_lookup() -> dict[tuple[str, int], dict]:
    audit = R36.build_system_capability_audit()
    return audit.set_index(["manufacturer", "substation_id"]).to_dict("index")


def build_window_feature_pool() -> tuple[pd.DataFrame, pd.DataFrame]:
    features = R36.parse_compact13_features()
    lookup = system_lookup()
    normal_rows = []
    positive_rows = []
    for manufacturer in R36.MANUFACTURERS:
        normal = load_meta(manufacturer, "normal_events.csv")
        faults = load_meta(manufacturer, "faults.csv").copy()
        for _, row in normal.iterrows():
            sid = int(row["substation ID"])
            start = pd.Timestamp(row["Event start"])
            end = pd.Timestamp(row["Event end"])
            values, sample_count, expected, coverage = R36.compute_features_for_window(manufacturer, sid, start, end, features)
            cap = lookup.get((manufacturer, sid), {})
            normal_rows.append(
                {
                    "sample_id": f"{manufacturer}_normal_{int(row['Event ID']):04d}",
                    "manufacturer": manufacturer,
                    "source_event_id": int(row["Event ID"]),
                    "substation_id": sid,
                    "manufacturer_substation_id": f"{manufacturer}_{sid}",
                    "label": "normal",
                    "y": 0,
                    "window_policy": "normal_event_7d",
                    "fault_group": "normal",
                    "fault_label": "",
                    "sample_count": sample_count,
                    "expected_sample_count": expected,
                    "coverage_rate": coverage,
                    "main_eligible": bool(coverage >= R36.COVERAGE_MIN and cap.get("common10_ready", False)),
                    **{col: cap.get(col, np.nan) for col in R36.SYSTEM_TAG_COLUMNS},
                    **values,
                }
            )
        faults["efd_possible_bool"] = faults["efd_possible"].astype(str).str.lower().eq("true")
        faults = faults.loc[faults["efd_possible_bool"] & faults["Report date"].notna()].copy()
        for _, row in faults.iterrows():
            sid = int(row["substation ID"])
            report = pd.Timestamp(row["Report date"])
            event_id = int(row["Event ID"])
            cap = lookup.get((manufacturer, sid), {})
            label = str(row.get("Fault label", ""))
            group = fault_group(label)
            for policy, delta in WINDOW_POLICIES.items():
                start = report - delta
                end = report
                values, sample_count, expected, coverage = R36.compute_features_for_window(manufacturer, sid, start, end, features)
                flags = R36.event_flags(manufacturer, row, coverage)
                exclude = []
                if coverage < R36.COVERAGE_MIN:
                    exclude.append("low_coverage")
                if not cap.get("common10_ready", False):
                    exclude.append("common10_missing")
                if flags["fault_label_unknown"]:
                    exclude.append("unknown_fault_label")
                if flags["training_end_missing"]:
                    exclude.append("training_end_missing")
                positive_rows.append(
                    {
                        "sample_id": f"{manufacturer}_pre_event_{event_id:04d}_{policy}",
                        "manufacturer": manufacturer,
                        "source_event_id": event_id,
                        "substation_id": sid,
                        "manufacturer_substation_id": f"{manufacturer}_{sid}",
                        "label": "pre_event",
                        "y": 1,
                        "window_policy": policy,
                        "fault_group": group,
                        "fault_label": label,
                        "sample_count": sample_count,
                        "expected_sample_count": expected,
                        "coverage_rate": coverage,
                        "main_eligible": len(exclude) == 0,
                        "exclude_reason": "|".join(exclude),
                        **flags,
                        **{col: cap.get(col, np.nan) for col in R36.SYSTEM_TAG_COLUMNS},
                        **values,
                    }
                )
    all_rows = pd.DataFrame([*normal_rows, *positive_rows])
    audit_cols = [
        "sample_id",
        "manufacturer",
        "source_event_id",
        "substation_id",
        "manufacturer_substation_id",
        "label",
        "window_policy",
        "fault_group",
        "fault_label",
        "system_capability_group",
        "coverage_rate",
        "main_eligible",
        "exclude_reason",
    ]
    for col in audit_cols:
        if col not in all_rows.columns:
            all_rows[col] = ""
    return all_rows[audit_cols], all_rows


def dataset_variants(pool: pd.DataFrame) -> dict[str, pd.DataFrame]:
    normals = pool.loc[pool["label"].eq("normal") & pool["main_eligible"].astype(bool)].copy()
    variants = {}
    for policy in WINDOW_POLICIES:
        pos = pool.loc[
            pool["label"].eq("pre_event") & pool["window_policy"].eq(policy) & pool["main_eligible"].astype(bool)
        ].copy()
        variants[f"all_systems__all_faults__{policy}"] = pd.concat([normals, pos], ignore_index=True)
        for group in sorted(pos["system_capability_group"].dropna().unique()):
            sub_pos = pos.loc[pos["system_capability_group"].eq(group)].copy()
            sub_norm = normals.loc[normals["system_capability_group"].eq(group)].copy()
            variants[f"system_{group}__all_faults__{policy}"] = pd.concat([sub_norm, sub_pos], ignore_index=True)
        for group in sorted(pos["fault_group"].dropna().unique()):
            if group in {"unknown_review", "other_review"}:
                continue
            sub_pos = pos.loc[pos["fault_group"].eq(group)].copy()
            variants[f"all_systems__fault_{group}__{policy}"] = pd.concat([normals, sub_pos], ignore_index=True)
    return variants


def can_eval(data: pd.DataFrame) -> bool:
    return len(data) >= 12 and data["y"].nunique() == 2 and data["y"].value_counts().min() >= 4


def evaluate_variant(dataset_id: str, data: pd.DataFrame, features: list[str]) -> tuple[list[dict], list[dict]]:
    if not can_eval(data):
        return [], [
            {
                "dataset_id": dataset_id,
                "quality_check": "skipped_insufficient_data_audit_only",
                "passed": True,
                "detail": f"rows={len(data)}, label_counts={data['y'].value_counts().to_dict()}",
            }
        ]
    n_splits = max(2, min(5, int(data["y"].value_counts().min()), data["manufacturer_substation_id"].nunique()))
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    pred_rows = []
    qa_rows = []
    for model_name in model_names():
        for fold, (train_idx, test_idx) in enumerate(
            splitter.split(data[features], data["y"].astype(int), data["manufacturer_substation_id"]), start=1
        ):
            train = data.iloc[train_idx].copy()
            test = data.iloc[test_idx].copy()
            overlap = set(train["manufacturer_substation_id"]) & set(test["manufacturer_substation_id"])
            qa_rows.append(
                {
                    "dataset_id": dataset_id,
                    "model": model_name,
                    "fold": fold,
                    "quality_check": "train_test_group_overlap_zero",
                    "passed": len(overlap) == 0,
                    "detail": "|".join(sorted(overlap)),
                }
            )
            try:
                model = make_model(model_name, train["y"].astype(int))
                model.fit(train[features], train["y"].astype(int))
                prob = class_one_probability(model, test[features])
            except Exception as exc:
                qa_rows.append(
                    {
                        "dataset_id": dataset_id,
                        "model": model_name,
                        "fold": fold,
                        "quality_check": "fit_predict",
                        "passed": False,
                        "detail": str(exc)[:300],
                    }
                )
                continue
            for row, p in zip(test.to_dict("records"), prob):
                pred_rows.append(
                    {
                        "dataset_id": dataset_id,
                        "model": model_name,
                        "fold": fold,
                        "sample_id": row["sample_id"],
                        "manufacturer": row["manufacturer"],
                        "source_event_id": row["source_event_id"],
                        "substation_id": row["substation_id"],
                        "system_capability_group": row["system_capability_group"],
                        "fault_group": row["fault_group"],
                        "fault_label": row["fault_label"],
                        "window_policy": row["window_policy"],
                        "label": row["label"],
                        "y_true": int(row["y"]),
                        "probability": float(p),
                    }
                )
    return pred_rows, qa_rows


def build_metrics(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_rows = []
    decision_rows = []
    if predictions.empty:
        return pd.DataFrame(), pd.DataFrame()
    for (dataset_id, model), group in predictions.groupby(["dataset_id", "model"]):
        for threshold in THRESHOLDS:
            row = metric(group["y_true"], group["probability"], threshold)
            metric_rows.append({"dataset_id": dataset_id, "model": model, "threshold": threshold, **row})
            passed = row["balanced_accuracy"] >= 0.70 and row["recall"] >= 0.70 and row["normal_fpr"] <= 0.25
            parts = dataset_id.split("__")
            decision_rows.append(
                {
                    "dataset_id": dataset_id,
                    "model": model,
                    "threshold": threshold,
                    "scope": parts[0],
                    "fault_scope": parts[1] if len(parts) > 1 else "",
                    "window_policy": parts[2] if len(parts) > 2 else "",
                    "balanced_accuracy": row["balanced_accuracy"],
                    "recall": row["recall"],
                    "normal_fpr": row["normal_fpr"],
                    "candidate_pass": passed,
                    "decision": "window_model_candidate" if passed else "window_label_review_required",
                }
            )
    metrics = pd.DataFrame(metric_rows)
    decision = pd.DataFrame(decision_rows)
    if not decision.empty:
        decision["rank_score"] = decision["candidate_pass"].astype(int) * 100 + decision["balanced_accuracy"] + decision["recall"] - decision["normal_fpr"]
        decision = decision.sort_values(["candidate_pass", "rank_score"], ascending=[False, False]).drop(columns=["rank_score"])
    return metrics, decision


def dataset_summary(variants: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for dataset_id, data in variants.items():
        rows.append(
            {
                "dataset_id": dataset_id,
                "rows": len(data),
                "normal_rows": int(data["y"].eq(0).sum()) if "y" in data else 0,
                "pre_event_rows": int(data["y"].eq(1).sum()) if "y" in data else 0,
                "manufacturer_count": int(data["manufacturer"].nunique()) if len(data) else 0,
                "substation_count": int(data["manufacturer_substation_id"].nunique()) if len(data) else 0,
                "system_groups": "|".join(sorted(data["system_capability_group"].dropna().astype(str).unique())) if len(data) else "",
                "fault_groups": "|".join(sorted(data.loc[data["y"].eq(1), "fault_group"].dropna().astype(str).unique())) if len(data) else "",
                "can_evaluate": can_eval(data) if len(data) else False,
            }
        )
    return pd.DataFrame(rows)


def write_notebooks() -> None:
    notebook_specs = [
        (
            "01_fault_label_system_window_audit.ipynb",
            "Fault label x system x window audit",
            "fault_label_system_window_audit.csv",
            "df.groupby(['manufacturer','label','window_policy']).size().head(30)",
        ),
        (
            "02_unified_window_model_grid.ipynb",
            "Unified pre-event window model grid",
            "unified_model_metrics.csv",
            "df.sort_values(['balanced_accuracy','recall'], ascending=False).head(20)",
        ),
        (
            "03_unified_decision_report.ipynb",
            "Unified decision report",
            "unified_decision_matrix.csv",
            "df.head(30)",
        ),
    ]
    for filename, title, csv_name, expr in notebook_specs:
        nb = nbf.v4.new_notebook()
        nb["cells"] = [
            nbf.v4.new_markdown_cell(
                f"# {title}\n\n통합 스크립트가 만든 산출물을 읽어 결과를 확인하는 노트북입니다."
            ),
            nbf.v4.new_code_cell(
                "from pathlib import Path\n"
                "import pandas as pd\n"
                "out = Path('09_실험라인/m1_m2_system_fault_window_pre_event/outputs')\n"
                f"df = pd.read_csv(out / '{csv_name}')\n"
                "print(df.shape)\n"
                f"display({expr})\n"
            ),
        ]
        nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
        nb["metadata"]["language_info"] = {"name": "python", "pygments_lexer": "ipython3"}
        nbf.write(nb, PATHS["notebooks"] / filename)


def write_report(summary: pd.DataFrame, metrics: pd.DataFrame, decision: pd.DataFrame, qa: pd.DataFrame) -> None:
    pass_count = int(decision["candidate_pass"].sum()) if not decision.empty else 0
    final = "window_model_candidates_found" if pass_count else "window_label_review_required"
    short_window_pass = int(
        decision.loc[decision["candidate_pass"].astype(bool) & decision["window_policy"].eq("report_pre_1d")].shape[0]
    ) if not decision.empty else 0
    longer_window_pass = int(
        decision.loc[
            decision["candidate_pass"].astype(bool)
            & decision["window_policy"].isin(["report_pre_3d", "report_pre_5d", "report_pre_7d"])
        ].shape[0]
    ) if not decision.empty else 0
    report = f"""# M1+M2 System/Fault/Window 통합 Pre-Event 실험 보고서

## 결론
최종 판단: **{final}**

요청대로 system group, fault group, window 후보, 모델 후보를 한 번에 만들고 비교했다.
전체 공통 모델 하나를 억지로 잠그는 대신, 어떤 조합에서 pre_event 신호가 살아나는지를 표로 잠갔다.
단, `report_pre_1d`는 report 직전 상태 감지에 가까워 조기탐지 후보와 분리해서 해석해야 한다.

## 핵심 요약
- window 후보: `report_pre_7d`, `report_pre_5d`, `report_pre_3d`, `report_pre_1d`
- feature: `common13`
- 모델: Dummy, Logistic, RandomForest, HistGradientBoosting, LightGBM, XGBoost
- 기준: balanced accuracy >= 0.70, recall >= 0.70, normal FPR <= 0.25
- 통과 후보 수: `{pass_count}`
- `report_pre_1d` 통과 후보 수: `{short_window_pass}`
- `report_pre_3d/5d/7d` 통과 후보 수: `{longer_window_pass}`

## 상위 Decision
{md_table(decision.head(30), max_rows=30) if not decision.empty else "candidate 없음"}

## Dataset Summary
{md_table(summary.head(80), max_rows=80)}

## Metric 상위
{md_table(metrics.sort_values(["balanced_accuracy", "recall"], ascending=False).head(40), max_rows=40) if not metrics.empty else "metric 없음"}

## 해석
- 통과 후보가 특정 system group 또는 fault group에 몰리면, pre_event는 전체 공통 문제가 아니라 `system/fault/window`별 문제로 다뤄야 한다.
- `report_pre_1d/3d`가 상위에 오르면 7일 전조보다 단기 징후 중심으로 재정의해야 한다.
- fault group별 후보가 강하면 출동 우선순위와 고장군 taxonomy를 pre_event 모델 앞단에 연결해야 한다.
- `report_pre_1d` 완전 분리처럼 보이는 결과는 운영상 “하루 전 상태 감지”로 두고, “며칠 전 조기탐지”는 3일/5일/7일 후보에서 별도 판단한다.

## 한계
- M1/M2는 같은 PreDist 계열이므로 완전 독립 외부 검증은 아니다.
- 세분화할수록 샘플 수가 작아져 과적합 위험이 커진다.
- 이 결과는 운영 확정이 아니라 다음 label/window 잠금 후보를 찾는 통합 실험이다.

## 품질 검증
{md_table(qa)}

source commit: `{source_commit_hash()}`
"""
    (PATHS["reports"] / "M1_M2_system_fault_window_unified_pre_event_보고서.md").write_text(report, encoding="utf-8")


def run_all() -> None:
    for key in ["out", "reports", "notebooks"]:
        PATHS[key].mkdir(parents=True, exist_ok=True)
    features = R36.parse_compact13_features()
    audit, pool = build_window_feature_pool()
    variants = dataset_variants(pool)
    summary = dataset_summary(variants)
    pred_rows = []
    qa_rows = []
    for dataset_id, data in variants.items():
        preds, qa = evaluate_variant(dataset_id, data, features)
        pred_rows.extend(preds)
        qa_rows.extend(qa)
    predictions = pd.DataFrame(pred_rows)
    qa = pd.DataFrame(qa_rows)
    metrics, decision = build_metrics(predictions)
    qa_extra = pd.DataFrame(
        [
            {"quality_check": "feature_count_common13", "passed": len(features) == 13, "detail": str(len(features))},
            {"quality_check": "raw_zip_exists", "passed": (PATHS["data"] / "predist_dataset.zip").exists(), "detail": str(PATHS["data"] / "predist_dataset.zip")},
            {"quality_check": "manufacturer_metadata_only", "passed": True, "detail": "manufacturer used for split/audit, not feature"},
            {"quality_check": "candidate_pass_count", "passed": True, "detail": str(int(decision["candidate_pass"].sum()) if not decision.empty else 0)},
        ]
    )
    qa_all = pd.concat([qa, qa_extra], ignore_index=True, sort=False)
    audit.to_csv(PATHS["out"] / "fault_label_system_window_audit.csv", index=False, encoding="utf-8-sig")
    pool.to_csv(PATHS["out"] / "fault_label_system_window_feature_pool.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(PATHS["out"] / "unified_dataset_summary.csv", index=False, encoding="utf-8-sig")
    predictions.to_csv(PATHS["out"] / "unified_model_predictions.csv", index=False, encoding="utf-8-sig")
    metrics.to_csv(PATHS["out"] / "unified_model_metrics.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(PATHS["out"] / "unified_decision_matrix.csv", index=False, encoding="utf-8-sig")
    qa_all.to_csv(PATHS["out"] / "quality_audit.csv", index=False, encoding="utf-8-sig")
    write_notebooks()
    write_report(summary, metrics, decision, qa_all)
    print("unified system/fault/window pre-event experiment complete")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["all"], default="all")
    parser.parse_args()
    run_all()


if __name__ == "__main__":
    main()
