"""한국어 프롬프트 템플릿."""

ANALYZE_PROMPT = """당신은 지역난방 기계실 예지보전 분석가다. 아래 상태카드를 보고 이 기계실에서
무엇이 이상한지 2~3문장의 한국어로 설명하라. 과장하지 말고 확률 수치를 근거로 서술하라.
fault_group은 리플레이 시나리오 메타데이터 기반이므로 '시나리오상'이라는 표현을 사용하라.

상태카드:
- 기계실: {substation_id}
- 판정: {primary_state} (사유: {why_reason})
- fault gate 확률: {fault_probability:.3f}
- pre-event 위험 확률: {risk_probability}
- 시나리오 고장군: {fault_group}
- 우선순위: {priority_tier} (점수 {priority_score})
- 주요 피처 변화: {top_features}

설명:"""

DISPATCH_PROMPT = """당신은 지역난방 운영센터의 출동 지시서 작성자다. 아래 정보로 한국어 작업지시서
초안을 markdown으로 작성하라. 섹션: ## 제목, **대상 기계실**, **위험 요약**, **권장 조치**,
**점검 항목** (체크리스트 4~6개), **판단 근거**. 시나리오 메타데이터 기반 고장군임을 근거 섹션에 명시하라.

정보:
- 기계실: {substation_id}
- 시나리오 고장군: {fault_group}
- 위험 확률: {risk_probability}
- 우선순위: {priority_tier} (점수 {priority_score})
- 리드타임 등급: {leadtime_label}
- 분석 요약: {analysis}

작업지시서:"""

FALLBACK_ACTION = {
    "pump_failure": "순환펌프 상태(진동/소음/전류) 점검 및 예비펌프 전환 준비",
    "control_controller": "제어기 파라미터/설정값 확인 및 제어반 점검",
    "valve_actuator": "전동밸브 액추에이터 동작시험 및 스트로크 확인",
    "pressure_regulator": "차압조절기 설정압/작동상태 점검",
    "leakage_water_loss": "누수 의심 구간 육안점검 및 보충수량 추이 확인",
    "unknown_review": "현장 종합점검 (고장군 미상 — 수동 검토 필요)",
    "other_review": "현장 종합점검 (분류 외 고장군 — 수동 검토 필요)",
}


def fallback_analysis(card: dict) -> str:
    risk = card.get("risk_probability")
    risk_txt = f"{risk:.2f}" if risk is not None else "N/A"
    return (
        f"{card['substation_id']} 기계실에서 fault gate 확률 {card.get('fault_probability', 0):.2f}, "
        f"pre-event 위험 확률 {risk_txt}로 조기경보 기준(0.6)을 초과했다. "
        f"시나리오상 고장군은 {card.get('fault_group', 'unknown')}이며 판정 사유: {card.get('why_reason', '')}."
    )


def fallback_dispatch(card: dict, analysis: str) -> tuple[str, str]:
    group = card.get("fault_group", "unknown_review")
    action = FALLBACK_ACTION.get(group, FALLBACK_ACTION["unknown_review"])
    risk = card.get("risk_probability")
    risk_txt = f"{risk:.2f}" if risk is not None else "N/A"
    score = card.get("priority_score")
    score_txt = f"{score:.1f}" if score is not None else "N/A"
    title = f"[{card.get('priority_tier', 'N/A')}] {card['substation_id']} 사전점검 출동"
    body = f"""## {title}

**대상 기계실**: {card['substation_id']}

**위험 요약**: pre-event 위험 확률 {risk_txt} (임계 0.6 초과), 우선순위 점수 {score_txt}

**권장 조치**: {action}

**점검 항목**
- [ ] 공급/환수 온도 추이 확인
- [ ] 유량/열량 미터 판독치 비교
- [ ] 해당 설비({group}) 중점 점검
- [ ] 이상 소음/진동/누수 여부 확인

**판단 근거**
{analysis}

_고장군 분류는 리플레이 시나리오 메타데이터 기반이며 모델 예측이 아님. 본 지시서는 템플릿 폴백으로 생성됨._
"""
    return title, body
