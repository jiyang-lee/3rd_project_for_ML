# M1 Dispatch Priority Weight Sensitivity Audit 보고서

## 결론
- 최종 판단: `baseline_28_keep_as_policy_v1`
- 추천 시나리오: `baseline_28`
- 기존 28번 점수는 확정 우선순위가 아니라 `baseline policy candidate`로 낮춰 표현한다.
- 28번 pre-event 모델과 29번 lead-time audit은 변경하지 않았다.
- 가중치는 학습하지 않았다. 이번 목적은 가중치를 바꿔도 상위 판단이 안정적인지 확인하는 것이다.

## 핵심 근거
- `baseline_28`의 top10 overlap은 `1.000`이고 high tier 비율은 `0.636`이다.
- baseline_28은 top10 overlap `1.000`, high tier 비율 `0.636`로 guardrail을 통과했다.
- `risk_heavy`는 review 대상 Event가 top10으로 올라오는지 확인하는 민감도 기준이다.
- `group_heavy`는 고장군 빈도가 순위를 과도하게 지배하는지 확인하는 반례 기준이다.

## 현재 모델과 정책 layer 위치
| 항목 | 값 |
| --- | --- |
| pre-event feature | compact13_overlap 13개 |
| pre-event model | LogisticRegression(class_weight=balanced) |
| pre-event threshold | 0.6 |
| 28번 lock decision | fault_pre_event_gate_v1_locked_for_M1 |
| priority layer | ML 모델이 아니라 정책 score |

## Why: 가중치 설명 원칙
| component | weight_role | why |
| --- | --- | --- |
| risk_probability | 가장 큰 비중 | 28번 LogisticRegression pre-event 모델이 낸 현재 위험 확률이라 개별 event의 가장 직접적인 근거다. |
| leadtime_urgency | 두 번째 비중 | 29번 stable crossing audit에서 며칠 전부터 잡히는지 확인했으므로 출동 여유를 반영한다. |
| group_weight | 가장 작은 비중 | 빈도와 monitoring potential은 고장군 보조 정보이므로 개별 event 위험을 뒤집지 않도록 제한한다. |

## Weight Scenario 비교
| scenario | w_risk | w_leadtime | w_group | top10_overlap_rate | mean_abs_rank_change | high_tier_ratio | review_events_in_top10 | passes_all_guardrails | scenario_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_28 | 0.550 | 0.300 | 0.150 | 1.000 | 0.000 | 0.636 |  | True | recommended |
| risk_heavy | 0.700 | 0.200 | 0.100 | 0.700 | 2.242 | 0.697 | 67 | False | reject_or_review |
| leadtime_heavy | 0.450 | 0.400 | 0.150 | 1.000 | 0.667 | 0.667 |  | True | candidate |
| group_heavy | 0.450 | 0.250 | 0.300 | 0.700 | 2.182 | 0.545 |  | True | candidate |
| balanced_policy | 0.500 | 0.300 | 0.200 | 1.000 | 1.030 | 0.636 |  | True | candidate |

## 고장군별 영향 요약
| fault_group | leadtime_label | leadtime_confidence | event_count | mean_score | high_count | medium_count | monitor_count | high_or_medium_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pressure_regulator | report_time_only | high | 4 | 90.382 | 4 | 0 | 0 | 1.000 |
| control_controller | report_time_only | high | 12 | 84.190 | 10 | 0 | 2 | 0.833 |
| pump_failure | short_stable | high | 5 | 76.642 | 3 | 1 | 1 | 0.800 |
| valve_actuator | early_stable | medium | 5 | 58.814 | 2 | 1 | 2 | 0.600 |
| leakage_water_loss | early_stable | high | 5 | 57.186 | 1 | 2 | 2 | 0.600 |
| unknown_review | review_only | review | 2 | 54.438 | 1 | 0 | 1 | 0.500 |

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
