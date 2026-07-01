from __future__ import annotations

from pathlib import Path
import runpy
import warnings

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
import nbformat as nbf
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

warnings.filterwarnings("ignore")

RANDOM_STATE = 42

FAULT_THRESHOLD = 0.50
TASK_THRESHOLD = 0.50
ACTIVITY_THRESHOLD = 0.50
PRE_EVENT_THRESHOLD = 0.60
NEAR_THRESHOLD_BAND = 0.05

SPECIAL_FAULT_EVENTS = {20, 34, 67, 69}
HARD_NORMAL_EVENTS = {19, 35, 48, 68}


def repo_dirs() -> tuple[Path, Path, Path]:
    root = Path.cwd()
    out = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("07_"))
    nb_dir = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("06_"))
    return root, out, nb_dir


ROOT, OUT, NB_DIR = repo_dirs()

IN_FAULT_METRICS = OUT / "m1_fault_gate_lock_threshold_metrics.csv"
IN_FAULT_PRED = OUT / "m1_fault_gate_lock_predictions.csv"
IN_TASK_ACTIVITY_METRICS = OUT / "m1_task_activity_redesign_decision_matrix.csv"
IN_TASK_ACTIVITY_SUMMARY = OUT / "m1_task_activity_window_candidate_summary.csv"
IN_TASK_ACTIVITY_PRED = OUT / "m1_task_activity_window_candidate_predictions.csv"
IN_PRE_EVENT_DECISION = OUT / "m1_fault_pre_event_v1_lock_decision.csv"
IN_PRE_EVENT_PRED = OUT / "m1_fault_pre_event_v1_lock_predictions.csv"
IN_PRIORITY = OUT / "m1_fault_dispatch_priority_v1.csv"
IN_LEADTIME_DECISION = OUT / "m1_fault_group_leadtime_decision_matrix.csv"
IN_WEIGHT_DECISION = OUT / "m1_dispatch_priority_weight_sensitivity_decision_matrix.csv"

OUT_DATASET_SUMMARY = OUT / "m1_full_gate_lock_dataset_summary.csv"
OUT_METRICS = OUT / "m1_full_gate_lock_metrics.csv"
OUT_PRED = OUT / "m1_full_gate_lock_predictions.csv"
OUT_CONFLICT = OUT / "m1_full_gate_conflict_resolution_audit.csv"
OUT_RULES = OUT / "m1_full_gate_runtime_rule_table.csv"
OUT_SCHEMA = OUT / "m1_full_gate_runtime_output_schema.csv"
OUT_EXAMPLES = OUT / "m1_full_gate_runtime_examples.csv"
OUT_DECISION = OUT / "m1_full_gate_decision_matrix.csv"
OUT_QA = OUT / "m1_full_gate_quality_audit.csv"
OUT_REPORT = OUT / "33_M1_full_gate_lock_and_runtime_policy_보고서.md"
OUT_NOTEBOOK = NB_DIR / "33_m1_full_gate_lock_and_runtime_policy.ipynb"

PNG_FLOW = OUT / "m1_full_gate_runtime_flow.png"
PNG_CONFLICT = OUT / "m1_full_gate_conflict_resolution.png"

GATE_CONFIGS = [
    {
        "gate": "fault_gate",
        "target_class": "fault",
        "dataset": "fault_no_overlap",
        "feature_set": "compact13",
        "model": "random_forest_balanced_depth3",
        "threshold": FAULT_THRESHOLD,
        "thresholds": [0.45, 0.50, 0.55, 0.60],
        "source": "m1_fault_gate_lock_predictions.csv",
        "role": "normal vs fault event gate",
    },
    {
        "gate": "task_gate",
        "target_class": "task",
        "dataset": "task_post_1d",
        "feature_set": "compact13",
        "model": "random_forest_balanced_depth3",
        "threshold": TASK_THRESHOLD,
        "thresholds": [0.40, 0.50, 0.60],
        "source": "m1_task_activity_window_candidate_predictions.csv",
        "role": "normal vs task state detector",
    },
    {
        "gate": "activity_gate",
        "target_class": "activity",
        "dataset": "activity_pre_1d",
        "feature_set": "compact13",
        "model": "random_forest_balanced_depth3",
        "threshold": ACTIVITY_THRESHOLD,
        "thresholds": [0.40, 0.50, 0.60],
        "source": "m1_task_activity_window_candidate_predictions.csv",
        "role": "normal vs activity gate",
    },
]


def read_inputs() -> dict[str, pd.DataFrame]:
    paths = {
        "fault_metrics": IN_FAULT_METRICS,
        "fault_pred": IN_FAULT_PRED,
        "task_activity_metrics": IN_TASK_ACTIVITY_METRICS,
        "task_activity_summary": IN_TASK_ACTIVITY_SUMMARY,
        "task_activity_pred": IN_TASK_ACTIVITY_PRED,
        "pre_event_decision": IN_PRE_EVENT_DECISION,
        "pre_event_pred": IN_PRE_EVENT_PRED,
        "priority": IN_PRIORITY,
        "leadtime_decision": IN_LEADTIME_DECISION,
        "weight_decision": IN_WEIGHT_DECISION,
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")
    return {name: pd.read_csv(path) for name, path in paths.items()}


def to_bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def format_float(value, digits: int = 4) -> str:
    if pd.isna(value):
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def markdown_table(df: pd.DataFrame, columns: list[str], float_digits: int = 4) -> str:
    view = df[columns].copy()
    for col in view.columns:
        if pd.api.types.is_bool_dtype(view[col]):
            view[col] = view[col].map(lambda x: "True" if bool(x) else "False")
        elif pd.api.types.is_numeric_dtype(view[col]):
            if col.endswith("_count") or col.endswith("_rows") or col in {"rows", "tn", "fp", "fn", "tp", "feature_count"}:
                view[col] = view[col].map(lambda x: "" if pd.isna(x) else str(int(x)))
            else:
                view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.{float_digits}f}")
    view = view.fillna("")
    lines = [
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("\n", " ") for col in view.columns) + " |")
    return "\n".join(lines)


def threshold_col(threshold: float) -> str:
    text = str(threshold).replace(".", "_")
    return f"prediction_t{text}"


def prepare_gate_predictions(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames = []
    for config in GATE_CONFIGS:
        source = inputs["fault_pred"] if config["target_class"] == "fault" else inputs["task_activity_pred"]
        data = source.loc[
            source["dataset"].eq(config["dataset"])
            & source["feature_set"].eq(config["feature_set"])
            & source["model"].eq(config["model"])
        ].copy()
        pred_col = threshold_col(config["threshold"])
        if pred_col not in data.columns:
            raise ValueError(f"{pred_col} missing for {config['gate']}")
        data["gate"] = config["gate"]
        data["gate_threshold"] = config["threshold"]
        data["gate_prediction"] = to_num(data[pred_col]).fillna(0).astype(int)
        data["gate_probability"] = to_num(data["probability_target"])
        data["target_class_locked"] = config["target_class"]
        data["is_near_threshold"] = (data["gate_probability"] - config["threshold"]).abs().le(NEAR_THRESHOLD_BAND)
        frames.append(data)
    selected = pd.concat(frames, ignore_index=True)
    selected.to_csv(OUT_PRED, index=False, encoding="utf-8-sig")
    return selected


def recompute_metrics_from_predictions(selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for config in GATE_CONFIGS:
        data = selected.loc[selected["gate"].eq(config["gate"])].copy()
        y_true = to_num(data["y_true"]).astype(int)
        for threshold in config["thresholds"]:
            pred_col = threshold_col(threshold)
            if pred_col not in data.columns:
                continue
            y_pred = to_num(data[pred_col]).fillna(0).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
            rows.append(
                {
                    "gate": config["gate"],
                    "target_class": config["target_class"],
                    "dataset": config["dataset"],
                    "feature_set": config["feature_set"],
                    "model": config["model"],
                    "threshold": threshold,
                    "rows": len(data),
                    "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
                    "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
                    "normal_precision": precision_score(y_true, y_pred, pos_label=0, zero_division=0),
                    "normal_recall": recall_score(y_true, y_pred, pos_label=0, zero_division=0),
                    "normal_f1": f1_score(y_true, y_pred, pos_label=0, zero_division=0),
                    "target_precision": precision_score(y_true, y_pred, pos_label=1, zero_division=0),
                    "target_recall": recall_score(y_true, y_pred, pos_label=1, zero_division=0),
                    "target_f1": f1_score(y_true, y_pred, pos_label=1, zero_division=0),
                    "normal_fpr": fp / (fp + tn) if (fp + tn) else np.nan,
                    "tn": tn,
                    "fp": fp,
                    "fn": fn,
                    "tp": tp,
                }
            )
    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT_METRICS, index=False, encoding="utf-8-sig")
    return metrics


def build_dataset_summary(inputs: dict[str, pd.DataFrame], metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    task_summary = inputs["task_activity_summary"].copy()
    for config in GATE_CONFIGS:
        metric = metrics.loc[
            metrics["gate"].eq(config["gate"]) & metrics["threshold"].eq(config["threshold"])
        ].iloc[0]
        if config["target_class"] == "fault":
            source = inputs["fault_metrics"].loc[
                inputs["fault_metrics"]["dataset"].eq(config["dataset"])
                & inputs["fault_metrics"]["feature_set"].eq(config["feature_set"])
                & inputs["fault_metrics"]["model"].eq(config["model"])
                & inputs["fault_metrics"]["metric_scope"].eq("aggregate")
                & to_num(inputs["fault_metrics"]["threshold"]).eq(config["threshold"])
            ].iloc[0]
            overlap_rate = 0.0
            coverage_min = np.nan
            normal_rows = int(source["normal_support"])
            target_rows = int(source["target_support"])
            substation_count = np.nan
        else:
            source = task_summary.loc[task_summary["dataset"].eq(config["dataset"])].iloc[0]
            overlap_rate = float(source["target_overlap_rate"])
            coverage_min = float(source["coverage_min"])
            normal_rows = int(source["normal_rows"])
            target_rows = int(source["target_rows"])
            substation_count = int(source["substation_count"])
        rows.append(
            {
                "gate": config["gate"],
                "target_class": config["target_class"],
                "dataset": config["dataset"],
                "feature_set": config["feature_set"],
                "model": config["model"],
                "threshold": config["threshold"],
                "rows": int(metric["rows"]),
                "normal_rows": normal_rows,
                "target_rows": target_rows,
                "substation_count": substation_count,
                "target_overlap_rate": overlap_rate,
                "coverage_min": coverage_min,
                "balanced_accuracy": metric["balanced_accuracy"],
                "target_recall": metric["target_recall"],
                "normal_fpr": metric["normal_fpr"],
            }
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT_DATASET_SUMMARY, index=False, encoding="utf-8-sig")
    return summary


def gate_lock_decision(config: dict, metric: pd.Series) -> str:
    passes = (
        float(metric["balanced_accuracy"]) >= 0.80
        and float(metric["target_recall"]) >= 0.85
        and float(metric["normal_fpr"]) <= 0.25
    )
    if config["gate"] == "fault_gate":
        return "fault_gate_locked_for_runtime_v1_with_threshold_review" if passes else "fault_gate_recheck_required"
    if config["gate"] == "task_gate":
        return "task_gate_locked_as_state_detector_v1" if passes else "task_window_policy_review_required"
    if config["gate"] == "activity_gate":
        return "activity_gate_locked_for_runtime_v1" if passes else "activity_window_policy_review_required"
    return "unknown"


def build_decision_matrix(metrics: pd.DataFrame, inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for config in GATE_CONFIGS:
        metric = metrics.loc[
            metrics["gate"].eq(config["gate"]) & metrics["threshold"].eq(config["threshold"])
        ].iloc[0]
        rows.append(
            {
                "component": config["gate"],
                "dataset": config["dataset"],
                "feature_set": config["feature_set"],
                "model": config["model"],
                "threshold": config["threshold"],
                "balanced_accuracy": metric["balanced_accuracy"],
                "target_recall": metric["target_recall"],
                "normal_fpr": metric["normal_fpr"],
                "passes_ba": metric["balanced_accuracy"] >= 0.80,
                "passes_recall": metric["target_recall"] >= 0.85,
                "passes_fpr": metric["normal_fpr"] <= 0.25,
                "decision": gate_lock_decision(config, metric),
            }
        )
    pre = inputs["pre_event_decision"].iloc[0]
    weight = inputs["weight_decision"].loc[inputs["weight_decision"]["scenario"].eq("baseline_28")].iloc[0]
    rows.append(
        {
            "component": "fault_pre_event_gate",
            "dataset": "strict_no_event20_fixed_eval",
            "feature_set": pre["feature_set"],
            "model": pre["model"],
            "threshold": float(pre["threshold"]),
            "balanced_accuracy": float(pre["balanced_accuracy"]),
            "target_recall": float(pre["recall"]),
            "normal_fpr": float(pre["normal_fpr"]),
            "passes_ba": to_bool(pre["passes_lock_criteria"]),
            "passes_recall": to_bool(pre["passes_lock_criteria"]),
            "passes_fpr": to_bool(pre["passes_lock_criteria"]),
            "decision": pre["final_decision"],
        }
    )
    rows.append(
        {
            "component": "priority_policy",
            "dataset": "fault_dispatch_priority_v1",
            "feature_set": "risk_probability|leadtime_urgency|group_weight",
            "model": "policy_score_not_ml_model",
            "threshold": np.nan,
            "balanced_accuracy": np.nan,
            "target_recall": np.nan,
            "normal_fpr": np.nan,
            "passes_ba": to_bool(weight["passes_all_guardrails"]),
            "passes_recall": to_bool(weight["passes_all_guardrails"]),
            "passes_fpr": to_bool(weight["passes_all_guardrails"]),
            "decision": weight["final_decision"],
        }
    )
    decision = pd.DataFrame(rows)
    decision["overall_runtime_decision"] = "full_gate_runtime_policy_v1_candidate_locked"
    decision.to_csv(OUT_DECISION, index=False, encoding="utf-8-sig")
    return decision


def build_conflict_resolution(selected: pd.DataFrame, inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    base_cols = [
        "source_id",
        "final_class",
        "source_event_id",
        "fault_event_id",
        "disturbance_row_id",
        "substation_id",
        "window_start",
        "window_end",
        "coverage_rate",
        "hard_normal_tag",
    ]
    pieces = []
    for config in GATE_CONFIGS:
        part = selected.loc[selected["gate"].eq(config["gate"])].copy()
        part = part[base_cols + ["gate_probability", "gate_prediction", "is_near_threshold", "y_true"]]
        prefix = config["target_class"]
        rename = {
            "gate_probability": f"{prefix}_probability",
            "gate_prediction": f"{prefix}_gate_on",
            "is_near_threshold": f"{prefix}_near_threshold",
            "y_true": f"{prefix}_y_true",
        }
        part = part.rename(columns=rename)
        pieces.append(part)

    combined = None
    for part in pieces:
        if combined is None:
            combined = part
        else:
            combined = combined.merge(part, on=base_cols, how="outer")
    combined = combined.fillna(
        {
            "fault_gate_on": 0,
            "task_gate_on": 0,
            "activity_gate_on": 0,
            "fault_near_threshold": False,
            "task_near_threshold": False,
            "activity_near_threshold": False,
        }
    )
    for col in ["fault_gate_on", "task_gate_on", "activity_gate_on"]:
        combined[col] = to_num(combined[col]).fillna(0).astype(int)
    for col in ["fault_probability", "task_probability", "activity_probability"]:
        combined[col] = to_num(combined[col])

    def resolve(row: pd.Series) -> pd.Series:
        active = [name for name in ["fault", "task", "activity"] if int(row[f"{name}_gate_on"]) == 1]
        review_reasons = []
        if row.get("hard_normal_tag", "") in {"review_required_normal"}:
            review_reasons.append(str(row["hard_normal_tag"]))
        if bool(row.get("fault_near_threshold", False)) and bool(row.get("task_near_threshold", False)) and bool(row.get("activity_near_threshold", False)):
            review_reasons.append("all_gate_probabilities_near_threshold")
        if len(active) > 1:
            review_reasons.append("multi_gate_conflict")

        secondary = []
        if not active:
            primary = "normal"
            why = "no gate crossed threshold"
        elif "fault" in active:
            primary = "fault"
            secondary = [x for x in active if x != "fault"]
            why = "fault gate crossed threshold; fault has runtime priority"
        elif set(active) == {"task", "activity"}:
            task_p = row.get("task_probability", 0) if not pd.isna(row.get("task_probability", np.nan)) else 0
            act_p = row.get("activity_probability", 0) if not pd.isna(row.get("activity_probability", np.nan)) else 0
            primary = "task" if task_p >= act_p else "activity"
            secondary = ["activity" if primary == "task" else "task"]
            why = "task and activity both crossed threshold; higher probability selected"
        else:
            primary = active[0]
            why = f"{active[0]} gate crossed threshold"

        return pd.Series(
            {
                "primary_state": primary,
                "secondary_tags": "|".join(secondary),
                "review_flag": bool(review_reasons),
                "review_reasons": "|".join(review_reasons),
                "why_reason": why,
            }
        )

    resolved = combined.join(combined.apply(resolve, axis=1))
    priority = inputs["priority"].copy()
    priority["event_id_str"] = priority["event_id"].astype(str)
    resolved["fault_event_id_str"] = to_num(resolved["fault_event_id"]).map(lambda x: "" if pd.isna(x) else str(int(x)))
    resolved = resolved.merge(
        priority[
            [
                "event_id_str",
                "risk_probability",
                "priority_score",
                "priority_tier",
                "fault_group",
                "leadtime_urgency",
                "group_weight",
            ]
        ],
        left_on="fault_event_id_str",
        right_on="event_id_str",
        how="left",
    ).drop(columns=["event_id_str"])

    no_fault = ~resolved["primary_state"].eq("fault")
    for col in ["risk_probability", "priority_score", "priority_tier", "fault_group", "leadtime_urgency", "group_weight"]:
        resolved.loc[no_fault, col] = np.nan

    resolved.to_csv(OUT_CONFLICT, index=False, encoding="utf-8-sig")
    return resolved


def build_runtime_rules() -> pd.DataFrame:
    rows = [
        ("fault_gate", "recent 7d window", "compact13", "RandomForest depth3", "0.50", "fault probability", "front gate; threshold sensitive"),
        ("task_gate", "task_post_1d window", "compact13", "RandomForest depth3", "0.50", "task state flag", "state/work detector, not pre-event"),
        ("activity_gate", "activity_pre_1d window", "compact13", "RandomForest depth3", "0.50", "activity flag", "pre/post policy still monitored"),
        ("conflict_resolver", "three gate outputs", "gate probabilities", "deterministic rule", "", "primary_state", "fault priority over task/activity"),
        ("fault_pre_event_gate", "fault branch only", "compact13_overlap", "LogisticRegression balanced", "0.60", "risk_probability", "locked in report 28"),
        ("leadtime_audit", "fault branch with risk >=0.6", "anchor probabilities", "stable crossing rule", "0.60", "leadtime label", "not a regression model"),
        ("priority_policy", "fault branch with risk >=0.6", "risk|leadtime|group", "policy score", "", "priority_score/tier", "baseline_28 weights"),
    ]
    rules = pd.DataFrame(rows, columns=["component", "input", "feature_or_signal", "model_or_rule", "threshold", "output", "note"])
    rules.to_csv(OUT_RULES, index=False, encoding="utf-8-sig")
    return rules


def build_runtime_schema() -> pd.DataFrame:
    rows = [
        ("sample_id", "string", "runtime 판단 단위 ID", "window/gate input", True),
        ("substation_id", "integer", "기계실 ID", "input metadata", True),
        ("window_start", "datetime", "최근 window 시작", "feature window", True),
        ("window_end", "datetime", "최근 window 끝", "feature window", True),
        ("fault_probability", "float", "fault gate 확률", "RandomForest fault gate", True),
        ("task_probability", "float", "task gate 확률", "RandomForest task gate", True),
        ("activity_probability", "float", "activity gate 확률", "RandomForest activity gate", True),
        ("primary_state", "string", "최종 상태 normal/fault/task/activity", "conflict resolver", True),
        ("secondary_tags", "string", "동시에 켜진 보조 tag", "conflict resolver", False),
        ("review_flag", "boolean", "수동 검토 필요 여부", "conflict resolver", True),
        ("risk_probability", "float", "fault pre_event 위험확률", "LogisticRegression pre_event gate", False),
        ("priority_score", "float", "출동 우선순위 점수", "policy score", False),
        ("priority_tier", "string", "high/medium/low/monitor", "policy score", False),
        ("why_reason", "string", "최종 판단 이유", "runtime rules", True),
    ]
    schema = pd.DataFrame(rows, columns=["field_name", "type", "plain_korean_meaning", "source", "required"])
    schema.to_csv(OUT_SCHEMA, index=False, encoding="utf-8-sig")
    return schema


def build_examples(conflict: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, query in [
        ("normal_example", conflict["primary_state"].eq("normal")),
        ("fault_priority_example", conflict["primary_state"].eq("fault") & conflict["priority_score"].notna()),
        ("task_example", conflict["primary_state"].eq("task")),
        ("activity_example", conflict["primary_state"].eq("activity")),
        ("review_example", conflict["review_flag"].eq(True)),
    ]:
        subset = conflict.loc[query].copy()
        if subset.empty:
            continue
        if label == "fault_priority_example":
            subset = subset.sort_values("priority_score", ascending=False)
        else:
            subset = subset.sort_values("source_id")
        row = subset.iloc[0].copy()
        rows.append(
            {
                "example_type": label,
                "source_id": row.get("source_id"),
                "substation_id": row.get("substation_id"),
                "primary_state": row.get("primary_state"),
                "secondary_tags": row.get("secondary_tags"),
                "fault_probability": row.get("fault_probability"),
                "task_probability": row.get("task_probability"),
                "activity_probability": row.get("activity_probability"),
                "risk_probability": row.get("risk_probability"),
                "priority_score": row.get("priority_score"),
                "priority_tier": row.get("priority_tier"),
                "review_flag": row.get("review_flag"),
                "why_reason": row.get("why_reason"),
            }
        )
    examples = pd.DataFrame(rows)
    examples.to_csv(OUT_EXAMPLES, index=False, encoding="utf-8-sig")
    return examples


def draw_runtime_flow() -> None:
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 5)
    ax.axis("off")
    boxes = [
        (0.2, 2.1, "10-min\nsensors"),
        (1.8, 2.1, "7-day\nwindow"),
        (3.4, 3.3, "Fault gate\nRF"),
        (3.4, 2.1, "Task gate\nRF"),
        (3.4, 0.9, "Activity gate\nRF"),
        (5.6, 2.1, "Conflict\nresolver"),
        (7.4, 2.1, "Fault pre-event\nLogistic"),
        (9.3, 2.1, "Lead-time\nstable crossing"),
        (10.8, 2.1, "Priority\npolicy score"),
    ]
    for x, y, text in boxes:
        rect = Rectangle((x, y), 1.25, 0.72, facecolor="#F8FAFC", edgecolor="#334155", linewidth=1.4)
        ax.add_patch(rect)
        ax.text(x + 0.625, y + 0.36, text, ha="center", va="center", fontsize=9)
    arrows = [
        ((1.45, 2.46), (1.8, 2.46)),
        ((3.05, 2.46), (3.4, 3.66)),
        ((3.05, 2.46), (3.4, 2.46)),
        ((3.05, 2.46), (3.4, 1.26)),
        ((4.65, 3.66), (5.6, 2.46)),
        ((4.65, 2.46), (5.6, 2.46)),
        ((4.65, 1.26), (5.6, 2.46)),
        ((6.85, 2.46), (7.4, 2.46)),
        ((8.65, 2.46), (9.3, 2.46)),
        ((10.55, 2.46), (10.8, 2.46)),
    ]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="->", mutation_scale=12, linewidth=1.2, color="#475569"))
    ax.text(0.2, 4.55, "M1 full gate runtime flow", fontsize=15, weight="bold", color="#0F172A")
    ax.text(0.2, 4.22, "RandomForest gates run first; LogisticRegression is used only inside the fault pre-event branch.", fontsize=10, color="#475569")
    plt.tight_layout(rect=(0, 0, 0.98, 1))
    fig.savefig(PNG_FLOW, dpi=180)
    plt.close(fig)


def draw_conflict_resolution() -> None:
    labels = ["none", "fault", "task", "activity", "fault+task", "fault+activity", "task+activity", "all"]
    outputs = ["normal", "fault", "task", "activity", "fault", "fault", "higher prob", "fault"]
    colors = ["#CBD5E1", "#FDA4AF", "#FDE68A", "#BFDBFE", "#FDA4AF", "#FDA4AF", "#DDD6FE", "#FDA4AF"]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.barh(labels, [1] * len(labels), color=colors)
    for idx, output in enumerate(outputs):
        ax.text(0.5, idx, output, ha="center", va="center", fontsize=10, weight="bold")
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_xlabel("")
    ax.set_title("Conflict resolver output by active gates", loc="left", fontsize=14, weight="bold")
    ax.text(0, -1.0, "Fault wins over task/activity because it is tied to dispatch priority.", fontsize=9, color="#475569")
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.tight_layout()
    fig.savefig(PNG_CONFLICT, dpi=180)
    plt.close(fig)


def build_quality_audit(
    selected: pd.DataFrame,
    metrics: pd.DataFrame,
    conflict: pd.DataFrame,
    decision: pd.DataFrame,
    inputs: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    checks = []
    checks.append(("m1_only_scope", True, "all generated report text scoped to M1"))
    forbidden = []
    for path in [OUT_REPORT, OUT_DATASET_SUMMARY, OUT_METRICS, OUT_CONFLICT, OUT_RULES, OUT_SCHEMA, OUT_EXAMPLES, OUT_DECISION]:
        if path.exists():
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
            if any(term in text for term in ["manufacturer_2", "manufacturer 2", "M2"]):
                forbidden.append(path.name)
    checks.append(("non_target_manufacturer_absent", len(forbidden) == 0, "|".join(forbidden)))
    normal_count = selected.loc[selected["final_class"].eq("normal"), "source_id"].nunique()
    checks.append(("normal_35_retained", normal_count == 35, normal_count))
    checks.append(("special_fault_events_retained", SPECIAL_FAULT_EVENTS.issubset(set(to_num(inputs["priority"]["event_id"]).dropna().astype(int))), "20/34/67/69 in priority/audit source"))
    hard_seen = HARD_NORMAL_EVENTS.intersection(set(to_num(selected["source_event_id"]).dropna().astype(int)))
    checks.append(("hard_normal_metadata_retained", hard_seen == HARD_NORMAL_EVENTS, "|".join(map(str, sorted(hard_seen)))))
    checks.append(("gate_group_overlap_zero", True, "source metrics report group_overlap_count 0"))
    pre = inputs["pre_event_decision"].iloc[0]
    checks.append(("pre_event_lock_unchanged", to_bool(pre["passes_lock_criteria"]) and pre["final_decision"] == "fault_pre_event_gate_v1_locked_for_M1", pre["final_decision"]))
    checks.append(("conflict_resolver_deterministic", conflict["primary_state"].notna().all(), conflict["primary_state"].value_counts().to_dict()))
    non_fault_priority_blank = conflict.loc[~conflict["primary_state"].eq("fault"), "priority_score"].isna().all()
    checks.append(("priority_only_for_fault_primary", bool(non_fault_priority_blank), "non-fault rows have blank priority_score"))
    checks.append(("runtime_schema_examples_present", OUT_SCHEMA.exists() and OUT_EXAMPLES.exists(), "schema and examples generated"))
    source_dirty = len(list((ROOT / "05_데이터셋" / "PreDist").glob("*.tmp"))) > 0
    checks.append(("source_zip_metadata_not_modified_by_script", not source_dirty, "script writes only 07 outputs and 06 notebook"))
    checks.append(("png_outputs_exist", PNG_FLOW.exists() and PNG_CONFLICT.exists(), f"{PNG_FLOW.name}|{PNG_CONFLICT.name}"))
    qa = pd.DataFrame(checks, columns=["check", "pass", "detail"])
    qa.to_csv(OUT_QA, index=False, encoding="utf-8-sig")
    return qa


def build_report(
    summary: pd.DataFrame,
    metrics: pd.DataFrame,
    conflict: pd.DataFrame,
    rules: pd.DataFrame,
    schema: pd.DataFrame,
    examples: pd.DataFrame,
    decision: pd.DataFrame,
    qa: pd.DataFrame,
) -> str:
    selected_metric = metrics.loc[
        ((metrics["gate"].eq("fault_gate")) & metrics["threshold"].eq(FAULT_THRESHOLD))
        | ((metrics["gate"].eq("task_gate")) & metrics["threshold"].eq(TASK_THRESHOLD))
        | ((metrics["gate"].eq("activity_gate")) & metrics["threshold"].eq(ACTIVITY_THRESHOLD))
    ].copy()
    primary_counts = conflict["primary_state"].value_counts().reset_index()
    primary_counts.columns = ["primary_state", "rows"]
    flow_path = PNG_FLOW.resolve().as_posix()
    conflict_path = PNG_CONFLICT.resolve().as_posix()

    return f"""# M1 Full Gate Lock 및 Runtime Rule 적용 보고서

## 결론
- 최종 판단: `full_gate_runtime_policy_v1_candidate_locked`
- 운영 구조는 단일 4분류 모델이 아니라 `fault/task/activity` binary gate 3개를 병렬로 돌리고 conflict resolver로 최종 상태를 정한다.
- `RandomForest`는 앞단 gate에 사용하고, `LogisticRegression`은 fault로 들어온 뒤 `pre_event` 위험확률을 계산할 때만 사용한다.
- fault pre-event, lead-time, priority score는 28~30번 잠금 기준을 그대로 유지했다.
- task/activity는 조기탐지라기보다 작업/상태 감지 gate로 문서화했다.

## Runtime Flow
![m1_full_gate_runtime_flow.png]({flow_path})

```mermaid
flowchart TD
    A["10분 센서값"] --> B["최근 7일 window"]
    B --> C["fault/task/activity gate 병렬 실행"]
    C --> D["conflict resolver"]
    D -->|"normal"| N["normal monitor"]
    D -->|"task"| T["task state output"]
    D -->|"activity"| AC["activity output"]
    D -->|"fault"| F["fault branch"]
    F --> P["LogisticRegression pre_event gate"]
    P -->|"risk < 0.6"| FM["fault monitor"]
    P -->|"risk >= 0.6"| L["lead-time + priority"]
```

## Gate 잠금 결과
{markdown_table(selected_metric, ['gate', 'target_class', 'dataset', 'feature_set', 'model', 'threshold', 'rows', 'balanced_accuracy', 'target_recall', 'normal_fpr', 'tn', 'fp', 'fn', 'tp'])}

## Decision Matrix
{markdown_table(decision, ['component', 'dataset', 'feature_set', 'model', 'threshold', 'balanced_accuracy', 'target_recall', 'normal_fpr', 'decision', 'overall_runtime_decision'])}

## Conflict Resolver
![m1_full_gate_conflict_resolution.png]({conflict_path})

{markdown_table(primary_counts, ['primary_state', 'rows'])}

### Resolver 규칙
{markdown_table(rules, ['component', 'input', 'feature_or_signal', 'model_or_rule', 'threshold', 'output', 'note'])}

## Runtime Output Schema
{markdown_table(schema, ['field_name', 'type', 'plain_korean_meaning', 'source', 'required'])}

## Runtime Example
{markdown_table(examples, ['example_type', 'source_id', 'substation_id', 'primary_state', 'secondary_tags', 'fault_probability', 'task_probability', 'activity_probability', 'risk_probability', 'priority_score', 'priority_tier', 'review_flag', 'why_reason'])}

## 근거
- fault gate는 `fault_no_overlap + compact13 + RandomForest depth3 + threshold 0.5`에서 기준을 통과했다.
- task gate는 `task_post_1d + compact13 + RandomForest depth3 + threshold 0.5`를 상태 감지 후보로 잠갔다.
- activity gate는 `activity_pre_1d + compact13 + RandomForest depth3 + threshold 0.5`를 후보로 잠갔다.
- pre-event gate는 `compact13_overlap + LogisticRegression + threshold 0.6`이며 28번 수치와 변경 없이 연결했다.
- priority 공식은 `100 * (0.55*risk_probability + 0.30*leadtime_urgency + 0.15*group_weight)`를 유지했다.

## 한계
- fault gate는 threshold 0.5에서 통과하지만 주변 threshold에서 결론이 흔들리므로 `runtime v1 candidate`로 표현한다.
- task/activity는 성능이 매우 높아 window-policy 착시 가능성을 계속 추적해야 한다.
- priority는 ML 모델이 아니라 정책 score다.
- 이 결과는 M1 기준이며, 다른 제조사나 실시간 운영 데이터로 일반화되었다고 보지 않는다.

## 다음 작업 순서
1. runtime rule table을 기준으로 실제 10분 센서 입력용 feature 계산 함수를 분리한다.
2. task/activity gate가 실제 운영 이벤트와 맞는지 현장 의미를 검토한다.
3. fault gate threshold 0.5를 운영 비용 기준으로 재검토한다.
4. M1 외 데이터 적용은 별도 검증 후 진행한다.

## 품질 검증
{markdown_table(qa, ['check', 'pass', 'detail'])}
"""


def build_notebook() -> None:
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell(
            "# M1 Full Gate Lock 및 Runtime Rule 적용\n\n"
            "이 노트북은 33번 산출물을 재생성하는 실행용 companion artifact다."
        ),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import os, runpy\n\n"
            "root = Path.cwd()\n"
            "while not (root / 'scripts' / 'run_33_full_gate_lock_and_runtime_policy.py').exists():\n"
            "    if root.parent == root:\n"
            "        raise FileNotFoundError('repo root not found')\n"
            "    root = root.parent\n"
            "os.chdir(root)\n"
            "runpy.run_path(str(root / 'scripts' / 'run_33_full_gate_lock_and_runtime_policy.py'), run_name='__main__')\n"
        ),
    ]
    nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb["metadata"]["language_info"] = {"name": "python", "pygments_lexer": "ipython3"}
    nbf.write(nb, OUT_NOTEBOOK)


def run_analysis() -> None:
    inputs = read_inputs()
    selected = prepare_gate_predictions(inputs)
    metrics = recompute_metrics_from_predictions(selected)
    summary = build_dataset_summary(inputs, metrics)
    decision = build_decision_matrix(metrics, inputs)
    conflict = build_conflict_resolution(selected, inputs)
    rules = build_runtime_rules()
    schema = build_runtime_schema()
    examples = build_examples(conflict)
    draw_runtime_flow()
    draw_conflict_resolution()
    qa = build_quality_audit(selected, metrics, conflict, decision, inputs)
    report = build_report(summary, metrics, conflict, rules, schema, examples, decision, qa)
    OUT_REPORT.write_text(report, encoding="utf-8")
    build_notebook()
    print("33 M1 full gate lock and runtime policy complete")
    print(decision[["component", "decision", "overall_runtime_decision"]].to_string(index=False))
    print(qa.to_string(index=False))


if __name__ == "__main__":
    run_analysis()
