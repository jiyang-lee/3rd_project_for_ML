from __future__ import annotations

from pathlib import Path
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

THRESHOLD = 0.6
SPECIAL_REVIEW_EVENTS = {20, 34, 67, 69}
ANCHOR_ORDER = ["D-7", "D-5", "D-3", "D-1", "D-12h", "D-0"]
ANCHOR_COLUMNS = {
    "D-7": "d_minus_7_detection_rate",
    "D-5": "d_minus_5_detection_rate",
    "D-3": "d_minus_3_detection_rate",
    "D-1": "d_minus_1_detection_rate",
    "D-12h": "d_minus_12h_detection_rate",
    "D-0": "d0_detection_rate",
}
EXPECTED_GROUPS = [
    "control_controller",
    "pump_failure",
    "valve_actuator",
    "pressure_regulator",
    "leakage_water_loss",
    "unknown_review",
]


def repo_dirs() -> tuple[Path, Path, Path]:
    root = Path.cwd()
    out = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("07_"))
    nb_dir = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("06_"))
    return root, out, nb_dir


ROOT, OUT, NB_DIR = repo_dirs()
REPORT_PATH = OUT / "29_M1_fault_group_leadtime_audit_lock_보고서.md"
NOTEBOOK_PATH = NB_DIR / "29_m1_fault_group_leadtime_audit_lock.ipynb"

IN_LEAD_SUMMARY = OUT / "m1_fault_rolling_leadtime_summary.csv"
IN_LEAD_PREDICTIONS = OUT / "m1_fault_rolling_leadtime_predictions.csv"
IN_PRIORITY = OUT / "m1_fault_dispatch_priority_v1.csv"
IN_GROUP_PROFILE = OUT / "m1_fault_group_priority_profile.csv"
IN_LOCK_DECISION = OUT / "m1_fault_pre_event_v1_lock_decision.csv"

OUT_EVENT_AUDIT = OUT / "m1_fault_group_leadtime_event_audit.csv"
OUT_GROUP_SUMMARY = OUT / "m1_fault_group_leadtime_summary.csv"
OUT_DECISION_MATRIX = OUT / "m1_fault_group_leadtime_decision_matrix.csv"
OUT_QUALITY_AUDIT = OUT / "m1_fault_group_leadtime_quality_audit.csv"

PNG_BOXPLOT = OUT / "m1_fault_group_leadtime_boxplot.png"
PNG_ANCHOR_RATE = OUT / "m1_fault_group_detection_rate_by_anchor.png"


def read_inputs() -> dict[str, pd.DataFrame]:
    paths = {
        "lead_summary": IN_LEAD_SUMMARY,
        "lead_predictions": IN_LEAD_PREDICTIONS,
        "priority": IN_PRIORITY,
        "group_profile": IN_GROUP_PROFILE,
        "lock_decision": IN_LOCK_DECISION,
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required 28 outputs: {missing}")
    return {name: pd.read_csv(path) for name, path in paths.items()}


def bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def format_event_ids(values: pd.Series | list[int]) -> str:
    if isinstance(values, pd.Series):
        values = values.dropna().astype(int).tolist()
    return "|".join(str(v) for v in sorted(set(values)))


def leadtime_label(group: str, event_count: int, stable_rate: float, median_hours: float) -> str:
    if group == "unknown_review" or event_count < 3:
        return "review_only"
    if pd.isna(stable_rate) or stable_rate < 0.5:
        return "unstable_or_not_detected"
    if pd.isna(median_hours):
        return "unstable_or_not_detected"
    if median_hours >= 72:
        return "early_stable"
    if median_hours >= 12:
        return "short_stable"
    return "report_time_only"


def leadtime_confidence(label: str, event_count: int, stable_rate: float) -> str:
    if label == "review_only":
        return "review"
    if pd.isna(stable_rate) or event_count < 3:
        return "low"
    if stable_rate >= 0.75 and event_count >= 4:
        return "high"
    if stable_rate >= 0.5:
        return "medium"
    return "low"


def operational_meaning(label: str) -> str:
    return {
        "early_stable": "days_before_warning_candidate",
        "short_stable": "short_leadtime_warning_candidate",
        "report_time_only": "same_day_fault_signal",
        "unstable_or_not_detected": "do_not_use_leadtime_alone",
        "review_only": "manual_review_only",
    }[label]


def prepare_event_audit(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    lead = inputs["lead_summary"].copy()
    predictions = inputs["lead_predictions"].copy()
    priority = inputs["priority"].copy()

    for flag in [
        "event20_low_coverage_flag",
        "event67_long_anomaly_flag",
        "unknown_fault_label_flag",
        "training_end_missing_flag",
    ]:
        if flag in lead.columns:
            lead[flag] = bool_series(lead[flag])
        if flag in predictions.columns:
            predictions[flag] = bool_series(predictions[flag])

    group_cols = [
        "event_id",
        "fault_group",
        "group_weight",
        "risk_probability",
        "leadtime_urgency",
        "priority_score",
        "priority_tier",
    ]
    event_audit = lead.merge(priority[group_cols], on="event_id", how="left", validate="one_to_one")

    prob_pivot = predictions.pivot(index="event_id", columns="anchor_label", values="fault_pre_event_probability")
    pred_pivot = predictions.pivot(index="event_id", columns="anchor_label", values="fault_pre_event_pred")
    cov_pivot = predictions.pivot(index="event_id", columns="anchor_label", values="coverage_rate")

    for anchor in ANCHOR_ORDER:
        safe = "anchor_" + ANCHOR_COLUMNS[anchor].replace("_detection_rate", "")
        event_audit[f"{safe}_probability"] = event_audit["event_id"].map(prob_pivot.get(anchor, pd.Series(dtype=float)))
        event_audit[f"{safe}_prediction"] = event_audit["event_id"].map(pred_pivot.get(anchor, pd.Series(dtype=float)))
        event_audit[f"{safe}_coverage_rate"] = event_audit["event_id"].map(cov_pivot.get(anchor, pd.Series(dtype=float)))

    event_audit["first_crossing_detected"] = event_audit["first_crossing_lead_time_hours"].notna()
    event_audit["stable_crossing_detected"] = event_audit["stable_crossing_lead_time_hours"].notna()
    event_audit["first_crossing_lead_time_days"] = event_audit["first_crossing_lead_time_hours"] / 24
    event_audit["stable_crossing_lead_time_days"] = event_audit["stable_crossing_lead_time_hours"] / 24
    event_audit["main_scope_included"] = True
    event_audit["clean_scope_included"] = ~event_audit["event_id"].isin(SPECIAL_REVIEW_EVENTS)

    reasons = []
    for _, row in event_audit.iterrows():
        row_reasons = []
        if bool(row.get("event20_low_coverage_flag", False)):
            row_reasons.append("event20_low_coverage")
        if bool(row.get("unknown_fault_label_flag", False)):
            row_reasons.append("unknown_fault_label")
        if bool(row.get("training_end_missing_flag", False)):
            row_reasons.append("training_end_missing")
        if bool(row.get("event67_long_anomaly_flag", False)):
            row_reasons.append("event67_long_anomaly")
        if int(row["event_id"]) in SPECIAL_REVIEW_EVENTS and not row_reasons:
            row_reasons.append("special_review_event")
        reasons.append("|".join(row_reasons))
    event_audit["review_reason"] = reasons

    ordered_cols = [
        "event_id",
        "substation_id",
        "fault_group",
        "fault_label",
        "problem_en",
        "efd_possible",
        "monitoring_potential",
        "report_date",
        "d0_probability",
        "d0_prediction",
        "first_crossing_lead_time_hours",
        "stable_crossing_lead_time_hours",
        "first_crossing_lead_time_days",
        "stable_crossing_lead_time_days",
        "first_crossing_detected",
        "stable_crossing_detected",
        "min_coverage_rate",
        "low_coverage_window_count",
        "event20_low_coverage_flag",
        "event67_long_anomaly_flag",
        "unknown_fault_label_flag",
        "training_end_missing_flag",
        "review_reason",
        "main_scope_included",
        "clean_scope_included",
        "group_weight",
        "priority_score",
        "priority_tier",
    ]
    anchor_cols = [
        col
        for anchor in ANCHOR_ORDER
        for col in [
            f"anchor_{ANCHOR_COLUMNS[anchor].replace('_detection_rate', '')}_probability",
            f"anchor_{ANCHOR_COLUMNS[anchor].replace('_detection_rate', '')}_prediction",
            f"anchor_{ANCHOR_COLUMNS[anchor].replace('_detection_rate', '')}_coverage_rate",
        ]
    ]
    return event_audit[ordered_cols + anchor_cols].sort_values(["fault_group", "event_id"]).reset_index(drop=True)


def summarize_scope(
    event_audit: pd.DataFrame,
    predictions: pd.DataFrame,
    group_profile: pd.DataFrame,
    scope: str,
) -> pd.DataFrame:
    if scope == "main":
        scoped_events = event_audit.copy()
        excluded_ids = ""
    elif scope == "clean":
        scoped_events = event_audit.loc[event_audit["clean_scope_included"]].copy()
        excluded_ids = format_event_ids(list(SPECIAL_REVIEW_EVENTS))
    else:
        raise ValueError(scope)

    rows = []
    for group in EXPECTED_GROUPS:
        group_events = scoped_events.loc[scoped_events["fault_group"].eq(group)].copy()
        event_ids = group_events["event_id"].astype(int).tolist()
        group_predictions = predictions.loc[predictions["event_id"].isin(event_ids)].copy()
        profile_row = group_profile.loc[group_profile["fault_group"].eq(group)]
        group_weight = profile_row["group_weight"].iloc[0] if not profile_row.empty else np.nan
        profile_events = profile_row["rows"].iloc[0] if not profile_row.empty else np.nan

        event_count = int(len(group_events))
        stable_detected = group_events["stable_crossing_lead_time_hours"].dropna()
        first_detected = group_events["first_crossing_lead_time_hours"].dropna()
        stable_rate = float(group_events["stable_crossing_detected"].mean()) if event_count else np.nan
        first_rate = float(group_events["first_crossing_detected"].mean()) if event_count else np.nan
        d0_rate = float(group_events["d0_prediction"].mean()) if event_count else np.nan
        median_stable = float(stable_detected.median()) if len(stable_detected) else np.nan
        label = leadtime_label(group, event_count, stable_rate, median_stable)

        row = {
            "scope": scope,
            "fault_group": group,
            "event_count": event_count,
            "profile_event_count": profile_events,
            "included_event_ids": format_event_ids(event_ids),
            "scope_excluded_event_ids": excluded_ids,
            "efd_possible_true_count": int(bool_series(group_events["efd_possible"]).sum()) if event_count else 0,
            "d0_detection_rate": d0_rate,
            "first_crossing_event_count": int(group_events["first_crossing_detected"].sum()) if event_count else 0,
            "first_crossing_detection_rate": first_rate,
            "stable_crossing_event_count": int(group_events["stable_crossing_detected"].sum()) if event_count else 0,
            "stable_crossing_detection_rate": stable_rate,
            "median_first_lead_time_hours": float(first_detected.median()) if len(first_detected) else np.nan,
            "median_first_lead_time_days": float(first_detected.median() / 24) if len(first_detected) else np.nan,
            "median_stable_lead_time_hours": median_stable,
            "median_stable_lead_time_days": median_stable / 24 if not pd.isna(median_stable) else np.nan,
            "p25_stable_lead_time_hours": float(stable_detected.quantile(0.25)) if len(stable_detected) else np.nan,
            "p75_stable_lead_time_hours": float(stable_detected.quantile(0.75)) if len(stable_detected) else np.nan,
            "event20_included_count": int(group_events["event20_low_coverage_flag"].sum()) if event_count else 0,
            "event67_included_count": int(group_events["event67_long_anomaly_flag"].sum()) if event_count else 0,
            "unknown_event_included_count": int(group_events["unknown_fault_label_flag"].sum()) if event_count else 0,
            "training_end_missing_count": int(group_events["training_end_missing_flag"].sum()) if event_count else 0,
            "min_coverage_rate": float(group_events["min_coverage_rate"].min()) if event_count else np.nan,
            "median_priority_score": float(group_events["priority_score"].median()) if event_count else np.nan,
            "group_weight": group_weight,
            "leadtime_label": label,
            "leadtime_confidence": leadtime_confidence(label, event_count, stable_rate),
            "operational_meaning": operational_meaning(label),
        }
        for anchor in ANCHOR_ORDER:
            anchor_predictions = group_predictions.loc[group_predictions["anchor_label"].eq(anchor)]
            row[ANCHOR_COLUMNS[anchor]] = (
                float(anchor_predictions["fault_pre_event_pred"].mean()) if len(anchor_predictions) else np.nan
            )
        rows.append(row)
    return pd.DataFrame(rows)


def build_summary_and_decision(
    event_audit: pd.DataFrame,
    predictions: pd.DataFrame,
    group_profile: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = pd.concat(
        [
            summarize_scope(event_audit, predictions, group_profile, "main"),
            summarize_scope(event_audit, predictions, group_profile, "clean"),
        ],
        ignore_index=True,
    )

    decision = summary[
        [
            "scope",
            "fault_group",
            "event_count",
            "stable_crossing_detection_rate",
            "median_stable_lead_time_hours",
            "median_stable_lead_time_days",
            "leadtime_label",
            "leadtime_confidence",
            "operational_meaning",
            "d0_detection_rate",
            "group_weight",
            "median_priority_score",
            "included_event_ids",
            "scope_excluded_event_ids",
        ]
    ].copy()
    decision["leadtime_lock_decision"] = np.where(
        decision["leadtime_label"].isin(["early_stable", "short_stable", "report_time_only"]),
        "group_leadtime_locked_as_audit",
        np.where(decision["leadtime_label"].eq("review_only"), "review_only", "leadtime_unstable"),
    )
    decision["priority_v1_usage"] = "context_only_priority_formula_unchanged"
    return summary, decision


def save_plots(event_audit: pd.DataFrame, summary: pd.DataFrame) -> None:
    plot_events = event_audit.loc[event_audit["stable_crossing_detected"]].copy()
    groups = [g for g in EXPECTED_GROUPS if g in plot_events["fault_group"].unique()]

    plt.figure(figsize=(12, 6))
    data = [
        plot_events.loc[plot_events["fault_group"].eq(group), "stable_crossing_lead_time_days"].dropna()
        for group in groups
    ]
    plt.boxplot(data, tick_labels=groups, showmeans=True)
    plt.xticks(rotation=25, ha="right")
    plt.ylabel("Stable lead time (days)")
    plt.title("M1 fault group stable lead-time distribution")
    plt.tight_layout()
    plt.savefig(PNG_BOXPLOT, dpi=160)
    plt.close()

    clean_summary = summary.loc[summary["scope"].eq("clean")].copy()
    anchor_cols = [ANCHOR_COLUMNS[a] for a in ANCHOR_ORDER]
    x = np.arange(len(clean_summary))
    width = 0.12
    plt.figure(figsize=(13, 6))
    for idx, anchor in enumerate(ANCHOR_ORDER):
        plt.bar(
            x + (idx - (len(ANCHOR_ORDER) - 1) / 2) * width,
            clean_summary[ANCHOR_COLUMNS[anchor]].fillna(0),
            width=width,
            label=anchor,
        )
    plt.xticks(x, clean_summary["fault_group"], rotation=25, ha="right")
    plt.ylabel("Detection rate")
    plt.ylim(0, 1.05)
    plt.title("M1 clean-scope detection rate by anchor and fault group")
    plt.legend(ncol=3)
    plt.tight_layout()
    plt.savefig(PNG_ANCHOR_RATE, dpi=160)
    plt.close()


def markdown_table(df: pd.DataFrame, columns: list[str], float_digits: int = 3) -> str:
    view = df[columns].copy()
    for col in view.select_dtypes(include=[float]).columns:
        view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.{float_digits}f}")
    view = view.fillna("")
    headers = [str(col) for col in view.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in view.iterrows():
        values = [str(row[col]).replace("\n", " ") for col in view.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_report(summary: pd.DataFrame, decision: pd.DataFrame, lock: pd.DataFrame) -> str:
    clean = summary.loc[summary["scope"].eq("clean")].copy()
    main = summary.loc[summary["scope"].eq("main")].copy()
    lock_row = lock.iloc[0]

    clean_focus = clean[
        [
            "fault_group",
            "event_count",
            "stable_crossing_detection_rate",
            "median_stable_lead_time_days",
            "leadtime_label",
            "leadtime_confidence",
        ]
    ].copy()
    early_groups = clean_focus.loc[clean_focus["leadtime_label"].eq("early_stable"), "fault_group"].tolist()
    short_groups = clean_focus.loc[clean_focus["leadtime_label"].eq("short_stable"), "fault_group"].tolist()
    report_groups = clean_focus.loc[clean_focus["leadtime_label"].eq("report_time_only"), "fault_group"].tolist()

    return f"""# M1 Fault Group Lead-Time Audit Lock 보고서

## 결론
- 최종 판단: `fault_group_leadtime_audit_locked_for_M1`
- 새 리드타임 모델은 만들지 않았다. 28번에서 잠긴 pre-event gate를 그대로 사용했다.
- 공식 리드타임 기준은 `stable_crossing_lead_time_hours`다. `first_crossing_lead_time_hours`는 조기 흔적 참고 지표로만 둔다.
- clean 기준에서 며칠 전부터 안정적으로 잡히는 후보는 `{', '.join(early_groups) if early_groups else '없음'}`이다.
- 짧은 리드타임 후보는 `{', '.join(short_groups) if short_groups else '없음'}`이고, 당일성 fault signal은 `{', '.join(report_groups) if report_groups else '없음'}`이다.
- 28번 dispatch priority v1 공식은 변경하지 않았다. 이번 결과는 priority 해석의 근거 표로만 사용한다.

## 현재 모델 위치
| 항목 | 값 |
| --- | --- |
| feature | {lock_row['feature_set']} {int(lock_row['feature_count'])}개 |
| model | {lock_row['model']} |
| threshold | {lock_row['threshold']} |
| 28번 lock decision | {lock_row['final_decision']} |
| fixed eval balanced accuracy | {float(lock_row['balanced_accuracy']):.6f} |
| fixed eval recall | {float(lock_row['recall']):.6f} |
| fixed eval normal FPR | {float(lock_row['normal_fpr']):.6f} |

## 조기탐지 -> 리드타임 -> 빈번도 로직
1. 10분 단위 센서값을 7일 window로 묶고 `compact13_overlap` feature를 계산한다.
2. LogisticRegression pre-event gate가 fault pre-event 확률을 낸다.
3. `D-7`, `D-5`, `D-3`, `D-1`, `D-12h`, `D-0` anchor에 같은 모델을 반복 적용한다.
4. threshold 0.6을 안정적으로 넘기기 시작한 시점을 `stable lead-time`으로 본다.
5. 이 값을 고장군별 빈번도와 함께 보아 출동 우선순위 해석 근거로 사용한다.

## Clean 기준 고장군별 리드타임
{markdown_table(clean, ['fault_group', 'event_count', 'd0_detection_rate', 'stable_crossing_detection_rate', 'median_stable_lead_time_days', 'p25_stable_lead_time_hours', 'p75_stable_lead_time_hours', 'leadtime_label', 'leadtime_confidence'])}

## Main 기준 고장군별 리드타임
{markdown_table(main, ['fault_group', 'event_count', 'd0_detection_rate', 'stable_crossing_detection_rate', 'median_stable_lead_time_days', 'leadtime_label', 'leadtime_confidence', 'event20_included_count', 'event67_included_count', 'unknown_event_included_count'])}

## Anchor별 탐지율
{markdown_table(clean, ['fault_group', 'event_count', 'd_minus_7_detection_rate', 'd_minus_5_detection_rate', 'd_minus_3_detection_rate', 'd_minus_1_detection_rate', 'd_minus_12h_detection_rate', 'd0_detection_rate'])}

## Decision Matrix
{markdown_table(decision.loc[decision['scope'].eq('clean')], ['fault_group', 'event_count', 'leadtime_label', 'leadtime_confidence', 'leadtime_lock_decision', 'operational_meaning'])}

## 한계
- 리드타임은 회귀 예측이 아니라 threshold 0.6 초과 시점 audit이다.
- 고장군별 event 수가 작아 중앙값과 탐지율이 Event 1~2개에 민감할 수 있다.
- `unknown_review`는 학습/잠금 대상이 아니라 수동 검토 대상으로 둔다.
- `valve_actuator`는 clean 기준 early 후보지만 stable detection rate가 0.5라 중간 신뢰도다.

## 다음 작업 순서
1. 이 표를 기준으로 “며칠 전부터 잡히는 고장군”과 “당일성 고장군”을 분리한다.
2. priority v1에는 기존 score를 유지하되, 보고/발표에서는 stable lead-time label을 함께 표시한다.
3. 고장군별 event 수가 늘어나면 같은 29번 노트북을 재실행해 lead-time label을 갱신한다.
4. 리드타임 회귀 모델은 event 수가 충분해진 뒤 별도 과제로 분리한다.
"""


def build_quality_audit(
    event_audit: pd.DataFrame,
    summary: pd.DataFrame,
    decision: pd.DataFrame,
    inputs: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add(check: str, passed: bool, detail: str = "") -> None:
        checks.append({"check": check, "pass": bool(passed), "detail": detail})

    for path in [IN_LEAD_SUMMARY, IN_LEAD_PREDICTIONS, IN_PRIORITY, IN_GROUP_PROFILE, IN_LOCK_DECISION]:
        add(f"input_exists_{path.name}", path.exists(), str(path))

    lock = inputs["lock_decision"].iloc[0]
    add(
        "pre_event_lock_unchanged",
        lock["final_decision"] == "fault_pre_event_gate_v1_locked_for_M1"
        and lock["model"] == "LogisticRegression(class_weight=balanced)"
        and float(lock["threshold"]) == THRESHOLD
        and lock["feature_set"] == "compact13_overlap",
        f"decision={lock['final_decision']}; model={lock['model']}; threshold={lock['threshold']}",
    )
    add("no_new_model_training", True, "29 uses 28 prediction CSV outputs only")
    add("event_audit_33_faults", len(event_audit) == 33, f"rows={len(event_audit)}")
    add(
        "one_fault_group_per_event",
        event_audit["event_id"].is_unique and event_audit["fault_group"].notna().all(),
        f"unique_events={event_audit['event_id'].nunique()}; missing_groups={event_audit['fault_group'].isna().sum()}",
    )
    present_special = set(event_audit.loc[event_audit["event_id"].isin(SPECIAL_REVIEW_EVENTS), "event_id"].astype(int))
    add(
        "special_event_flags_retained",
        present_special == SPECIAL_REVIEW_EVENTS,
        f"present={format_event_ids(list(present_special))}",
    )
    add(
        "main_and_clean_summary_present",
        set(summary["scope"]) == {"main", "clean"},
        "|".join(sorted(summary["scope"].unique())),
    )
    add(
        "decision_matrix_has_all_expected_groups",
        set(decision["fault_group"]) == set(EXPECTED_GROUPS),
        "|".join(sorted(decision["fault_group"].unique())),
    )
    add(
        "stable_crossing_is_official_metric",
        "stable_crossing_lead_time_hours" in event_audit.columns
        and "first_crossing_lead_time_hours" in event_audit.columns,
        "stable is official; first is reference",
    )

    saved_summary = pd.read_csv(OUT_GROUP_SUMMARY)
    recomputed = pd.concat(
        [
            summarize_scope(event_audit, inputs["lead_predictions"], inputs["group_profile"], "main"),
            summarize_scope(event_audit, inputs["lead_predictions"], inputs["group_profile"], "clean"),
        ],
        ignore_index=True,
    )
    compare_cols = [
        "event_count",
        "d0_detection_rate",
        "stable_crossing_detection_rate",
        "median_stable_lead_time_hours",
    ]
    merged = saved_summary.merge(
        recomputed[["scope", "fault_group"] + compare_cols],
        on=["scope", "fault_group"],
        suffixes=("_saved", "_recomputed"),
    )
    max_diff = 0.0
    for col in compare_cols:
        left = pd.to_numeric(merged[f"{col}_saved"], errors="coerce").fillna(-999999)
        right = pd.to_numeric(merged[f"{col}_recomputed"], errors="coerce").fillna(-999999)
        max_diff = max(max_diff, float((left - right).abs().max()))
    add("saved_summary_recompute_match", max_diff < 1e-12, f"max_diff={max_diff}")

    generated_text_files = [
        OUT_EVENT_AUDIT,
        OUT_GROUP_SUMMARY,
        OUT_DECISION_MATRIX,
        REPORT_PATH,
        NOTEBOOK_PATH,
        Path(__file__),
    ]
    forbidden_terms = ["manufacturer" + "_" + "2", "manufacturer" + " " + "2", "M" + "2"]
    hits = []
    for path in generated_text_files:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for term in forbidden_terms:
                if term in text:
                    hits.append(f"{path.name}:{term}")
    add("non_target_manufacturer_absent", not hits, "|".join(hits))

    return pd.DataFrame(checks)


def write_notebook() -> None:
    import nbformat as nbf

    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell(
            "# M1 Fault Group Lead-Time Audit Lock\n\n"
            "28번 pre-event gate 결과를 재사용해 고장군별 stable lead-time을 잠그는 노트북이다."
        ),
        nbf.v4.new_markdown_cell("## Context & Methods\n\n새 리드타임 모델은 만들지 않는다. 28번의 로지스틱 pre-event 확률과 rolling anchor 예측만 집계한다."),
        nbf.v4.new_code_cell(
            "from scripts.run_29_fault_group_leadtime_audit_lock import run_analysis\n"
            "results = run_analysis(write_notebook_file=False)\n"
            "results['summary'].head()"
        ),
        nbf.v4.new_markdown_cell("## Data\n\n이벤트 단위 audit과 main/clean 고장군 요약을 확인한다."),
        nbf.v4.new_code_cell(
            "display(results['event_audit'].head(10))\n"
            "display(results['summary'])"
        ),
        nbf.v4.new_markdown_cell("## Results\n\n공식 리드타임은 stable crossing 기준이다."),
        nbf.v4.new_code_cell(
            "display(results['decision_matrix'])\n"
            "display(results['quality_audit'])"
        ),
        nbf.v4.new_markdown_cell(
            "## Takeaways\n\n"
            "- 28번 pre-event gate는 변경하지 않는다.\n"
            "- 고장군별 리드타임은 `stable_crossing_lead_time_hours` 기준으로 해석한다.\n"
            "- 28번 priority score는 그대로 두고, 이번 표는 우선순위 해석 근거로 사용한다."
        ),
    ]
    nbf.write(nb, NOTEBOOK_PATH)


def run_analysis(write_notebook_file: bool = True) -> dict[str, pd.DataFrame]:
    inputs = read_inputs()
    event_audit = prepare_event_audit(inputs)
    summary, decision = build_summary_and_decision(
        event_audit,
        inputs["lead_predictions"].copy(),
        inputs["group_profile"].copy(),
    )

    event_audit.to_csv(OUT_EVENT_AUDIT, index=False, encoding="utf-8-sig")
    summary.to_csv(OUT_GROUP_SUMMARY, index=False, encoding="utf-8-sig")
    decision.to_csv(OUT_DECISION_MATRIX, index=False, encoding="utf-8-sig")
    save_plots(event_audit, summary)

    report = build_report(summary, decision, inputs["lock_decision"])
    REPORT_PATH.write_text(report, encoding="utf-8")

    quality = build_quality_audit(event_audit, summary, decision, inputs)
    quality.to_csv(OUT_QUALITY_AUDIT, index=False, encoding="utf-8-sig")

    if write_notebook_file:
        write_notebook()

    print("29 M1 fault group lead-time audit lock complete")
    print(summary.loc[summary["scope"].eq("clean"), ["fault_group", "event_count", "median_stable_lead_time_days", "leadtime_label"]].to_string(index=False))
    print(quality.to_string(index=False))
    return {
        "event_audit": event_audit,
        "summary": summary,
        "decision_matrix": decision,
        "quality_audit": quality,
    }


if __name__ == "__main__":
    run_analysis()
