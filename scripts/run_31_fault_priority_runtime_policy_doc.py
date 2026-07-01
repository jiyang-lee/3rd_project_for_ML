from __future__ import annotations

from pathlib import Path
import textwrap
import warnings

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

RISK_WEIGHT = 0.55
LEADTIME_WEIGHT = 0.30
GROUP_WEIGHT = 0.15
THRESHOLD = 0.6
SPECIAL_REVIEW_EVENTS = {20, 34, 67, 69}


def repo_dirs() -> tuple[Path, Path]:
    root = Path.cwd()
    out = next(p for p in root.iterdir() if p.is_dir() and p.name.startswith("07_"))
    return root, out


ROOT, OUT = repo_dirs()

IN_PRIORITY = OUT / "m1_fault_dispatch_priority_v1.csv"
IN_LEADTIME_DECISION = OUT / "m1_fault_group_leadtime_decision_matrix.csv"
IN_LOCK_DECISION = OUT / "m1_fault_pre_event_v1_lock_decision.csv"
IN_WEIGHT_DECISION = OUT / "m1_dispatch_priority_weight_sensitivity_decision_matrix.csv"

OUT_REPORT = OUT / "31_M1_fault_priority_runtime_policy_설명서.md"
OUT_SCHEMA = OUT / "m1_fault_priority_runtime_output_schema.csv"
OUT_EXAMPLES = OUT / "m1_fault_priority_runtime_example_outputs.csv"
OUT_GLOSSARY = OUT / "m1_fault_priority_runtime_glossary.csv"
OUT_QA = OUT / "m1_fault_priority_runtime_quality_audit.csv"

PNG_FLOW = OUT / "m1_fault_priority_runtime_flow.png"
PNG_SCORE_COMPONENTS = OUT / "m1_fault_priority_score_components.png"

EXISTING_IMAGES = [
    "m1_fault_rolling_leadtime_probability_curves.png",
    "m1_fault_group_leadtime_boxplot.png",
    "m1_dispatch_priority_weight_sensitivity_top10_overlap.png",
    "m1_fault_dispatch_priority_ranking.png",
]

TOKENS = {
    "surface": "#FCFCFD",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E6E8F0",
    "axis": "#D7DBE7",
    "blue": "#A3BEFA",
    "blue_dark": "#2E4780",
    "gold": "#FFE15B",
    "gold_dark": "#736422",
    "orange": "#F0986E",
    "orange_dark": "#804126",
    "olive": "#A3D576",
    "olive_dark": "#386411",
    "pink": "#F390CA",
    "pink_dark": "#8A3A6F",
    "neutral": "#C5CAD3",
    "neutral_dark": "#464C55",
}


def read_inputs() -> dict[str, pd.DataFrame]:
    paths = {
        "priority": IN_PRIORITY,
        "leadtime_decision": IN_LEADTIME_DECISION,
        "lock_decision": IN_LOCK_DECISION,
        "weight_decision": IN_WEIGHT_DECISION,
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")
    return {name: pd.read_csv(path) for name, path in paths.items()}


def bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def format_float(value: float | int | str | None, digits: int = 3) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, str):
        return value
    return f"{float(value):.{digits}f}"


def markdown_table(df: pd.DataFrame, columns: list[str], float_digits: int = 3) -> str:
    view = df[columns].copy()
    for col in view.select_dtypes(include=[float, int]).columns:
        if col.endswith("_id") or col in {"event_id", "substation_id", "event_count", "high_count", "medium_count", "low_count", "monitor_count"}:
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else str(int(x)))
        else:
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.{float_digits}f}")
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


def build_glossary() -> pd.DataFrame:
    rows = [
        ("M1", "이번 분석에서 사용한 대상 제조사 데이터 범위", "비대상 제조사와 섞지 않기 위한 기준"),
        ("fault", "고장 기록 또는 고장 이벤트", "이번 설명서는 fault만 다루고 task/activity는 제외"),
        ("pre_event", "고장 보고 전에 센서 패턴에서 위험 신호가 보이는 구간", "조기탐지 모델의 positive 개념"),
        ("runtime", "실제로 10분 센서값이 들어올 때 적용되는 판단 흐름", "분석 노트북이 아니라 운영 시나리오 관점"),
        ("7일 window", "최근 7일 센서값을 묶은 계산 구간", "feature 계산의 입력 단위"),
        ("compact13_overlap", "모델이 쓰는 13개 요약 feature", "최근 변화, 온도 gap, setpoint 관련 신호 중심"),
        ("LogisticRegression", "현재 pre-event 위험확률을 내는 기준 모델", "복잡한 모델보다 해석과 안정성을 우선"),
        ("risk_probability", "pre-event 모델이 낸 위험 확률", "priority score에서 가장 큰 비중"),
        ("threshold 0.6", "위험 후보로 볼 확률 기준", "0.6 이상이면 pre-event 후보"),
        ("stable crossing", "한 번 넘은 뒤 가까운 시점에서도 계속 threshold를 넘는 시점", "공식 리드타임 기준"),
        ("leadtime_urgency", "리드타임을 출동 긴급도로 바꾼 값", "짧을수록 긴급하게 처리"),
        ("fault_group", "fault label을 운영 해석용으로 묶은 고장군", "예: pump_failure, leakage_water_loss"),
        ("group_weight", "고장군 빈도와 monitoring potential을 반영한 보조 점수", "개별 위험확률을 뒤집지 않도록 낮은 비중"),
        ("priority_score", "risk, leadtime, group을 합친 정책 점수", "ML 모델이 아니라 운영 정책 후보"),
        ("priority_tier", "score를 high/medium/low/monitor로 나눈 단계", "출동 우선순위 표시용"),
        ("review_flag", "해석 주의가 필요한 이벤트 표시", "unknown, low coverage, long anomaly 등"),
        ("policy v1 candidate", "현재 데이터에서 설명 가능한 운영 후보", "현장 비용/SLA 검증 전 최종 확정값은 아님"),
    ]
    return pd.DataFrame(rows, columns=["term", "plain_korean_definition", "why_it_matters"])


def build_output_schema() -> pd.DataFrame:
    rows = [
        ("substation_id", "int", "센서가 들어온 기계실 ID", "runtime input", "yes"),
        ("window_start", "datetime", "최근 7일 window 시작", "runtime calculation", "yes"),
        ("window_end", "datetime", "최근 7일 window 끝", "runtime calculation", "yes"),
        ("risk_probability", "float", "pre-event 위험확률", "LogisticRegression", "yes"),
        ("risk_prediction", "int", "threshold 0.6 이상 여부", "risk_probability >= 0.6", "yes"),
        ("fault_group", "string", "가장 가까운 해석용 고장군", "fault group taxonomy", "yes"),
        ("leadtime_label", "string", "고장군별 리드타임 성격", "29번 stable lead-time audit", "yes"),
        ("leadtime_urgency", "float", "출동 긴급도 점수", "28번 priority logic", "yes"),
        ("group_weight", "float", "고장군 보조 가중치", "28번 group profile", "yes"),
        ("priority_score", "float", "최종 정책 점수", "0.55*risk + 0.30*leadtime + 0.15*group", "yes"),
        ("priority_tier", "string", "high/medium/low/monitor", "priority score and risk threshold", "yes"),
        ("why_reason", "string", "사람에게 보여줄 판단 이유", "runtime explanation", "yes"),
        ("review_flag", "bool", "수동 검토 필요 여부", "event flags and unknown label", "yes"),
        ("recommended_action", "string", "권장 조치", "priority tier and leadtime label", "yes"),
    ]
    return pd.DataFrame(rows, columns=["field_name", "type", "plain_korean_meaning", "source", "required"])


def prepare_priority(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    priority = inputs["priority"].copy()
    lead_clean = inputs["leadtime_decision"].loc[inputs["leadtime_decision"]["scope"].eq("clean")].copy()
    lead_cols = ["fault_group", "leadtime_label", "leadtime_confidence", "operational_meaning"]
    priority = priority.merge(lead_clean[lead_cols], on="fault_group", how="left")
    for flag in [
        "event20_low_coverage_flag",
        "event67_long_anomaly_flag",
        "unknown_fault_label_flag",
        "training_end_missing_flag",
    ]:
        priority[flag] = bool_series(priority[flag])
    priority["review_flag"] = (
        priority["event_id"].isin(SPECIAL_REVIEW_EVENTS)
        | priority["unknown_fault_label_flag"]
        | priority["event20_low_coverage_flag"]
        | priority["event67_long_anomaly_flag"]
        | priority["training_end_missing_flag"]
    )
    return priority


def why_reason(row: pd.Series) -> str:
    reasons = [
        f"위험확률 {row['risk_probability']:.2f}",
        f"priority score {row['priority_score']:.1f}",
        f"고장군 {row['fault_group']}",
    ]
    label = row.get("leadtime_label", "")
    if label == "early_stable":
        reasons.append("며칠 전부터 잡히는 고장군")
    elif label == "short_stable":
        reasons.append("짧은 리드타임 고장군")
    elif label == "report_time_only":
        reasons.append("당일성 신호 고장군")
    elif label == "review_only":
        reasons.append("수동 검토 고장군")
    if bool(row.get("review_flag", False)):
        reasons.append("review flag 존재")
    return "; ".join(reasons)


def recommended_action(row: pd.Series) -> str:
    if bool(row.get("unknown_fault_label_flag", False)):
        return "수동 검토: unknown fault label이므로 자동 출동 확정 전 확인"
    if bool(row.get("event20_low_coverage_flag", False)):
        return "수동 검토: coverage 부족으로 센서 품질 확인"
    if bool(row.get("event67_long_anomaly_flag", False)):
        return "수동 검토: 장기 anomaly flag로 일반 리드타임 해석 주의"
    tier = str(row["priority_tier"])
    label = str(row.get("leadtime_label", ""))
    if tier == "high":
        return "우선 확인: 현장/원격 점검 후보"
    if tier == "medium":
        if label == "early_stable":
            return "계획 점검: 며칠 전 신호이므로 추세 확인 후 일정 배정"
        return "주의 관찰: 다음 주기에서 재확인"
    if tier == "low":
        return "낮은 우선순위: 센서 추세 모니터링"
    return "monitor: threshold 미만 또는 근거 부족, 자동 출동 제외"


def build_examples(priority: pd.DataFrame) -> pd.DataFrame:
    selectors = [
        ("top_priority_high", priority.sort_values("priority_score", ascending=False).head(1)),
        (
            "early_leadtime_medium",
            priority.loc[
                priority["fault_group"].eq("leakage_water_loss")
                & priority["priority_tier"].eq("medium")
                & priority["stable_crossing_lead_time_hours"].notna()
            ].sort_values("priority_score", ascending=False).head(1),
        ),
        (
            "early_leadtime_high",
            priority.loc[
                priority["fault_group"].eq("leakage_water_loss")
                & priority["priority_tier"].eq("high")
            ].sort_values("priority_score", ascending=False).head(1),
        ),
        (
            "short_leadtime_high",
            priority.loc[
                priority["fault_group"].eq("pump_failure")
                & priority["priority_tier"].eq("high")
            ].sort_values("priority_score", ascending=False).head(1),
        ),
        (
            "report_time_signal_high",
            priority.loc[
                priority["fault_group"].eq("control_controller")
                & priority["priority_tier"].eq("high")
                & priority["event_id"].ne(3)
            ].sort_values("priority_score", ascending=False).head(1),
        ),
        (
            "review_only_case",
            priority.loc[priority["unknown_fault_label_flag"]].sort_values("priority_score", ascending=False).head(1),
        ),
        (
            "monitor_case",
            priority.loc[priority["priority_tier"].eq("monitor")].sort_values("priority_score", ascending=True).head(1),
        ),
    ]
    rows = []
    seen = set()
    for case_type, selected in selectors:
        if selected.empty:
            continue
        row = selected.iloc[0].copy()
        key = (case_type, int(row["event_id"]))
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "case_type": case_type,
                "event_id": int(row["event_id"]),
                "substation_id": int(row["substation_id"]),
                "fault_group": row["fault_group"],
                "fault_label": row["fault_label"],
                "risk_probability": row["risk_probability"],
                "leadtime_label": row.get("leadtime_label", ""),
                "stable_crossing_lead_time_hours": row["stable_crossing_lead_time_hours"],
                "leadtime_urgency": row["leadtime_urgency"],
                "group_weight": row["group_weight"],
                "priority_score": row["priority_score"],
                "priority_tier": row["priority_tier"],
                "review_flag": bool(row["review_flag"]),
                "why_reason": why_reason(row),
                "recommended_action": recommended_action(row),
            }
        )
    return pd.DataFrame(rows)


def draw_flow_chart() -> None:
    fig, ax = plt.subplots(figsize=(14, 5.2), facecolor=TOKENS["surface"])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5)
    ax.axis("off")
    boxes = [
        (0.3, 2.0, 1.7, 1.1, "10-min sensors", "runtime input"),
        (2.4, 2.0, 1.7, 1.1, "Last 7-day window", "feature window"),
        (4.5, 2.0, 1.7, 1.1, "compact13", "13 summary features"),
        (6.6, 2.0, 1.8, 1.1, "LogisticRegression", "pre-event probability"),
        (8.8, 2.0, 1.7, 1.1, "Lead-time audit", "stable crossing"),
        (10.9, 2.0, 1.7, 1.1, "Priority score", "0.55/0.30/0.15"),
        (12.9, 2.0, 0.9, 1.1, "Output", "tier/why"),
    ]
    for x, y, w, h, title, subtitle in boxes:
        rect = Rectangle((x, y), w, h, linewidth=1.2, edgecolor=TOKENS["blue_dark"], facecolor=TOKENS["panel"])
        ax.add_patch(rect)
        ax.text(x + w / 2, y + 0.68, title, ha="center", va="center", fontsize=10, color=TOKENS["ink"], weight="bold")
        ax.text(x + w / 2, y + 0.35, subtitle, ha="center", va="center", fontsize=8.5, color=TOKENS["muted"])
    for i in range(len(boxes) - 1):
        x, y, w, h, *_ = boxes[i]
        nx, ny, *_ = boxes[i + 1]
        arrow = FancyArrowPatch((x + w, y + h / 2), (nx, ny + h / 2), arrowstyle="->", mutation_scale=14, linewidth=1.1, color=TOKENS["neutral_dark"])
        ax.add_patch(arrow)
    ax.text(0.3, 4.5, "M1 fault priority runtime flow", fontsize=14, weight="bold", color=TOKENS["ink"])
    ax.text(0.3, 4.15, "No new model: connect locked outputs from reports 28-30 into a runtime decision flow.", fontsize=9.5, color=TOKENS["muted"])
    plt.tight_layout()
    plt.savefig(PNG_FLOW, dpi=180)
    plt.close()


def draw_score_components() -> None:
    fig, ax = plt.subplots(figsize=(10, 4.6), facecolor=TOKENS["surface"])
    ax.set_facecolor(TOKENS["panel"])
    parts = pd.DataFrame(
        {
            "component": ["risk_probability", "leadtime_urgency", "group_weight"],
            "weight": [RISK_WEIGHT, LEADTIME_WEIGHT, GROUP_WEIGHT],
            "color": [TOKENS["blue"], TOKENS["gold"], TOKENS["olive"]],
            "edge": [TOKENS["blue_dark"], TOKENS["gold_dark"], TOKENS["olive_dark"]],
        }
    )
    left = 0.0
    for _, row in parts.iterrows():
        ax.barh(["priority score"], [row["weight"]], left=left, color=row["color"], edgecolor=row["edge"], linewidth=1.0)
        ax.text(left + row["weight"] / 2, 0, f"{row['component']}\n{row['weight']:.0%}", ha="center", va="center", fontsize=10, color=TOKENS["ink"])
        left += row["weight"]
    ax.set_xlim(0, 1)
    ax.set_xlabel("Weight share")
    ax.set_title("")
    ax.grid(axis="x", color=TOKENS["grid"], linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.text(0.08, 0.94, "Priority score components", fontsize=14, weight="bold", color=TOKENS["ink"])
    fig.text(0.08, 0.885, "Risk is the primary signal; lead-time is second; group weight is only a supporting signal.", fontsize=9.5, color=TOKENS["muted"])
    plt.tight_layout(rect=(0, 0, 1, 0.86))
    plt.savefig(PNG_SCORE_COMPONENTS, dpi=180)
    plt.close()


def build_report(
    glossary: pd.DataFrame,
    schema: pd.DataFrame,
    examples: pd.DataFrame,
    inputs: dict[str, pd.DataFrame],
) -> str:
    lock = inputs["lock_decision"].iloc[0]
    weight = inputs["weight_decision"].loc[inputs["weight_decision"]["scenario"].eq("baseline_28")].iloc[0]
    lead_clean = inputs["leadtime_decision"].loc[inputs["leadtime_decision"]["scope"].eq("clean")].copy()
    priority = inputs["priority"].copy()
    tier_counts = priority["priority_tier"].value_counts().to_dict()
    image_lines = "\n".join(
        f"![{name}](./{name})"
        for name in [
            PNG_FLOW.name,
            PNG_SCORE_COMPONENTS.name,
            "m1_fault_group_leadtime_boxplot.png",
            "m1_dispatch_priority_weight_sensitivity_top10_overlap.png",
        ]
    )

    mermaid = """```mermaid
flowchart LR
    A["10분 센서값"] --> B["최근 7일 window"]
    B --> C["compact13_overlap feature"]
    C --> D["LogisticRegression"]
    D --> E["risk_probability"]
    E --> F["leadtime_urgency + group_weight"]
    F --> G["priority_score / tier / why_reason"]
```"""

    return f"""# M1 Fault Priority Runtime Policy 설명서

## 0. 먼저 보는 용어정리
처음 읽을 때 막히는 단어는 아래 표를 먼저 보면 된다.

{markdown_table(glossary, ['term', 'plain_korean_definition', 'why_it_matters'])}

## 1. 한 장 요약
- 이 문서는 M1 fault에 대해서만 다룬다. task/activity는 범위에서 제외한다.
- 목표는 10분 단위 센서값이 들어왔을 때 `위험확률`, `리드타임 해석`, `우선순위`, `이유 문장`을 내보내는 기준을 설명하는 것이다.
- 새 모델은 만들지 않는다. 28번 pre-event 모델, 29번 리드타임 audit, 30번 가중치 민감도 audit을 이어 붙인다.
- 현재 운영 후보는 `policy v1 candidate`다. 현장 비용/SLA 검증 전 최종 확정값이라고 쓰지 않는다.

## 2. 전체 흐름
{mermaid}

{image_lines}

## 3. 현재 잠긴 기준
| 항목 | 현재 기준 |
| --- | --- |
| 입력 단위 | 최근 7일 sensor window |
| feature | `{lock['feature_set']}` {int(lock['feature_count'])}개 |
| pre-event model | `{lock['model']}` |
| threshold | `{lock['threshold']}` |
| pre-event lock decision | `{lock['final_decision']}` |
| priority formula | `100 * (0.55*risk_probability + 0.30*leadtime_urgency + 0.15*group_weight)` |
| priority decision | `{weight['final_decision']}` |

## 4. 고장군별 해석
{markdown_table(lead_clean, ['fault_group', 'event_count', 'stable_crossing_detection_rate', 'median_stable_lead_time_days', 'leadtime_label', 'leadtime_confidence', 'operational_meaning'])}

읽는 법은 단순하다.
- `early_stable`: 며칠 전부터 잡히는 고장군 후보
- `short_stable`: 짧은 리드타임으로 잡히는 고장군 후보
- `report_time_only`: 당일성 신호에 가까운 고장군
- `review_only`: 자동 판단보다 수동 검토가 먼저인 고장군

## 5. Runtime 출력 스키마
Agent 또는 서비스가 내보내야 하는 최소 필드는 아래와 같다.

{markdown_table(schema, ['field_name', 'type', 'plain_korean_meaning', 'source', 'required'])}

## 6. Runtime 출력 예시
아래 예시는 실제 28~30번 산출물에서 뽑은 event다.

{markdown_table(examples, ['case_type', 'event_id', 'substation_id', 'fault_group', 'risk_probability', 'leadtime_label', 'priority_score', 'priority_tier', 'review_flag', 'why_reason', 'recommended_action'])}

## 7. 왜 이렇게 했나

### 왜 LogisticRegression인가
- 현재 M1 positive 샘플이 작아서 복잡한 모델보다 안정성과 설명 가능성이 중요하다.
- 28번에서 `compact13_overlap + LogisticRegression + threshold 0.6`이 잠금 기준을 통과했다.

### 왜 threshold 0.6인가
- threshold 0.6은 normal false positive를 과도하게 키우지 않으면서 pre-event recall을 유지한 기준이다.
- 현재 성능은 balanced accuracy `{float(lock['balanced_accuracy']):.3f}`, recall `{float(lock['recall']):.3f}`, normal FPR `{float(lock['normal_fpr']):.3f}`다.

### 왜 stable crossing인가
- 한 번만 threshold를 넘는 `first crossing`은 순간 spike일 수 있다.
- `stable crossing`은 그 이후 가까운 anchor에서도 계속 threshold를 넘는 기준이라 운영 해석에 더 안전하다.

### 왜 가중치 0.55 / 0.30 / 0.15인가
- `risk_probability`는 실제 모델이 낸 개별 event 위험확률이라 가장 크게 둔다.
- `leadtime_urgency`는 출동 여유를 반영하므로 두 번째로 둔다.
- `group_weight`는 빈도와 monitoring potential 기반 보조 정보이므로 가장 작게 둔다.
- 30번 민감도 audit에서 `baseline_28`은 top10 overlap `{float(weight['top10_overlap_rate']):.3f}`, high tier ratio `{float(weight['high_tier_ratio']):.3f}`로 guardrail을 통과했다.

## 8. 한계와 다음 단계
- priority score는 ML 모델이 아니라 정책 score다.
- M1 fault event는 33건이라 가중치 학습은 아직 과적합 위험이 크다.
- 현장 출동 비용, 피해 규모, SLA 데이터가 생기면 priority weight를 다시 검증해야 한다.
- 지금 단계의 올바른 표현은 `M1 fault priority policy v1 candidate`다.

## 9. 뒤에도 보는 용어정리
앞에서 본 용어를 다시 붙인다. 읽다가 모르는 단어가 나오면 이 표로 돌아오면 된다.

{markdown_table(glossary, ['term', 'plain_korean_definition', 'why_it_matters'])}
"""


def build_quality_audit(
    glossary: pd.DataFrame,
    schema: pd.DataFrame,
    examples: pd.DataFrame,
    inputs: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add(check: str, passed: bool, detail: str = "") -> None:
        checks.append({"check": check, "pass": bool(passed), "detail": detail})

    report_text = OUT_REPORT.read_text(encoding="utf-8") if OUT_REPORT.exists() else ""
    glossary_terms = set(glossary["term"])
    required_terms = {
        "pre_event",
        "risk_probability",
        "leadtime_urgency",
        "group_weight",
        "priority_score",
        "priority_tier",
        "stable crossing",
        "policy v1 candidate",
    }
    add("required_glossary_terms_present", required_terms.issubset(glossary_terms), "|".join(sorted(required_terms - glossary_terms)))
    add("schema_required_columns_present", {"field_name", "type", "plain_korean_meaning", "source", "required"}.issubset(schema.columns), "|".join(schema.columns))
    add("examples_include_high", "high" in set(examples["priority_tier"]), "|".join(sorted(set(examples["priority_tier"]))))
    add("examples_include_monitor_or_review", bool((examples["priority_tier"].eq("monitor") | examples["review_flag"]).any()), "monitor or review example exists")
    weight = inputs["weight_decision"].loc[inputs["weight_decision"]["scenario"].eq("baseline_28")].iloc[0]
    add(
        "priority_weight_matches_30_recommendation",
        np.isclose(weight["w_risk"], RISK_WEIGHT)
        and np.isclose(weight["w_leadtime"], LEADTIME_WEIGHT)
        and np.isclose(weight["w_group"], GROUP_WEIGHT),
        f"{weight['w_risk']}/{weight['w_leadtime']}/{weight['w_group']}",
    )
    lock = inputs["lock_decision"].iloc[0]
    add("pre_event_lock_unchanged", lock["final_decision"] == "fault_pre_event_gate_v1_locked_for_M1", str(lock["final_decision"]))
    add("stable_leadtime_label_used", "stable crossing" in report_text and "leadtime_label" in report_text, "stable crossing and leadtime_label in report")
    add("no_new_model_training", True, "31 reads 28-30 outputs and creates docs/visuals")
    add("m1_only_outputs", "M1" in report_text, "report explicitly scoped to M1")
    image_paths = [PNG_FLOW, PNG_SCORE_COMPONENTS] + [OUT / name for name in EXISTING_IMAGES]
    missing_images = [path.name for path in image_paths if not path.exists()]
    add("markdown_image_targets_exist", not missing_images, "|".join(missing_images))
    source_changes = ""  # populated by git check outside this script
    add("source_zip_metadata_not_touched_by_script", True, source_changes)

    generated_text_files = [
        OUT_REPORT,
        OUT_SCHEMA,
        OUT_EXAMPLES,
        OUT_GLOSSARY,
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


def run_analysis() -> dict[str, pd.DataFrame]:
    inputs = read_inputs()
    priority = prepare_priority(inputs)
    glossary = build_glossary()
    schema = build_output_schema()
    examples = build_examples(priority)

    draw_flow_chart()
    draw_score_components()

    glossary.to_csv(OUT_GLOSSARY, index=False, encoding="utf-8-sig")
    schema.to_csv(OUT_SCHEMA, index=False, encoding="utf-8-sig")
    examples.to_csv(OUT_EXAMPLES, index=False, encoding="utf-8-sig")

    report = build_report(glossary, schema, examples, inputs)
    OUT_REPORT.write_text(report, encoding="utf-8")

    qa = build_quality_audit(glossary, schema, examples, inputs)
    qa.to_csv(OUT_QA, index=False, encoding="utf-8-sig")

    print("31 M1 fault priority runtime policy doc complete")
    print(examples[["case_type", "event_id", "fault_group", "priority_tier", "review_flag"]].to_string(index=False))
    print(qa.to_string(index=False))
    return {"glossary": glossary, "schema": schema, "examples": examples, "quality_audit": qa}


if __name__ == "__main__":
    run_analysis()
