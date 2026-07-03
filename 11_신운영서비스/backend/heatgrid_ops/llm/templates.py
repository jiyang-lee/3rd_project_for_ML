from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionText:
    text: str
    ticket_intent: str


def top_feature_text(features: dict[str, float] | None, limit: int = 3) -> str:
    if not features:
        return "주요 피처 없음"
    ranked = sorted(features.items(), key=lambda item: abs(item[1]), reverse=True)[:limit]
    return ", ".join(f"{name}={value:.2f}" for name, value in ranked)


def fallback_action(intent: str, card: dict[str, object], evidence: list[str]) -> ActionText:
    substation_id = str(card.get("substation_id", "unknown"))
    tier = str(card.get("priority_tier", "monitor"))
    score = card.get("priority_score")
    risk = card.get("risk_probability")
    fault_group = str(card.get("fault_group", "unknown_review"))
    why = str(card.get("why_reason", "근거 없음"))
    features = card.get("features")
    feature_text = top_feature_text(features if isinstance(features, dict) else None)
    evidence_text = "\n".join(f"- {item}" for item in evidence[:5]) or "- 추가 근거 없음"

    match intent:
        case "explain_priority":
            text = (
                f"{substation_id} 우선순위 설명\n"
                f"- 등급: {tier}, 점수: {score}\n"
                f"- 위험확률: {risk}, 고장군: {fault_group}\n"
                f"- 판단 이유: {why}\n"
                f"- 주요 피처: {feature_text}\n"
                f"\n근거\n{evidence_text}"
            )
            return ActionText(text=text, ticket_intent="internal")
        case "vendor_message":
            text = (
                f"[업체 전달문] {substation_id}\n"
                f"우선순위 {tier} 카드가 생성되었습니다. 관련 구간은 {fault_group}로 분류되며 "
                f"현장 점검 전 최근 72시간 센서 추이와 밸브/열교환기 책임 구간을 확인해 주세요.\n\n"
                f"근거\n{evidence_text}"
            )
            return ActionText(text=text, ticket_intent="vendor")
        case "resident_notice":
            text = (
                f"[입주민 공지 초안] {substation_id}\n"
                "난방/급탕 설비 점검 가능성이 확인되어 사전 점검을 준비 중입니다. "
                "현재 즉시 중단 조치는 아니며, 점검 일정 확정 시 별도 안내하겠습니다."
            )
            return ActionText(text=text, ticket_intent="notice")
        case "report":
            text = (
                f"# {substation_id} 운영 보고서\n\n"
                f"## 요약\n- 등급: {tier}\n- 점수: {score}\n- 위험확률: {risk}\n- 고장군: {fault_group}\n\n"
                f"## 판단 근거\n{why}\n\n## 주요 피처\n{feature_text}\n\n## 참고 근거\n{evidence_text}\n"
            )
            return ActionText(text=text, ticket_intent="internal")
        case unreachable:
            raise RuntimeError(f"unsupported intent: {unreachable}")


def fallback_rag_answer(question: str, evidence: list[str]) -> str:
    evidence_text = "\n".join(f"- {item}" for item in evidence[:5])
    if not evidence_text:
        return (
            f"질문: {question}\n\n"
            "RAG 문서에서 직접 연결되는 근거를 찾지 못했습니다. 검색어를 더 짧게 나누어 다시 질문해 주세요."
        )
    return (
        f"질문: {question}\n\n"
        "RAG 문서에서 확인된 내용은 아래와 같습니다.\n"
        f"{evidence_text}\n\n"
        "근거 밖의 내용은 포함하지 않았습니다."
    )
