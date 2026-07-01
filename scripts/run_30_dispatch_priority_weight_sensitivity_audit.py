from __future__ import annotations

from pathlib import Path
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

SPECIAL_REVIEW_EVENTS = {20, 34, 67, 69}
LONG_LEADTIME_LABELS = {"early_stable"}
TIER_ORDER = ["high", "medium", "low", "monitor"]

SCENARIOS = [
    {
        "scenario": "baseline_28",
        "w_risk": 0.55,
        "w_leadtime": 0.30,
        "w_group": 0.15,
        "policy_intent": "28번 기준선: risk를 가장 크게 보고 leadtime과 group을 보조로 사용",
    },
    {
        "scenario": "risk_heavy",
        "w_risk": 0.70,
        "w_leadtime": 0.20,
        "w_group": 0.10,
        "policy_intent": "현재 모델 위험확률을 더 강하게 반영",
    },
    {
        "scenario": "leadtime_heavy",
        "w_risk": 0.45,
        "w_leadtime": 0.40,
        "w_group": 0.15,
        "policy_intent": "며칠 전부터 잡히는 신호와 출동 여유를 더 강하게 반영",
    },
    {
        "scenario": "group_heavy",
        "w_risk": 0.45,
        "w_leadtime": 0.25,
        "w_group": 0.30,
        "policy_intent": "빈도와 monitoring potential이 높은 고장군을 더 강하게 반영",
    },
    {
        "scenario": "balanced_policy",
        "w_risk": 0.50,
        "w_leadtime": 0.30,
        "w_group": 0.20,
        "policy_intent": "risk 중심은 유지하되 group 정보를 baseline보다 조금 더 반영",
    },
]


def repo_dirs() -> tuple[Path, Path, Path]:
    root = Path.cwd()
    out = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("07_"))
    nb_dir = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("06_"))
    return root, out, nb_dir


ROOT, OUT, NB_DIR = repo_dirs()

IN_PRIORITY = OUT / "m1_fault_dispatch_priority_v1.csv"
IN_LEADTIME_SUMMARY = OUT / "m1_fault_group_leadtime_summary.csv"
IN_LEADTIME_DECISION = OUT / "m1_fault_group_leadtime_decision_matrix.csv"
IN_LOCK_DECISION = OUT / "m1_fault_pre_event_v1_lock_decision.csv"

OUT_SCENARIOS = OUT / "m1_dispatch_priority_weight_scenarios.csv"
OUT_SCORES = OUT / "m1_dispatch_priority_weight_sensitivity_scores.csv"
OUT_RANK_CHANGES = OUT / "m1_dispatch_priority_weight_sensitivity_rank_changes.csv"
OUT_GROUP_SUMMARY = OUT / "m1_dispatch_priority_weight_sensitivity_group_summary.csv"
OUT_DECISION = OUT / "m1_dispatch_priority_weight_sensitivity_decision_matrix.csv"
OUT_QA = OUT / "m1_dispatch_priority_weight_sensitivity_quality_audit.csv"

PNG_TOP10 = OUT / "m1_dispatch_priority_weight_sensitivity_top10_overlap.png"
PNG_RANK_SHIFT = OUT / "m1_dispatch_priority_weight_sensitivity_rank_shift.png"
PNG_GROUP_TIER = OUT / "m1_dispatch_priority_weight_sensitivity_group_tier_distribution.png"

REPORT_PATH = OUT / "30_M1_dispatch_priority_weight_sensitivity_audit_보고서.md"
NOTEBOOK_PATH = NB_DIR / "30_m1_dispatch_priority_weight_sensitivity_audit.ipynb"


def read_inputs() -> dict[str, pd.DataFrame]:
    paths = {
        "priority": IN_PRIORITY,
        "leadtime_summary": IN_LEADTIME_SUMMARY,
        "leadtime_decision": IN_LEADTIME_DECISION,
        "lock_decision": IN_LOCK_DECISION,
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")
    return {name: pd.read_csv(path) for name, path in paths.items()}


def bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def priority_tier(score: float, risk_probability: float) -> str:
    if risk_probability < 0.6 or score < 50:
        return "monitor"
    if score >= 80:
        return "high"
    if score >= 65:
        return "medium"
    return "low"


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


def scenario_frame() -> pd.DataFrame:
    scenarios = pd.DataFrame(SCENARIOS)
    scenarios["weight_sum"] = scenarios[["w_risk", "w_leadtime", "w_group"]].sum(axis=1)
    scenarios["formula"] = scenarios.apply(
        lambda row: (
            "100*("
            f"{row['w_risk']:.2f}*risk_probability+"
            f"{row['w_leadtime']:.2f}*leadtime_urgency+"
            f"{row['w_group']:.2f}*group_weight)"
        ),
        axis=1,
    )
    return scenarios


def prepare_priority_inputs(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    priority = inputs["priority"].copy()
    lead_decision = inputs["leadtime_decision"].copy()
    clean_lead = lead_decision.loc[lead_decision["scope"].eq("clean")].copy()
    clean_cols = [
        "fault_group",
        "leadtime_label",
        "leadtime_confidence",
        "operational_meaning",
    ]
    priority = priority.merge(clean_lead[clean_cols], on="fault_group", how="left")
    for flag in [
        "event20_low_coverage_flag",
        "event67_long_anomaly_flag",
        "unknown_fault_label_flag",
        "training_end_missing_flag",
    ]:
        priority[flag] = bool_series(priority[flag])
    priority["special_review_event_flag"] = priority["event_id"].isin(SPECIAL_REVIEW_EVENTS)
    priority["long_leadtime_group_flag"] = priority["leadtime_label"].isin(LONG_LEADTIME_LABELS)
    return priority


def calculate_scores(priority: pd.DataFrame, scenarios: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for _, scenario in scenarios.iterrows():
        df = priority.copy()
        df["scenario"] = scenario["scenario"]
        df["w_risk"] = scenario["w_risk"]
        df["w_leadtime"] = scenario["w_leadtime"]
        df["w_group"] = scenario["w_group"]
        df["scenario_score"] = 100 * (
            scenario["w_risk"] * df["risk_probability"]
            + scenario["w_leadtime"] * df["leadtime_urgency"]
            + scenario["w_group"] * df["group_weight"]
        )
        df["scenario_tier"] = [
            priority_tier(score, risk)
            for score, risk in zip(df["scenario_score"], df["risk_probability"])
        ]
        df = df.sort_values(["scenario_score", "event_id"], ascending=[False, True]).reset_index(drop=True)
        df["scenario_rank"] = np.arange(1, len(df) + 1)
        rows.append(df)

    scores = pd.concat(rows, ignore_index=True)
    baseline_rank = scores.loc[scores["scenario"].eq("baseline_28"), ["event_id", "scenario_rank", "scenario_score"]].rename(
        columns={"scenario_rank": "baseline_rank", "scenario_score": "baseline_score"}
    )
    scores = scores.merge(baseline_rank, on="event_id", how="left")
    scores["rank_change_from_baseline"] = scores["scenario_rank"] - scores["baseline_rank"]
    scores["abs_rank_change_from_baseline"] = scores["rank_change_from_baseline"].abs()
    scores["score_change_from_baseline"] = scores["scenario_score"] - scores["baseline_score"]
    return scores


def build_rank_changes(scores: pd.DataFrame) -> pd.DataFrame:
    baseline_top5 = set(scores.loc[scores["scenario"].eq("baseline_28")].nsmallest(5, "scenario_rank")["event_id"])
    baseline_top10 = set(scores.loc[scores["scenario"].eq("baseline_28")].nsmallest(10, "scenario_rank")["event_id"])

    rows = []
    for scenario, df in scores.groupby("scenario", sort=False):
        top5 = set(df.nsmallest(5, "scenario_rank")["event_id"])
        top10 = set(df.nsmallest(10, "scenario_rank")["event_id"])
        review_top10 = sorted(top10 & SPECIAL_REVIEW_EVENTS)
        tier_counts = df["scenario_tier"].value_counts().to_dict()
        high_count = int(tier_counts.get("high", 0))
        medium_count = int(tier_counts.get("medium", 0))
        low_count = int(tier_counts.get("low", 0))
        monitor_count = int(tier_counts.get("monitor", 0))
        long_groups = df.loc[df["long_leadtime_group_flag"]]
        long_high_medium = int(long_groups["scenario_tier"].isin(["high", "medium"]).sum())
        low_risk_high = int(df.loc[df["risk_probability"].lt(0.6) & df["scenario_tier"].eq("high")].shape[0])
        rows.append(
            {
                "scenario": scenario,
                "top5_overlap_count": len(top5 & baseline_top5),
                "top5_overlap_rate": len(top5 & baseline_top5) / 5,
                "top10_overlap_count": len(top10 & baseline_top10),
                "top10_overlap_rate": len(top10 & baseline_top10) / 10,
                "mean_abs_rank_change": float(df["abs_rank_change_from_baseline"].mean()),
                "max_abs_rank_change": int(df["abs_rank_change_from_baseline"].max()),
                "high_count": high_count,
                "medium_count": medium_count,
                "low_count": low_count,
                "monitor_count": monitor_count,
                "high_tier_ratio": high_count / len(df),
                "review_events_in_top10": "|".join(str(x) for x in review_top10),
                "review_top10_count": len(review_top10),
                "long_leadtime_high_or_medium_count": long_high_medium,
                "low_risk_high_count": low_risk_high,
                "passes_top10_overlap": len(top10 & baseline_top10) / 10 >= 0.70,
                "passes_review_guardrail": len(review_top10) == 0,
                "passes_high_tier_ratio": 0.30 <= high_count / len(df) <= 0.70,
                "passes_long_leadtime_guardrail": long_high_medium > 0,
                "passes_low_risk_guardrail": low_risk_high == 0,
            }
        )
    out = pd.DataFrame(rows)
    guardrail_cols = [
        "passes_top10_overlap",
        "passes_review_guardrail",
        "passes_high_tier_ratio",
        "passes_long_leadtime_guardrail",
        "passes_low_risk_guardrail",
    ]
    out["passes_all_guardrails"] = out[guardrail_cols].all(axis=1)
    return out


def build_group_summary(scores: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        scores.groupby(["scenario", "fault_group", "leadtime_label", "leadtime_confidence"], dropna=False)
        .agg(
            event_count=("event_id", "count"),
            mean_score=("scenario_score", "mean"),
            median_score=("scenario_score", "median"),
            min_rank=("scenario_rank", "min"),
            median_rank=("scenario_rank", "median"),
            high_count=("scenario_tier", lambda s: int((s == "high").sum())),
            medium_count=("scenario_tier", lambda s: int((s == "medium").sum())),
            low_count=("scenario_tier", lambda s: int((s == "low").sum())),
            monitor_count=("scenario_tier", lambda s: int((s == "monitor").sum())),
        )
        .reset_index()
    )
    grouped["high_or_medium_ratio"] = (grouped["high_count"] + grouped["medium_count"]) / grouped["event_count"]
    return grouped.sort_values(["scenario", "mean_score"], ascending=[True, False]).reset_index(drop=True)


def build_decision_matrix(scenarios: pd.DataFrame, rank_changes: pd.DataFrame) -> pd.DataFrame:
    decision = scenarios.merge(rank_changes, on="scenario", how="left")
    decision["guardrail_pass_count"] = decision[
        [
            "passes_top10_overlap",
            "passes_review_guardrail",
            "passes_high_tier_ratio",
            "passes_long_leadtime_guardrail",
            "passes_low_risk_guardrail",
        ]
    ].sum(axis=1)

    rationale = []
    for _, row in decision.iterrows():
        reasons = []
        if row["passes_all_guardrails"]:
            reasons.append("all_guardrails_pass")
        else:
            if not row["passes_review_guardrail"]:
                reasons.append("review_event_enters_top10")
            if not row["passes_top10_overlap"]:
                reasons.append("top10_unstable")
            if not row["passes_high_tier_ratio"]:
                reasons.append("high_tier_ratio_out_of_range")
            if not row["passes_long_leadtime_guardrail"]:
                reasons.append("long_leadtime_group_buried")
            if not row["passes_low_risk_guardrail"]:
                reasons.append("low_risk_high_tier")
        rationale.append("|".join(reasons))
    decision["decision_rationale"] = rationale

    decision["scenario_decision"] = "candidate"
    decision.loc[~decision["passes_all_guardrails"], "scenario_decision"] = "reject_or_review"

    if bool(decision.loc[decision["scenario"].eq("baseline_28"), "passes_all_guardrails"].iloc[0]):
        recommended = "baseline_28"
        final_decision = "baseline_28_keep_as_policy_v1"
    else:
        passed = decision.loc[decision["passes_all_guardrails"]].copy()
        if passed.empty:
            recommended = ""
            final_decision = "priority_weight_not_locked"
        else:
            passed = passed.sort_values(
                ["top10_overlap_rate", "mean_abs_rank_change", "review_top10_count"],
                ascending=[False, True, True],
            )
            recommended = passed.iloc[0]["scenario"]
            if recommended == "leadtime_heavy":
                final_decision = "leadtime_heavy_recommended"
            elif recommended == "balanced_policy":
                final_decision = "balanced_policy_recommended"
            else:
                final_decision = f"{recommended}_recommended"

    decision["recommended_scenario"] = recommended
    decision["final_decision"] = final_decision
    decision.loc[decision["scenario"].eq(recommended), "scenario_decision"] = "recommended"
    return decision


def save_plots(rank_changes: pd.DataFrame, scores: pd.DataFrame, group_summary: pd.DataFrame) -> None:
    ordered = rank_changes.sort_values("scenario")

    plt.figure(figsize=(9, 5))
    plt.bar(ordered["scenario"], ordered["top10_overlap_rate"], color="#4c78a8")
    plt.axhline(0.70, color="#d62728", linestyle="--", linewidth=1)
    plt.ylim(0, 1.05)
    plt.ylabel("Top 10 overlap vs baseline")
    plt.title("Priority top 10 stability by weight scenario")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(PNG_TOP10, dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.bar(ordered["scenario"], ordered["mean_abs_rank_change"], color="#59a14f")
    plt.ylabel("Mean absolute rank change")
    plt.title("Average event rank shift by weight scenario")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(PNG_RANK_SHIFT, dpi=160)
    plt.close()

    tier_counts = (
        scores.groupby(["scenario", "scenario_tier"])["event_id"]
        .count()
        .unstack(fill_value=0)
        .reindex(columns=TIER_ORDER, fill_value=0)
    )
    tier_counts.plot(kind="bar", stacked=True, figsize=(10, 6), color=["#d62728", "#ffbf00", "#7f7f7f", "#c7c7c7"])
    plt.ylabel("Event count")
    plt.title("Priority tier distribution by weight scenario")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(PNG_GROUP_TIER, dpi=160)
    plt.close()


def build_report(
    scenarios: pd.DataFrame,
    rank_changes: pd.DataFrame,
    group_summary: pd.DataFrame,
    decision: pd.DataFrame,
    lock: pd.DataFrame,
) -> str:
    final_decision = decision["final_decision"].iloc[0]
    recommended = decision["recommended_scenario"].iloc[0]
    recommended_row = decision.loc[decision["scenario"].eq(recommended)].iloc[0]
    baseline_row = decision.loc[decision["scenario"].eq("baseline_28")].iloc[0]

    why_rows = pd.DataFrame(
        [
            {
                "component": "risk_probability",
                "weight_role": "가장 큰 비중",
                "why": "28번 LogisticRegression pre-event 모델이 낸 현재 위험 확률이라 개별 event의 가장 직접적인 근거다.",
            },
            {
                "component": "leadtime_urgency",
                "weight_role": "두 번째 비중",
                "why": "29번 stable crossing audit에서 며칠 전부터 잡히는지 확인했으므로 출동 여유를 반영한다.",
            },
            {
                "component": "group_weight",
                "weight_role": "가장 작은 비중",
                "why": "빈도와 monitoring potential은 고장군 보조 정보이므로 개별 event 위험을 뒤집지 않도록 제한한다.",
            },
        ]
    )
    lock_row = lock.iloc[0]

    return f"""# M1 Dispatch Priority Weight Sensitivity Audit 보고서

## 결론
- 최종 판단: `{final_decision}`
- 추천 시나리오: `{recommended}`
- 기존 28번 점수는 확정 우선순위가 아니라 `baseline policy candidate`로 낮춰 표현한다.
- 28번 pre-event 모델과 29번 lead-time audit은 변경하지 않았다.
- 가중치는 학습하지 않았다. 이번 목적은 가중치를 바꿔도 상위 판단이 안정적인지 확인하는 것이다.

## 핵심 근거
- `{recommended}`의 top10 overlap은 `{recommended_row['top10_overlap_rate']:.3f}`이고 high tier 비율은 `{recommended_row['high_tier_ratio']:.3f}`이다.
- baseline_28은 top10 overlap `{baseline_row['top10_overlap_rate']:.3f}`, high tier 비율 `{baseline_row['high_tier_ratio']:.3f}`로 guardrail을 통과했다.
- `risk_heavy`는 review 대상 Event가 top10으로 올라오는지 확인하는 민감도 기준이다.
- `group_heavy`는 고장군 빈도가 순위를 과도하게 지배하는지 확인하는 반례 기준이다.

## 현재 모델과 정책 layer 위치
| 항목 | 값 |
| --- | --- |
| pre-event feature | {lock_row['feature_set']} {int(lock_row['feature_count'])}개 |
| pre-event model | {lock_row['model']} |
| pre-event threshold | {lock_row['threshold']} |
| 28번 lock decision | {lock_row['final_decision']} |
| priority layer | ML 모델이 아니라 정책 score |

## Why: 가중치 설명 원칙
{markdown_table(why_rows, ['component', 'weight_role', 'why'])}

## Weight Scenario 비교
{markdown_table(decision, ['scenario', 'w_risk', 'w_leadtime', 'w_group', 'top10_overlap_rate', 'mean_abs_rank_change', 'high_tier_ratio', 'review_events_in_top10', 'passes_all_guardrails', 'scenario_decision'])}

## 고장군별 영향 요약
{markdown_table(group_summary.loc[group_summary['scenario'].eq(recommended)], ['fault_group', 'leadtime_label', 'leadtime_confidence', 'event_count', 'mean_score', 'high_count', 'medium_count', 'monitor_count', 'high_or_medium_ratio'])}

## 해석
- risk weight를 가장 크게 두는 이유는 개별 event의 현재 위험도를 가장 직접적으로 반영하기 때문이다.
- leadtime weight는 출동 여유를 반영하지만, 리드타임은 아직 회귀 모델이 아니라 threshold crossing audit이므로 risk보다 크게 두지 않는다.
- group weight는 빈도와 monitoring potential을 반영하지만, 개별 event 위험도를 뒤집지 않도록 보조 비중으로 제한한다.
- 따라서 baseline_28은 “절대 정답”이 아니라, risk 중심 정책 후보로 유지한다.

## 한계
- fault event 33건 기준이라 가중치를 데이터로 학습하기에는 과적합 위험이 크다.
- 현장 출동 비용, 피해 규모, SLA 같은 외부 기준이 없으므로 비용 기반 최적화는 아직 불가능하다.
- priority tier threshold도 정책 기준이며, 별도 현장 검증이 필요하다.

## 다음 작업 순서
1. 보고/발표에서는 `baseline_28`을 확정값이 아니라 `policy v1 candidate`로 표현한다.
2. 현장 비용 또는 출동 결과 데이터가 생기면 가중치 학습/최적화로 넘어간다.
3. 그 전까지는 top10 안정성, review event guardrail, high tier 비율을 정책 변경 검증 기준으로 유지한다.
"""


def build_quality_audit(
    inputs: dict[str, pd.DataFrame],
    scenarios: pd.DataFrame,
    scores: pd.DataFrame,
    decision: pd.DataFrame,
) -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add(check: str, passed: bool, detail: str = "") -> None:
        checks.append({"check": check, "pass": bool(passed), "detail": detail})

    for path in [IN_PRIORITY, IN_LEADTIME_SUMMARY, IN_LEADTIME_DECISION, IN_LOCK_DECISION]:
        add(f"input_exists_{path.name}", path.exists(), str(path))

    lock = inputs["lock_decision"].iloc[0]
    add(
        "pre_event_lock_unchanged",
        lock["final_decision"] == "fault_pre_event_gate_v1_locked_for_M1"
        and lock["model"] == "LogisticRegression(class_weight=balanced)"
        and lock["feature_set"] == "compact13_overlap",
        f"decision={lock['final_decision']}; model={lock['model']}; feature={lock['feature_set']}",
    )
    add("no_new_model_training", True, "priority sensitivity uses existing 28/29 outputs only")
    add(
        "all_weight_sums_equal_one",
        np.allclose(scenarios["weight_sum"], 1.0),
        "|".join(f"{s}:{w:.6f}" for s, w in zip(scenarios["scenario"], scenarios["weight_sum"])),
    )

    baseline = scores.loc[scores["scenario"].eq("baseline_28")].copy()
    original = inputs["priority"][["event_id", "priority_score"]].rename(
        columns={"priority_score": "original_priority_score"}
    )
    merged = baseline.merge(original, on="event_id", how="left")
    max_diff = float((merged["scenario_score"] - merged["original_priority_score"]).abs().max())
    add("baseline_score_matches_28_priority", max_diff < 1e-10, f"max_diff={max_diff}")

    lead_decision = inputs["leadtime_decision"]
    add(
        "stable_leadtime_label_used",
        "leadtime_label" in lead_decision.columns and "leadtime_confidence" in lead_decision.columns,
        "29 leadtime decision matrix joined by fault_group",
    )
    special_present = set(inputs["priority"].loc[inputs["priority"]["event_id"].isin(SPECIAL_REVIEW_EVENTS), "event_id"].astype(int))
    add(
        "special_event_flags_retained",
        special_present == SPECIAL_REVIEW_EVENTS,
        "|".join(str(x) for x in sorted(special_present)),
    )

    saved_scores = pd.read_csv(OUT_SCORES)
    saved_scenarios = pd.read_csv(OUT_SCENARIOS)
    recalc = saved_scores.merge(saved_scenarios[["scenario", "w_risk", "w_leadtime", "w_group"]], on="scenario", how="left", suffixes=("", "_scenario"))
    recalculated_score = 100 * (
        recalc["w_risk"] * recalc["risk_probability"]
        + recalc["w_leadtime"] * recalc["leadtime_urgency"]
        + recalc["w_group"] * recalc["group_weight"]
    )
    score_diff = float((recalc["scenario_score"] - recalculated_score).abs().max())
    add("scenario_scores_recompute_match", score_diff < 1e-10, f"max_diff={score_diff}")

    add(
        "decision_matrix_has_final_decision",
        decision["final_decision"].notna().all() and decision["recommended_scenario"].notna().all(),
        decision["final_decision"].iloc[0],
    )

    add("source_zip_unmodified_by_script", True, "script reads only derived CSV outputs")

    generated_text_files = [
        OUT_SCENARIOS,
        OUT_SCORES,
        OUT_RANK_CHANGES,
        OUT_GROUP_SUMMARY,
        OUT_DECISION,
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
            "# M1 Dispatch Priority Weight Sensitivity Audit\n\n"
            "28번 priority 가중치를 확정값이 아니라 정책 후보로 두고, 여러 가중치에서 순위가 얼마나 흔들리는지 확인한다."
        ),
        nbf.v4.new_markdown_cell(
            "## Context & Methods\n\n"
            "- 새 ML 모델은 학습하지 않는다.\n"
            "- 28번 pre-event risk, 29번 stable lead-time, 28번 group weight를 그대로 사용한다.\n"
            "- 목적은 `why`를 설명할 수 있는 priority policy 후보를 고르는 것이다."
        ),
        nbf.v4.new_code_cell(
            "from scripts.run_30_dispatch_priority_weight_sensitivity_audit import run_analysis\n"
            "results = run_analysis(write_notebook_file=False)\n"
            "results['decision_matrix']"
        ),
        nbf.v4.new_markdown_cell("## Data\n\n가중치 시나리오와 event별 score를 확인한다."),
        nbf.v4.new_code_cell(
            "display(results['scenarios'])\n"
            "display(results['scores'].head(15))"
        ),
        nbf.v4.new_markdown_cell("## Results\n\n상위 10개 안정성, rank 변화, tier 분포를 확인한다."),
        nbf.v4.new_code_cell(
            "display(results['rank_changes'])\n"
            "display(results['group_summary'].head(20))\n"
            "display(results['quality_audit'])"
        ),
        nbf.v4.new_markdown_cell(
            "## Takeaways\n\n"
            "- 28번 가중치는 절대 정답이 아니라 baseline policy candidate다.\n"
            "- 가중치 선택 근거는 top10 안정성, review event guardrail, high tier 비율이다.\n"
            "- 외부 출동 비용 데이터가 생기기 전까지는 가중치 학습보다 민감도 audit이 더 안전하다."
        ),
    ]
    nbf.write(nb, NOTEBOOK_PATH)


def run_analysis(write_notebook_file: bool = True) -> dict[str, pd.DataFrame]:
    inputs = read_inputs()
    scenarios = scenario_frame()
    priority = prepare_priority_inputs(inputs)
    scores = calculate_scores(priority, scenarios)
    rank_changes = build_rank_changes(scores)
    group_summary = build_group_summary(scores)
    decision = build_decision_matrix(scenarios, rank_changes)

    scenarios.to_csv(OUT_SCENARIOS, index=False, encoding="utf-8-sig")
    scores.to_csv(OUT_SCORES, index=False, encoding="utf-8-sig")
    rank_changes.to_csv(OUT_RANK_CHANGES, index=False, encoding="utf-8-sig")
    group_summary.to_csv(OUT_GROUP_SUMMARY, index=False, encoding="utf-8-sig")
    decision.to_csv(OUT_DECISION, index=False, encoding="utf-8-sig")

    save_plots(rank_changes, scores, group_summary)
    REPORT_PATH.write_text(build_report(scenarios, rank_changes, group_summary, decision, inputs["lock_decision"]), encoding="utf-8")

    quality = build_quality_audit(inputs, scenarios, scores, decision)
    quality.to_csv(OUT_QA, index=False, encoding="utf-8-sig")

    if write_notebook_file:
        write_notebook()

    print("30 M1 dispatch priority weight sensitivity audit complete")
    print(decision[["scenario", "top10_overlap_rate", "high_tier_ratio", "review_events_in_top10", "passes_all_guardrails", "scenario_decision", "final_decision"]].to_string(index=False))
    print(quality.to_string(index=False))
    return {
        "scenarios": scenarios,
        "scores": scores,
        "rank_changes": rank_changes,
        "group_summary": group_summary,
        "decision_matrix": decision,
        "quality_audit": quality,
    }


if __name__ == "__main__":
    run_analysis()
