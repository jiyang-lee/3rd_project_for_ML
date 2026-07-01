# M1 Fault Group Lead-Time Audit Lock 보고서

## 결론
- 최종 판단: `fault_group_leadtime_audit_locked_for_M1`
- 새 리드타임 모델은 만들지 않았다. 28번에서 잠긴 pre-event gate를 그대로 사용했다.
- 공식 리드타임 기준은 `stable_crossing_lead_time_hours`다. `first_crossing_lead_time_hours`는 조기 흔적 참고 지표로만 둔다.
- clean 기준에서 며칠 전부터 안정적으로 잡히는 후보는 `valve_actuator, leakage_water_loss`이다.
- 짧은 리드타임 후보는 `pump_failure`이고, 당일성 fault signal은 `control_controller, pressure_regulator`이다.
- 28번 dispatch priority v1 공식은 변경하지 않았다. 이번 결과는 priority 해석의 근거 표로만 사용한다.

## 현재 모델 위치
| 항목 | 값 |
| --- | --- |
| feature | compact13_overlap 13개 |
| model | LogisticRegression(class_weight=balanced) |
| threshold | 0.6 |
| 28번 lock decision | fault_pre_event_gate_v1_locked_for_M1 |
| fixed eval balanced accuracy | 0.850000 |
| fixed eval recall | 0.785714 |
| fixed eval normal FPR | 0.085714 |

## 조기탐지 -> 리드타임 -> 빈번도 로직
1. 10분 단위 센서값을 7일 window로 묶고 `compact13_overlap` feature를 계산한다.
2. LogisticRegression pre-event gate가 fault pre-event 확률을 낸다.
3. `D-7`, `D-5`, `D-3`, `D-1`, `D-12h`, `D-0` anchor에 같은 모델을 반복 적용한다.
4. threshold 0.6을 안정적으로 넘기기 시작한 시점을 `stable lead-time`으로 본다.
5. 이 값을 고장군별 빈번도와 함께 보아 출동 우선순위 해석 근거로 사용한다.

## Clean 기준 고장군별 리드타임
| fault_group | event_count | d0_detection_rate | stable_crossing_detection_rate | median_stable_lead_time_days | p25_stable_lead_time_hours | p75_stable_lead_time_hours | leadtime_label | leadtime_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| control_controller | 12 | 0.833 | 0.833 | 0.000 | 0.000 | 0.000 | report_time_only | high |
| pump_failure | 5 | 0.800 | 0.800 | 0.500 | 0.000 | 36.000 | short_stable | high |
| valve_actuator | 4 | 0.500 | 0.500 | 3.500 | 42.000 | 126.000 | early_stable | medium |
| pressure_regulator | 4 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | report_time_only | high |
| leakage_water_loss | 4 | 0.750 | 0.750 | 7.000 | 84.000 | 168.000 | early_stable | high |
| unknown_review | 0 |  |  |  |  |  | review_only | review |

## Main 기준 고장군별 리드타임
| fault_group | event_count | d0_detection_rate | stable_crossing_detection_rate | median_stable_lead_time_days | leadtime_label | leadtime_confidence | event20_included_count | event67_included_count | unknown_event_included_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| control_controller | 12 | 0.833 | 0.833 | 0.000 | report_time_only | high | 0 | 0 | 0 |
| pump_failure | 5 | 0.800 | 0.800 | 0.500 | short_stable | high | 0 | 0 | 0 |
| valve_actuator | 5 | 0.600 | 0.600 | 0.000 | report_time_only | medium | 0 | 1 | 0 |
| pressure_regulator | 4 | 1.000 | 1.000 | 0.000 | report_time_only | high | 0 | 0 | 0 |
| leakage_water_loss | 5 | 0.600 | 0.600 | 7.000 | early_stable | medium | 1 | 0 | 0 |
| unknown_review | 2 | 0.500 | 0.500 | 0.000 | review_only | review | 0 | 0 | 2 |

## Anchor별 탐지율
| fault_group | event_count | d_minus_7_detection_rate | d_minus_5_detection_rate | d_minus_3_detection_rate | d_minus_1_detection_rate | d_minus_12h_detection_rate | d0_detection_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control_controller | 12 | 0.417 | 0.250 | 0.417 | 0.500 | 0.083 | 0.833 |
| pump_failure | 5 | 0.600 | 0.600 | 0.600 | 0.800 | 0.400 | 0.800 |
| valve_actuator | 4 | 1.000 | 0.750 | 1.000 | 1.000 | 0.250 | 0.500 |
| pressure_regulator | 4 | 0.750 | 0.750 | 0.750 | 0.750 | 0.000 | 1.000 |
| leakage_water_loss | 4 | 0.750 | 0.500 | 1.000 | 0.750 | 0.500 | 0.750 |
| unknown_review | 0 |  |  |  |  |  |  |

## Decision Matrix
| fault_group | event_count | leadtime_label | leadtime_confidence | leadtime_lock_decision | operational_meaning |
| --- | --- | --- | --- | --- | --- |
| control_controller | 12 | report_time_only | high | group_leadtime_locked_as_audit | same_day_fault_signal |
| pump_failure | 5 | short_stable | high | group_leadtime_locked_as_audit | short_leadtime_warning_candidate |
| valve_actuator | 4 | early_stable | medium | group_leadtime_locked_as_audit | days_before_warning_candidate |
| pressure_regulator | 4 | report_time_only | high | group_leadtime_locked_as_audit | same_day_fault_signal |
| leakage_water_loss | 4 | early_stable | high | group_leadtime_locked_as_audit | days_before_warning_candidate |
| unknown_review | 0 | review_only | review | review_only | manual_review_only |

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
