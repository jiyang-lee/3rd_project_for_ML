from __future__ import annotations

import subprocess
from pathlib import Path

import nbformat as nbf
import numpy as np
import pandas as pd


ROOT = Path.cwd()
LEGACY_OUT = ROOT / "07_데이터산출물"
STANDARD_OUT = ROOT / "09_실험라인" / "m1_m2_standard_pre_event" / "outputs"
LINE = ROOT / "09_실험라인" / "state_card_external_validation"
NOTEBOOK_DIR = LINE / "notebooks"
OUTPUT_DIR = LINE / "outputs"
REPORT_DIR = LINE / "reports"
SCADA_DIR = ROOT / "05_데이터셋" / "SCADA" / "XAI4HEAT"
PREDIST_DIR = ROOT / "05_데이터셋" / "PreDist"

LIGHTGBM_CANDIDATE = {"feature_set": "common13", "model": "lightgbm_depth3", "threshold": 0.5}
XGBOOST_REFERENCE = {"feature_set": "common13", "model": "xgboost_depth3", "threshold": 0.4}
LOGISTIC_REFERENCE = {"feature_set": "common13", "model": "logistic_balanced", "threshold": 0.5}


def ensure_dirs() -> None:
    for path in [NOTEBOOK_DIR, OUTPUT_DIR, REPORT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def git_status_for(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "status", "--short", "--", str(path.relative_to(ROOT))],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
        ).strip()
    except Exception as exc:
        return f"status_check_failed: {exc}"


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


def read_required() -> dict[str, pd.DataFrame]:
    paths = {
        "full_conflict": LEGACY_OUT / "m1_full_gate_conflict_resolution_audit.csv",
        "full_metrics": LEGACY_OUT / "m1_full_gate_lock_metrics.csv",
        "full_decision": LEGACY_OUT / "m1_full_gate_decision_matrix.csv",
        "full_rules": LEGACY_OUT / "m1_full_gate_runtime_rule_table.csv",
        "priority": LEGACY_OUT / "m1_fault_dispatch_priority_v1.csv",
        "leadtime_group": LEGACY_OUT / "m1_fault_group_leadtime_summary.csv",
        "leave_metrics": STANDARD_OUT / "leave_manufacturer_out_metrics.csv",
        "standard_predictions": STANDARD_OUT / "model_selection_predictions.csv",
        "xai_predictions": LEGACY_OUT / "xai4heat_scada_runtime_predictions.csv",
        "xai_schema": LEGACY_OUT / "xai4heat_scada_schema_mapping_audit.csv",
        "xai_coverage": LEGACY_OUT / "xai4heat_scada_feature_coverage_audit.csv",
        "xai_decision": LEGACY_OUT / "xai4heat_scada_runtime_validation_decision_matrix.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required input files: " + " | ".join(missing))
    return {name: pd.read_csv(path) for name, path in paths.items()}


def build_schema() -> pd.DataFrame:
    rows = [
        ("sample_id", "string", "상태카드 대상 window 또는 event ID", "runtime/window input", True),
        ("data_scope", "string", "M1 내부, M1↔M2, XAI4HEAT 중 출처 구분", "validation layer", True),
        ("substation_id", "string", "기계실 또는 외부 SCADA 파일 ID", "input metadata", True),
        ("window_start", "datetime", "센서 feature 계산 window 시작", "feature window", False),
        ("window_end", "datetime", "센서 feature 계산 window 끝", "feature window", False),
        ("primary_state", "string", "최종 상태 normal/fault/task/activity/review_required", "conflict resolver", True),
        ("secondary_tags", "string", "동시에 켜진 보조 gate 목록", "conflict resolver", False),
        ("fault_detected", "boolean", "fault gate 통과 여부", "RandomForest fault gate", True),
        ("task_detected", "boolean", "task gate 통과 여부", "RandomForest task gate", True),
        ("activity_detected", "boolean", "activity gate 통과 여부", "RandomForest activity gate", True),
        ("pre_event_detected", "string", "fault branch에서 조기탐지 gate 통과 여부 또는 불가 사유", "fault pre_event gate", True),
        ("risk_probability", "float", "fault pre_event 위험 확률", "Logistic/standard candidate", False),
        ("fault_group", "string", "고장군", "fault taxonomy", False),
        ("leadtime_label", "string", "고장군 stable crossing 리드타임 등급", "29 lead-time audit", False),
        ("priority_score", "float", "출동 우선순위 정책 점수", "30 priority policy", False),
        ("priority_tier", "string", "high/medium/low/monitor", "30 priority policy", False),
        ("review_flag", "boolean", "수동 검토 필요 여부", "resolver/metadata", True),
        ("why_reason", "string", "사람이 읽는 판정 이유", "runtime explanation", True),
        ("label_metric_available", "boolean", "이 데이터에서 성능지표 계산 가능 여부", "validation layer", True),
        ("validation_level", "string", "performance/runtime/proxy/not_available 구분", "validation layer", True),
    ]
    schema = pd.DataFrame(rows, columns=["field_name", "type", "plain_korean_meaning", "source", "required"])
    schema.to_csv(OUTPUT_DIR / "state_card_output_schema.csv", index=False, encoding="utf-8-sig")
    return schema


def build_rule_table() -> pd.DataFrame:
    rows = [
        {
            "rule_id": "R1",
            "component": "front_gates",
            "condition": "fault/task/activity gate를 병렬 적용",
            "output": "각 gate probability와 detected flag",
            "model_or_rule": "RandomForest depth3, threshold 0.5",
            "note": "task는 조기탐지가 아니라 상태/작업 감지",
        },
        {
            "rule_id": "R2",
            "component": "conflict_resolver",
            "condition": "fault와 task/activity가 동시에 켜짐",
            "output": "primary_state=fault, secondary_tags에 task/activity 보존",
            "model_or_rule": "deterministic rule",
            "note": "운영 위험도가 높은 fault 우선",
        },
        {
            "rule_id": "R3",
            "component": "conflict_resolver",
            "condition": "task와 activity만 동시에 켜짐",
            "output": "확률이 높은 쪽을 primary_state로 선택",
            "model_or_rule": "probability comparison",
            "note": "둘 다 secondary tag에도 남김",
        },
        {
            "rule_id": "R4",
            "component": "fault_pre_event",
            "condition": "primary_state=fault",
            "output": "pre_event_detected와 risk_probability",
            "model_or_rule": "pre_event model, threshold 0.6",
            "note": "fault branch에서만 계산",
        },
        {
            "rule_id": "R5",
            "component": "leadtime_priority",
            "condition": "fault이고 risk_probability >= 0.6",
            "output": "fault_group, leadtime_label, priority_score, priority_tier",
            "model_or_rule": "29 stable crossing + 30 baseline policy",
            "note": "priority는 ML 모델이 아니라 정책 점수",
        },
        {
            "rule_id": "R6",
            "component": "external_runtime",
            "condition": "외부 데이터에 라벨 또는 필수 feature가 없음",
            "output": "review_required 또는 not_available 사유 기록",
            "model_or_rule": "availability rule",
            "note": "성능점수 대신 coverage/runtime 검증",
        },
    ]
    rules = pd.DataFrame(rows)
    rules.to_csv(OUTPUT_DIR / "state_card_rule_table.csv", index=False, encoding="utf-8-sig")
    return rules


def normalize_bool(value) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes"}


def leadtime_label_from_hours(hours) -> str:
    if pd.isna(hours):
        return "not_available"
    hours = float(hours)
    if hours >= 72:
        return "early_stable"
    if hours >= 12:
        return "short_stable"
    if hours >= 0:
        return "report_time_only"
    return "unstable_or_not_detected"


def build_m1_state_cards(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    conflict = inputs["full_conflict"].copy()
    priority = inputs["priority"].copy()
    leadtime = inputs["leadtime_group"].loc[inputs["leadtime_group"]["scope"].eq("main")].copy()
    priority_small = priority[
        [
            "event_id",
            "fault_group",
            "risk_probability",
            "priority_score",
            "priority_tier",
            "stable_crossing_lead_time_hours",
        ]
    ].copy()
    leadtime_small = leadtime[["fault_group", "leadtime_label"]].drop_duplicates("fault_group")
    cards = conflict.merge(
        priority_small,
        how="left",
        left_on="fault_event_id",
        right_on="event_id",
        suffixes=("", "_priority"),
    ).merge(leadtime_small, how="left", on="fault_group")
    out = pd.DataFrame()
    out["sample_id"] = cards["source_id"].astype(str)
    out["data_scope"] = "M1_full_gate_internal"
    out["substation_id"] = cards["substation_id"].astype(str)
    out["window_start"] = cards["window_start"]
    out["window_end"] = cards["window_end"]
    out["primary_state"] = cards["primary_state"].fillna("review_required")
    out["secondary_tags"] = cards["secondary_tags"].fillna("")
    out["fault_detected"] = cards["fault_gate_on"].map(normalize_bool)
    out["task_detected"] = cards["task_gate_on"].map(normalize_bool)
    out["activity_detected"] = cards["activity_gate_on"].map(normalize_bool)
    risk = pd.to_numeric(cards["risk_probability_priority"].combine_first(cards["risk_probability"]), errors="coerce")
    out["risk_probability"] = risk
    out["pre_event_detected"] = np.where(
        out["primary_state"].eq("fault") & risk.notna(),
        np.where(risk.ge(0.6), "true", "false"),
        np.where(out["primary_state"].eq("fault"), "not_available_fault_report_unmatched", "not_applicable_not_fault"),
    )
    out["fault_group"] = cards["fault_group"].fillna("not_applicable")
    out["leadtime_label"] = cards["leadtime_label"].fillna(
        cards["stable_crossing_lead_time_hours"].map(leadtime_label_from_hours)
    )
    out["priority_score"] = pd.to_numeric(cards["priority_score"], errors="coerce")
    out["priority_tier"] = cards["priority_tier"].fillna("not_applicable")
    out["review_flag"] = cards["review_flag"].map(normalize_bool)
    out["why_reason"] = cards["why_reason"].fillna("")
    out["label_metric_available"] = True
    out["validation_level"] = "performance_validation_m1_internal"
    return out


def selected_model_rows(df: pd.DataFrame) -> pd.DataFrame:
    selectors = [LIGHTGBM_CANDIDATE, XGBOOST_REFERENCE, LOGISTIC_REFERENCE]
    parts = []
    for selector in selectors:
        part = df.loc[
            df["feature_set"].eq(selector["feature_set"])
            & df["model"].eq(selector["model"])
            & pd.to_numeric(df["threshold"], errors="coerce").eq(selector["threshold"])
        ].copy()
        parts.append(part)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def build_m1_m2_metrics(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    leave = inputs["leave_metrics"].copy()
    selected = selected_model_rows(leave)
    selected["validation_level"] = "cross_manufacturer_performance"
    selected["metric_scope_note"] = np.where(
        selected["evaluation_scope"].eq("M1_to_M2"),
        "M1으로 학습하고 M2에서 평가",
        "M2로 학습하고 M1에서 평가",
    )
    selected.to_csv(OUTPUT_DIR / "m1_m2_state_card_metrics.csv", index=False, encoding="utf-8-sig")
    return selected


def build_m1_m2_pre_event_cards(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    pred = inputs["standard_predictions"].copy()
    selector = LIGHTGBM_CANDIDATE
    pred = pred.loc[
        pred["evaluation_scope"].isin(["M1_to_M2", "M2_to_M1"])
        & pred["feature_set"].eq(selector["feature_set"])
        & pred["model"].eq(selector["model"])
    ].copy()
    pred["probability"] = pd.to_numeric(pred["probability"], errors="coerce")
    cards = pd.DataFrame()
    cards["sample_id"] = pred["sample_id"].astype(str)
    cards["data_scope"] = pred["evaluation_scope"]
    cards["substation_id"] = pred["manufacturer_substation_id"].astype(str)
    cards["window_start"] = ""
    cards["window_end"] = ""
    cards["primary_state"] = np.where(pred["probability"].ge(selector["threshold"]), "fault", "normal")
    cards["secondary_tags"] = ""
    cards["fault_detected"] = pred["probability"].ge(selector["threshold"])
    cards["task_detected"] = False
    cards["activity_detected"] = False
    cards["pre_event_detected"] = np.where(pred["probability"].ge(selector["threshold"]), "true", "false")
    cards["risk_probability"] = pred["probability"]
    cards["fault_group"] = np.where(pred["label"].eq("pre_event"), "unknown_in_cross_manufacturer_table", "not_applicable")
    cards["leadtime_label"] = "not_available_cross_manufacturer_table"
    cards["priority_score"] = np.nan
    cards["priority_tier"] = "not_available_cross_manufacturer_table"
    cards["review_flag"] = False
    cards["why_reason"] = (
        "cross-manufacturer pre_event probability from "
        + selector["model"]
        + " threshold "
        + str(selector["threshold"])
    )
    cards["label_metric_available"] = True
    cards["validation_level"] = "cross_manufacturer_pre_event_performance"
    return cards


def resolve_external_state(row: pd.Series) -> dict:
    gate_status = {gate: row.get(f"{gate}_status", "") for gate in ["fault_gate", "task_gate", "activity_gate"]}
    if any(status == "blocked_by_missing_features" for status in gate_status.values()):
        why = "required compact13 features are missing, so at least one front gate is blocked"
        return {
            "primary_state": "review_required",
            "secondary_tags": "",
            "fault_detected": False,
            "task_detected": False,
            "activity_detected": False,
            "pre_event_detected": "blocked_by_missing_features",
            "risk_probability": np.nan,
            "fault_group": "not_available_external_label_missing",
            "leadtime_label": "not_available_external_label_missing",
            "priority_score": np.nan,
            "priority_tier": "not_available_external_label_missing",
            "review_flag": True,
            "why_reason": why,
        }
    fault = normalize_bool(row.get("fault_gate_prediction", False))
    task = normalize_bool(row.get("task_gate_prediction", False))
    activity = normalize_bool(row.get("activity_gate_prediction", False))
    detected = []
    if fault:
        detected.append("fault")
    if task:
        detected.append("task")
    if activity:
        detected.append("activity")
    if fault:
        primary = "fault"
    elif task and activity:
        task_prob = row.get("task_gate_probability", 0) or 0
        activity_prob = row.get("activity_gate_probability", 0) or 0
        primary = "task" if float(task_prob) >= float(activity_prob) else "activity"
    elif task:
        primary = "task"
    elif activity:
        primary = "activity"
    else:
        primary = "normal"
    secondary = "|".join([tag for tag in detected if tag != primary])
    risk_probability = row.get("fault_pre_event_gate_probability", np.nan)
    pre_event_status = "not_applicable_not_fault"
    if fault:
        if pd.isna(risk_probability):
            pre_event_status = "not_available_external_label_missing"
        else:
            pre_event_status = "true" if float(risk_probability) >= 0.6 else "false"
    return {
        "primary_state": primary,
        "secondary_tags": secondary,
        "fault_detected": fault,
        "task_detected": task,
        "activity_detected": activity,
        "pre_event_detected": pre_event_status,
        "risk_probability": risk_probability,
        "fault_group": "not_available_external_label_missing" if fault else "not_applicable",
        "leadtime_label": "not_available_external_label_missing" if fault else "not_applicable",
        "priority_score": np.nan,
        "priority_tier": "not_available_external_label_missing" if fault else "not_applicable",
        "review_flag": False,
        "why_reason": "external runtime gate outputs resolved; no external labels available for performance scoring",
    }


def build_xai4heat_cards(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    pred = inputs["xai_predictions"].copy()
    if pred.empty:
        return pd.DataFrame()
    rows = []
    for file_name, group in pred.groupby("file"):
        pivot = {"file": file_name}
        for _, row in group.iterrows():
            gate = row["gate"]
            pivot[f"{gate}_status"] = row["runtime_status"]
            pivot[f"{gate}_probability"] = row["probability"]
            pivot[f"{gate}_prediction"] = row["prediction"]
            pivot[f"{gate}_missing_feature_count"] = row["missing_feature_count"]
        resolved = resolve_external_state(pd.Series(pivot))
        rows.append(
            {
                "sample_id": file_name,
                "data_scope": "XAI4HEAT_runtime",
                "substation_id": file_name.replace("_combined_data.csv", ""),
                "window_start": "",
                "window_end": "",
                **resolved,
                "label_metric_available": False,
                "validation_level": "external_runtime_validation_only",
            }
        )
    cards = pd.DataFrame(rows)
    cards.to_csv(OUTPUT_DIR / "xai4heat_state_card_runtime_outputs.csv", index=False, encoding="utf-8-sig")
    return cards


def build_xai4heat_audits(inputs: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    schema = inputs["xai_schema"].copy()
    coverage = inputs["xai_coverage"].copy()
    schema["state_card_relevance"] = np.where(
        schema["match_status"].isin(["direct_match", "semantic_match"]),
        "can_support_feature_mapping",
        "missing_for_required_feature",
    )
    coverage["state_card_runtime_effect"] = np.where(
        coverage["feature_available"].astype(bool),
        "available",
        "may_block_gate_or_pre_event",
    )
    schema.to_csv(OUTPUT_DIR / "xai4heat_state_card_schema_mapping_audit.csv", index=False, encoding="utf-8-sig")
    coverage.to_csv(OUTPUT_DIR / "xai4heat_state_card_coverage_audit.csv", index=False, encoding="utf-8-sig")
    return schema, coverage


def build_predictions(inputs: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    m1_cards = build_m1_state_cards(inputs)
    m1m2_cards = build_m1_m2_pre_event_cards(inputs)
    xai_cards = build_xai4heat_cards(inputs)
    m1_m2_only = pd.concat([m1_cards, m1m2_cards], ignore_index=True)
    m1_m2_only.to_csv(OUTPUT_DIR / "m1_m2_state_card_predictions.csv", index=False, encoding="utf-8-sig")
    combined = pd.concat([m1_cards, m1m2_cards, xai_cards], ignore_index=True)
    combined.to_csv(OUTPUT_DIR / "state_card_all_outputs.csv", index=False, encoding="utf-8-sig")
    return combined, m1m2_cards, xai_cards


def build_decision_matrix(
    schema: pd.DataFrame,
    metrics: pd.DataFrame,
    xai_cards: pd.DataFrame,
    xai_coverage: pd.DataFrame,
    inputs: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    full_decision = inputs["full_decision"].copy()
    full_locked = full_decision["overall_runtime_decision"].astype(str).str.contains("locked").any()
    candidate = metrics.loc[
        metrics["feature_set"].eq(LIGHTGBM_CANDIDATE["feature_set"])
        & metrics["model"].eq(LIGHTGBM_CANDIDATE["model"])
        & pd.to_numeric(metrics["threshold"], errors="coerce").eq(LIGHTGBM_CANDIDATE["threshold"])
    ]
    min_ba = float(candidate["balanced_accuracy"].min()) if len(candidate) else np.nan
    min_recall = float(candidate["recall"].min()) if len(candidate) else np.nan
    max_fpr = float(candidate["normal_fpr"].max()) if len(candidate) else np.nan
    xai_blocked = int(xai_cards["primary_state"].eq("review_required").sum()) if len(xai_cards) else 0
    xai_total = int(len(xai_cards))
    coverage_rate = float(xai_coverage["feature_available"].mean()) if len(xai_coverage) else 0.0
    final_decision = "state_card_ready_internal_cross_manufacturer_partial_external_runtime"
    rows = [
        {
            "decision_item": "state_card_schema_locked",
            "status": "pass" if schema["required"].astype(bool).sum() >= 1 else "fail",
            "evidence": f"{len(schema)} output fields",
            "final_decision": final_decision,
        },
        {
            "decision_item": "m1_full_gate_internal",
            "status": "pass" if full_locked else "fail",
            "evidence": "; ".join(full_decision["decision"].astype(str).head(5)),
            "final_decision": final_decision,
        },
        {
            "decision_item": "m1_m2_cross_manufacturer_pre_event",
            "status": "partial",
            "evidence": f"LightGBM threshold 0.5 min_BA={min_ba:.4f}, min_recall={min_recall:.4f}, max_normal_FPR={max_fpr:.4f}",
            "final_decision": final_decision,
        },
        {
            "decision_item": "xai4heat_state_card_runtime",
            "status": "blocked_by_missing_features" if xai_blocked else "pass",
            "evidence": f"{xai_blocked}/{xai_total} files review_required; feature availability={coverage_rate:.4f}",
            "final_decision": final_decision,
        },
        {
            "decision_item": "xai4heat_label_performance",
            "status": "not_applicable",
            "evidence": "XAI4HEAT has no fault/task/activity or report-date labels for this validation",
            "final_decision": final_decision,
        },
    ]
    decision = pd.DataFrame(rows)
    decision.to_csv(OUTPUT_DIR / "state_card_external_validation_decision_matrix.csv", index=False, encoding="utf-8-sig")
    return decision


def build_quality_audit(
    combined_cards: pd.DataFrame,
    metrics: pd.DataFrame,
    xai_cards: pd.DataFrame,
    xai_coverage: pd.DataFrame,
) -> pd.DataFrame:
    required = set(build_schema()["field_name"])
    output_cols = set(combined_cards.columns)
    original_status = git_status_for(PREDIST_DIR)
    scada_status = git_status_for(SCADA_DIR)
    lightgbm = metrics.loc[
        metrics["feature_set"].eq(LIGHTGBM_CANDIDATE["feature_set"])
        & metrics["model"].eq(LIGHTGBM_CANDIDATE["model"])
        & pd.to_numeric(metrics["threshold"], errors="coerce").eq(LIGHTGBM_CANDIDATE["threshold"])
    ]
    rows = [
        {
            "check": "state_card_required_columns_present",
            "pass": required.issubset(output_cols),
            "evidence": f"missing={sorted(required - output_cols)}",
        },
        {
            "check": "non_fault_no_priority_score",
            "pass": combined_cards.loc[~combined_cards["primary_state"].eq("fault"), "priority_score"].isna().all(),
            "evidence": "priority score only populated on fault branch",
        },
        {
            "check": "m1_full_gate_rows_included",
            "pass": int(combined_cards["data_scope"].eq("M1_full_gate_internal").sum()) == len(pd.read_csv(LEGACY_OUT / "m1_full_gate_conflict_resolution_audit.csv")),
            "evidence": str(int(combined_cards["data_scope"].eq("M1_full_gate_internal").sum())),
        },
        {
            "check": "m1_m2_lightgbm_holdout_rows",
            "pass": len(lightgbm) == 2,
            "evidence": f"rows={len(lightgbm)}",
        },
        {
            "check": "xai4heat_no_label_metrics",
            "pass": (not xai_cards.empty) and (xai_cards["label_metric_available"].eq(False).all()),
            "evidence": xai_cards["validation_level"].value_counts().to_dict() if not xai_cards.empty else "no rows",
        },
        {
            "check": "xai4heat_missing_features_recorded",
            "pass": len(xai_coverage) > 0 and (~xai_coverage["feature_available"].astype(bool)).any(),
            "evidence": xai_coverage["feature_available"].value_counts().to_dict() if len(xai_coverage) else "no coverage",
        },
        {
            "check": "predist_original_not_modified",
            "pass": original_status == "",
            "evidence": original_status or "clean",
        },
        {
            "check": "xai4heat_original_not_modified",
            "pass": scada_status == "",
            "evidence": scada_status or "clean",
        },
    ]
    quality = pd.DataFrame(rows)
    quality.to_csv(OUTPUT_DIR / "quality_audit.csv", index=False, encoding="utf-8-sig")
    return quality


def write_report(
    schema: pd.DataFrame,
    rules: pd.DataFrame,
    metrics: pd.DataFrame,
    combined: pd.DataFrame,
    xai_schema: pd.DataFrame,
    xai_coverage: pd.DataFrame,
    xai_cards: pd.DataFrame,
    decision: pd.DataFrame,
    quality: pd.DataFrame,
) -> None:
    candidate_metrics = metrics.loc[
        metrics["feature_set"].eq(LIGHTGBM_CANDIDATE["feature_set"])
        & metrics["model"].eq(LIGHTGBM_CANDIDATE["model"])
        & pd.to_numeric(metrics["threshold"], errors="coerce").eq(LIGHTGBM_CANDIDATE["threshold"])
    ].copy()
    status_counts = combined.groupby(["data_scope", "primary_state"], as_index=False).size()
    xai_runtime_status = xai_cards["primary_state"].value_counts().rename_axis("primary_state").reset_index(name="count") if len(xai_cards) else pd.DataFrame()
    feature_coverage = xai_coverage.groupby("feature_available", as_index=False).size().rename(columns={"size": "count"})
    report = f"""# State Card External Validation 보고서

## 결론
- 최종 출력은 단일 class가 아니라 `primary_state + secondary_tags + pre_event_detected + fault_group + leadtime_label + priority_tier + why_reason` 형태의 상태카드로 잠갔다.
- M1 내부 full gate는 기존 33번 runtime policy를 그대로 재현해 상태카드로 변환했다.
- M1↔M2 성능은 `common13 + LightGBM depth3 + threshold 0.5`를 기준 후보로 정리했다. 이는 완전 외부가 아니라 cross-manufacturer 검증이다.
- XAI4HEAT는 라벨과 report date가 없어 성능점수를 계산하지 않았다. 현재는 필수 feature 일부가 없어 상태카드가 `review_required`로 차단되는 runtime/schema 검증 결과다.

## 상태카드 스키마
{md_table(schema, ["field_name", "type", "plain_korean_meaning", "source", "required"])}

## Runtime Rule
{md_table(rules, ["rule_id", "component", "condition", "output", "model_or_rule", "note"])}

## M1↔M2 Pre-Event 성능 근거
{md_table(candidate_metrics, ["evaluation_scope", "feature_set", "model", "threshold", "rows", "normal_rows", "pre_event_rows", "balanced_accuracy", "precision", "recall", "f1", "normal_fpr", "tn", "fp", "fn", "tp"])}

## 상태카드 출력 분포
{md_table(status_counts, ["data_scope", "primary_state", "size"])}

## XAI4HEAT Runtime 검증
### Schema Mapping
{md_table(xai_schema.groupby("match_status", as_index=False).size().rename(columns={"size": "count"}), ["match_status", "count"])}

### Feature Coverage
{md_table(feature_coverage, ["feature_available", "count"])}

### Runtime State Card
{md_table(xai_runtime_status, ["primary_state", "count"]) if len(xai_runtime_status) else "runtime row 없음"}

## Decision Matrix
{md_table(decision, ["decision_item", "status", "evidence", "final_decision"])}

## 한계
- XAI4HEAT에는 fault/task/activity 라벨과 고장 report date가 없어 BA, precision, recall, f1을 계산할 수 없다.
- XAI4HEAT는 1시간 해상도이고, PreDist M1/M2는 10분 해상도 기준이라 feature 의미가 완전히 같지 않다.
- M1↔M2 검증은 제조사 간 검증이지 완전 독립 외부 현장 검증은 아니다.
- 현재 XAI4HEAT는 `p_net_meter_flow` 등 일부 required feature가 없어 front gate inference가 차단된다.

## 다음 작업 순서
1. 상태카드 출력 스키마를 joblib inference wrapper의 반환 형식으로 맞춘다.
2. 외부 현장 데이터 요청 포맷을 이 상태카드 필드 기준으로 정리한다.
3. report date가 있는 외부 district-heating fault 데이터가 확보되면 이 실험라인에 `performance_validation_external`을 추가한다.
4. XAI4HEAT 대응을 계속하려면 누락 feature 허용 모델 또는 별도 SCADA-compatible feature set을 설계한다.

## Quality Audit
{md_table(quality, ["check", "pass", "evidence"])}
"""
    (REPORT_DIR / "state_card_external_validation_보고서.md").write_text(report, encoding="utf-8")


def write_notebooks() -> None:
    output_prefix = "09_실험라인/state_card_external_validation/outputs"
    notebooks = [
        (
            "01_state_card_schema_lock.ipynb",
            "State Card Schema Lock",
            [
                f"pd.read_csv('{output_prefix}/state_card_output_schema.csv')",
                f"pd.read_csv('{output_prefix}/state_card_rule_table.csv')",
            ],
        ),
        (
            "02_m1_m2_state_card_performance_validation.ipynb",
            "M1/M2 State Card Performance Validation",
            [
                f"pd.read_csv('{output_prefix}/m1_m2_state_card_metrics.csv')",
                f"pd.read_csv('{output_prefix}/state_card_all_outputs.csv').groupby(['data_scope','primary_state']).size().reset_index(name='rows')",
            ],
        ),
        (
            "03_xai4heat_state_card_runtime_validation.ipynb",
            "XAI4HEAT State Card Runtime Validation",
            [
                f"pd.read_csv('{output_prefix}/xai4heat_state_card_schema_mapping_audit.csv').groupby('match_status').size().reset_index(name='rows')",
                f"pd.read_csv('{output_prefix}/xai4heat_state_card_runtime_outputs.csv')",
            ],
        ),
        (
            "04_state_card_external_validation_report.ipynb",
            "State Card External Validation Report",
            [
                f"pd.read_csv('{output_prefix}/state_card_external_validation_decision_matrix.csv')",
                f"pd.read_csv('{output_prefix}/quality_audit.csv')",
            ],
        ),
    ]
    for filename, title, expressions in notebooks:
        nb = nbf.v4.new_notebook()
        nb.cells = [
            nbf.v4.new_markdown_cell(f"# {title}\n\n상태카드 기반 외부 검증 산출물을 확인하는 재실행용 노트북입니다."),
            nbf.v4.new_code_cell("import pandas as pd\npd.set_option('display.max_columns', 80)"),
        ]
        for expr in expressions:
            nb.cells.append(nbf.v4.new_code_cell(expr))
        nbf.write(nb, NOTEBOOK_DIR / filename)


def main() -> None:
    ensure_dirs()
    inputs = read_required()
    schema = build_schema()
    rules = build_rule_table()
    metrics = build_m1_m2_metrics(inputs)
    combined, _, xai_cards = build_predictions(inputs)
    xai_schema, xai_coverage = build_xai4heat_audits(inputs)
    decision = build_decision_matrix(schema, metrics, xai_cards, xai_coverage, inputs)
    quality = build_quality_audit(combined, metrics, xai_cards, xai_coverage)
    write_report(schema, rules, metrics, combined, xai_schema, xai_coverage, xai_cards, decision, quality)
    write_notebooks()
    print("state card external validation complete")


if __name__ == "__main__":
    main()
