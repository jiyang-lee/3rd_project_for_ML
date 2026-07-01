# M1 Fault Pre-Event Lead-Time Priority v1 보고서

## 결론
- 최종 판단: `fault_pre_event_gate_v1_locked_for_M1`
- pre-event gate v1은 27번 recipe를 재현했고, M1 기준 잠금 조건을 통과했다.
- rolling lead-time은 회귀 모델이 아니라 threshold 0.6 최초/안정 초과 시점 audit으로 산출했다.
- dispatch priority v1은 ML 모델이 아니라 `risk_probability`, `leadtime_urgency`, `group_weight`를 결합한 정책 score다.
- task/activity는 이번 범위에서 제외했다.

## 핵심 수치
| 항목 | 값 |
| --- | --- |
| fixed eval | normal 35 + pre_event positive 14 |
| feature | compact13_overlap 13개 |
| model | LogisticRegression(class_weight=balanced) |
| threshold | 0.6 |
| balanced accuracy | 0.850000 |
| recall | 0.785714 |
| normal FPR | 0.085714 |
| FP / FN | 3 / 3 |
| rolling fault events | 33 |
| first crossing events | 32 |
| stable crossing events | 25 |
| high / medium priority | 21 / 4 |

## Pre-Event Gate v1 Lock
| final_decision | recipe | feature_set | feature_count | model | threshold | fixed_eval_rows | normal_rows | positive_rows | balanced_accuracy | recall | normal_fpr | false_positive_count | false_negative_count | group_overlap_zero | reproduced_27_recipe | passes_lock_criteria |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fault_pre_event_gate_v1_locked_for_M1 | expanded_compact13_logistic_balanced_threshold_0.6 | compact13_overlap | 13 | LogisticRegression(class_weight=balanced) | 0.6 | 49 | 35 | 14 | 0.85 | 0.785714 | 0.0857143 | 3 | 3 | True | True | True |

## Rolling Lead-Time 결과
- `first_crossing_lead_time_hours`: 먼 anchor부터 가까운 anchor 순서로 threshold 0.6을 처음 넘은 시점이다.
- `stable_crossing_lead_time_hours`: 해당 시점 이후 더 가까운 모든 anchor에서도 threshold 0.6을 유지하는 최초 시점이다.
- Event 20은 low coverage flag, Event 67은 long anomaly flag, Event 34/69는 unknown/review flag로 유지했다.

| event_id | fault_label | d0_probability | first_crossing_lead_time_hours | stable_crossing_lead_time_hours | min_coverage_rate | event20_low_coverage_flag | event67_long_anomaly_flag | unknown_fault_label_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | Leakage | 1 | 168 | 168 | 1 | False | False | False |
| 1 | Motorised control valve (primary side): Actuator defective | 0.999763 | 168 | 168 | 1 | False | False | False |
| 40 | Safety relief valve: Water loss, does not close properly | 0.904853 | 168 | 168 | 0.99504 | False | False | False |
| 47 | Failure of the heating circuit pump | 0.946489 | 72 | 72 | 1 | False | False | False |
| 5 | Failure of the heating circuit pump | 0.983612 | 24 | 24 | 1 | False | False | False |
| 44 | Temperature monitor/controller defective | 0.858773 | 12 | 12 | 1 | False | False | False |
| 7 | Incorrect setting of the differential pressure regulator | 0.999994 | 168 | 0 | 1 | False | False | False |
| 53 | Shut-off valve closed | 0.991303 | 168 | 0 | 1 | False | False | False |
| 69 | unknown | 0.987606 | 168 | 0 | 1 | False | False | True |
| 3 | Control unit: Incorrect parameterisation | 0.985404 | 168 | 0 | 1 | False | False | False |
| 57 | Differential pressure regulator defective | 0.973481 | 168 | 0 | 1 | False | False | False |
| 49 | Control unit: Incorrect parameterisation | 0.960765 | 0 | 0 | 0.997024 | False | False | False |

## Fault Group Priority Profile
| fault_group | rows | fault_label_count | efd_possible_true | mean_monitoring_potential | frequency_norm | monitoring_norm | group_weight |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control_controller | 12 | 2 | 9 | 3.91667 | 1 | 1 | 1 |
| pump_failure | 5 | 2 | 5 | 3.78 | 0.416667 | 0.965106 | 0.636043 |
| valve_actuator | 5 | 4 | 4 | 3.24 | 0.416667 | 0.827234 | 0.580894 |
| pressure_regulator | 4 | 2 | 4 | 3.15 | 0.333333 | 0.804255 | 0.521702 |
| leakage_water_loss | 5 | 3 | 5 | 1.9 | 0.416667 | 0.485106 | 0.444043 |
| unknown_review | 2 | 1 | 2 |  | 0.166667 | 0 | 0.1 |

## Dispatch Priority v1
- 공식: `100 * (0.55*risk_probability + 0.30*leadtime_urgency + 0.15*group_weight)`
- tier: `high >= 80`, `medium >= 65`, `low >= 50`, 그 외 또는 probability < 0.6은 `monitor`.

| event_id | fault_group | risk_probability | stable_crossing_lead_time_hours | leadtime_urgency | group_weight | priority_score | priority_tier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | control_controller | 0.985404 | 0 | 1 | 1 | 99.1972 | high |
| 49 | control_controller | 0.960765 | 0 | 1 | 1 | 97.842 | high |
| 60 | control_controller | 0.911346 | 0 | 1 | 1 | 95.124 | high |
| 23 | control_controller | 0.898881 | 0 | 1 | 1 | 94.4385 | high |
| 5 | pump_failure | 0.983612 | 24 | 1 | 0.636043 | 93.6393 | high |
| 53 | valve_actuator | 0.991303 | 0 | 1 | 0.580894 | 93.2351 | high |
| 62 | control_controller | 0.876529 | 0 | 1 | 1 | 93.2091 | high |
| 7 | pressure_regulator | 0.999994 | 0 | 1 | 0.521702 | 92.8252 | high |
| 32 | control_controller | 0.860889 | 0 | 1 | 1 | 92.3489 | high |
| 44 | control_controller | 0.858773 | 12 | 1 | 1 | 92.2325 | high |
| 57 | pressure_regulator | 0.973481 | 0 | 1 | 0.521702 | 91.367 | high |
| 67 | valve_actuator | 0.951542 | 0 | 1 | 0.580894 | 91.0482 | high |
| 24 | pump_failure | 0.933219 | 0 | 1 | 0.636043 | 90.8677 | high |
| 38 | pressure_regulator | 0.957392 | 0 | 1 | 0.521702 | 90.4821 | high |
| 52 | control_controller | 0.791321 | 0 | 1 | 1 | 88.5227 | high |

## 품질 검증
| check | pass | evidence |
| --- | --- | --- |
| M1 source prefix only | True | manufacturer 1 |
| fixed eval 49 rows retained | True | 49 |
| normal 35 retained | True | 35 |
| positive 14 retained | True | 14 |
| 27 recipe metrics reproduced | True | ba=0.850000, recall=0.785714, fpr=0.085714 |
| saved metric recompute matches | True | ba=0.850000 |
| compact13 only | True | 13 |
| feature leakage terms absent | True | compact13 feature names checked |
| group CV overlap zero | True | 0 |
| rolling window end equals anchor | True | window_end == anchor_time |
| coverage and sample count recorded | True | min_coverage=0.724206 |
| special fault flags retained | True | 20/34/69/67 flags checked |
| all fault labels mapped once | True | 14 |
| priority formula present | True | 100*(0.55*risk_probability+0.30*leadtime_urgency+0.15*group_weight) |
| forbidden manufacturer strings absent | True | generated core CSV checked |

## 한계
- 리드타임은 아직 회귀 예측이 아니라 anchor 기반 audit이다.
- `Report date`는 실제 물리적 고장 발생 시각이 아니라 기록/보고 시각일 수 있다.
- M1 fault는 33건이므로 고장군 supervised classifier를 바로 확정하기에는 작다.
- Event 67 같은 장기 anomaly와 Event 20 같은 coverage 이슈는 별도 해석 flag가 필요하다.

## 다음 작업 순서
1. rolling lead-time anchor를 실제 운영 주기 기준으로 더 촘촘하게 확장한다.
2. priority v1 score를 현장 출동 정책과 맞춰 tier threshold를 검토한다.
3. 고장군별 원시 시계열 예시를 붙여 priority 해석 가능성을 보강한다.
