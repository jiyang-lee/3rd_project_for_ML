# Agent Handoff Guide

이 문서는 에이전트 또는 후속 통합 파이프라인이 어떤 파일과 컬럼을 사용해야 하는지 정리한다.

## 필수 전달 파일

```text
output/agent_priority_card.csv
output/agent/agent_card_value_mapping_ko.md
output/agent/agent_card_column_dictionary_ko.csv
```

## 선택 전달 파일

```text
output/agent/m1_agent_priority_card.csv
output/agent/m1_specialist_parallel_agent_card.csv
output/reports/m1_specialist_vs_current_best_comparison.csv
output/reports/final_validation_report.md
output/reports/m1_specialist_report.md
```

## 메인 값

에이전트가 설비 우선순위를 볼 때 기본으로 쓰는 값은 다음 두 컬럼이다.

```text
priority_score
priority_level
```

현재 `priority_score`는 M1 hybrid priority다.

```text
priority_score
= 0.65 * current_best_priority_score
+ 0.35 * m1_specialist_priority_score
```

즉 기존 best 계열 판단을 기본축으로 두고, M1 specialist gate 판단을 보조 근거로 섞은 값이다.

## 설명에 쓰는 주요 근거

```text
current_best_priority_score
current_best_priority_level
risk_score
risk_level_calibrated
predicted_lead_time_bucket
leadtime_urgency_score
anomaly_evidence_source
anomaly_criticality
m1_priority_agreement
m1_specialist_pre_event_probability
m1_specialist_primary_state
m1_specialist_fault_group
m1_specialist_priority_score
review_required
review_reasons
trust_level
why_reason
recommended_action
```

## 주의

- `priority_score`는 이미 최종 hybrid 값이므로 에이전트에서 다시 가중합하지 않는다.
- `current_best_priority_score`는 기존 best 판단을 설명하기 위해 보존한 값이다.
- `m1_specialist_*` 값은 M1 전용 specialist 근거이며 risk/leadtime을 대체하지 않는다.
- `predicted_lead_time_bucket`은 정확한 고장 시점 예측이 아니라 조기 위험 참고 신호다.
- `review_required == True`이면 자동 결론보다 사람이 확인해야 할 근거를 우선 표시한다.
