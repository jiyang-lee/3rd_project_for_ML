# Agent Output Contract

최종 agent card는 `output/agent_priority_card.csv`다.

## Key Columns

| column | meaning |
| --- | --- |
| `manufacturer` | 제조사/설비군 |
| `substation_id` | 기계실 또는 설비 ID |
| `window_start` | 분석 window 시작 시각 |
| `window_end` | 분석 window 종료 시각 |

## Anomaly Columns

| column | meaning |
| --- | --- |
| `anomaly_ensemble_score` | IsolationForest와 Mahalanobis ratio를 가중합한 이상 점수 |
| `iforest_score_ratio` | train-normal q99 기준 IsolationForest ratio |
| `mahalanobis_score_ratio` | train-normal q99 기준 Mahalanobis ratio |
| `anomaly_consensus_count` | 두 detector 중 threshold 초과 개수 |
| `anomaly_criticality` | threshold 초과 지속 누적 counter |
| `anomaly_event_label` | criticality 기준 최종 anomaly event |
| `anomaly_evidence_event_label` | agent 설명에 쓰는 active anomaly event |
| `anomaly_evidence_source` | anomaly 근거 출처 설명 |

## Risk / Leadtime Columns

| column | meaning |
| --- | --- |
| `risk_probability` | 기존 best risk 확률 |
| `risk_score` | priority에 쓰는 calibrated risk score |
| `risk_level_calibrated` | low/medium/high/critical 위험 단계 |
| `predicted_lead_time_bucket` | 0-24h, 1-3d, 3-7d 중 leadtime 참고 bucket |
| `leadtime_urgency_score` | leadtime이 가까울수록 커지는 긴급도 점수 |

## Priority Columns

| column | meaning |
| --- | --- |
| `current_best_priority_score` | 기존 best priority score |
| `current_best_priority_level` | 기존 best priority level |
| `m1_specialist_priority_score` | M1 specialist gate 기반 priority score |
| `m1_specialist_priority_level` | M1 specialist priority level |
| `m1_hybrid_priority_score` | current-best와 M1 specialist를 결합한 score |
| `m1_hybrid_priority_level` | hybrid priority level |
| `priority_score` | 최종 agent용 priority score |
| `priority_level` | 최종 agent용 priority level |
| `priority_source` | 최종 priority 생성 방식 |
| `priority_high_label` | high 이상이면 1 |

## Specialist Evidence Columns

| column | meaning |
| --- | --- |
| `m1_specialist_fault_probability` | fault gate 확률 |
| `m1_specialist_task_probability` | task gate 확률 |
| `m1_specialist_activity_probability` | activity gate 확률 |
| `m1_specialist_pre_event_probability` | pre-event logistic 확률 |
| `m1_specialist_primary_state` | specialist가 본 주요 상태 |
| `m1_specialist_secondary_tags` | 보조 상태 tag |
| `m1_specialist_fault_group` | fault group |
| `m1_specialist_group_weight` | fault group 가중치 |
| `m1_specialist_gate_review_required` | specialist gate 기준 review 필요 여부 |
| `m1_specialist_gate_review_reasons` | specialist review 사유 |

## Operational Columns

| column | meaning |
| --- | --- |
| `review_required` | 사람이 확인해야 할 사유가 있으면 True |
| `review_reasons` | review 사유 |
| `trust_level` | 모델 근거 신뢰도 단계 |
| `first_crossing_time` | 최초 alarm crossing 시점 |
| `stable_crossing_time` | 안정적으로 alarm이 유지된 시점 |
| `stable_crossing_lead_hours` | event 대비 stable crossing 선행 시간 |
| `why_reason` | agent 설명용 요약 이유 |
| `recommended_action` | 권장 조치 문장 |
