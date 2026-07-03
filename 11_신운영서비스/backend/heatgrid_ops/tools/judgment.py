from __future__ import annotations


def rule_judgment(card: dict[str, object]) -> str:
    tier = str(card.get("priority_tier", "monitor"))
    pre_event = str(card.get("pre_event_detected", "false"))
    review = bool(card.get("review_flag", False))
    if tier in {"urgent", "high"} and pre_event == "true":
        return "우선 출동 검토: 높은 우선순위와 pre-event 신호가 동시에 확인됨"
    if review:
        return "운영자 검토 필요: 모델/정책 불일치 또는 임계값 근접"
    return "모니터링 유지: 즉시 조치 조건은 아님"
