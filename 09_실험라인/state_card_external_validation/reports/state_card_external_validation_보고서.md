# State Card External Validation 보고서

## 결론
- 최종 출력은 단일 class가 아니라 `primary_state + secondary_tags + pre_event_detected + fault_group + leadtime_label + priority_tier + why_reason` 형태의 상태카드로 잠갔다.
- M1 내부 full gate는 기존 33번 runtime policy를 그대로 재현해 상태카드로 변환했다.
- M1↔M2 성능은 `common13 + LightGBM depth3 + threshold 0.5`를 기준 후보로 정리했다. 이는 완전 외부가 아니라 cross-manufacturer 검증이다.
- XAI4HEAT는 라벨과 report date가 없어 성능점수를 계산하지 않았다. 현재는 필수 feature 일부가 없어 상태카드가 `review_required`로 차단되는 runtime/schema 검증 결과다.

## 상태카드 스키마
| field_name | type | plain_korean_meaning | source | required |
| --- | --- | --- | --- | --- |
| sample_id | string | 상태카드 대상 window 또는 event ID | runtime/window input | True |
| data_scope | string | M1 내부, M1↔M2, XAI4HEAT 중 출처 구분 | validation layer | True |
| substation_id | string | 기계실 또는 외부 SCADA 파일 ID | input metadata | True |
| window_start | datetime | 센서 feature 계산 window 시작 | feature window | False |
| window_end | datetime | 센서 feature 계산 window 끝 | feature window | False |
| primary_state | string | 최종 상태 normal/fault/task/activity/review_required | conflict resolver | True |
| secondary_tags | string | 동시에 켜진 보조 gate 목록 | conflict resolver | False |
| fault_detected | boolean | fault gate 통과 여부 | RandomForest fault gate | True |
| task_detected | boolean | task gate 통과 여부 | RandomForest task gate | True |
| activity_detected | boolean | activity gate 통과 여부 | RandomForest activity gate | True |
| pre_event_detected | string | fault branch에서 조기탐지 gate 통과 여부 또는 불가 사유 | fault pre_event gate | True |
| risk_probability | float | fault pre_event 위험 확률 | Logistic/standard candidate | False |
| fault_group | string | 고장군 | fault taxonomy | False |
| leadtime_label | string | 고장군 stable crossing 리드타임 등급 | 29 lead-time audit | False |
| priority_score | float | 출동 우선순위 정책 점수 | 30 priority policy | False |
| priority_tier | string | high/medium/low/monitor | 30 priority policy | False |
| review_flag | boolean | 수동 검토 필요 여부 | resolver/metadata | True |
| why_reason | string | 사람이 읽는 판정 이유 | runtime explanation | True |
| label_metric_available | boolean | 이 데이터에서 성능지표 계산 가능 여부 | validation layer | True |
| validation_level | string | performance/runtime/proxy/not_available 구분 | validation layer | True |

## Runtime Rule
| rule_id | component | condition | output | model_or_rule | note |
| --- | --- | --- | --- | --- | --- |
| R1 | front_gates | fault/task/activity gate를 병렬 적용 | 각 gate probability와 detected flag | RandomForest depth3, threshold 0.5 | task는 조기탐지가 아니라 상태/작업 감지 |
| R2 | conflict_resolver | fault와 task/activity가 동시에 켜짐 | primary_state=fault, secondary_tags에 task/activity 보존 | deterministic rule | 운영 위험도가 높은 fault 우선 |
| R3 | conflict_resolver | task와 activity만 동시에 켜짐 | 확률이 높은 쪽을 primary_state로 선택 | probability comparison | 둘 다 secondary tag에도 남김 |
| R4 | fault_pre_event | primary_state=fault | pre_event_detected와 risk_probability | pre_event model, threshold 0.6 | fault branch에서만 계산 |
| R5 | leadtime_priority | fault이고 risk_probability >= 0.6 | fault_group, leadtime_label, priority_score, priority_tier | 29 stable crossing + 30 baseline policy | priority는 ML 모델이 아니라 정책 점수 |
| R6 | external_runtime | 외부 데이터에 라벨 또는 필수 feature가 없음 | review_required 또는 not_available 사유 기록 | availability rule | 성능점수 대신 coverage/runtime 검증 |

## M1↔M2 Pre-Event 성능 근거
| evaluation_scope | feature_set | model | threshold | rows | normal_rows | pre_event_rows | balanced_accuracy | precision | recall | f1 | normal_fpr | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1_to_M2 | common13 | lightgbm_depth3 | 0.5000 | 51 | 30 | 21 | 0.8071 | 0.8333 | 0.7143 | 0.7692 | 0.1000 | 27 | 3 | 6 | 15 |
| M2_to_M1 | common13 | lightgbm_depth3 | 0.5000 | 61 | 35 | 26 | 0.7604 | 0.7500 | 0.6923 | 0.7200 | 0.1714 | 29 | 6 | 8 | 18 |

## 상태카드 출력 분포
| data_scope | primary_state | size |
| --- | --- | --- |
| M1_full_gate_internal | activity | 47 |
| M1_full_gate_internal | fault | 56 |
| M1_full_gate_internal | normal | 34 |
| M1_full_gate_internal | task | 42 |
| M1_to_M2 | fault | 18 |
| M1_to_M2 | normal | 33 |
| M2_to_M1 | fault | 24 |
| M2_to_M1 | normal | 37 |
| XAI4HEAT_runtime | review_required | 5 |

## XAI4HEAT Runtime 검증
### Schema Mapping
| match_status | count |
| --- | --- |
| missing | 10 |
| semantic_match | 30 |

### Feature Coverage
| feature_available | count |
| --- | --- |
| False | 15 |
| True | 50 |

### Runtime State Card
| primary_state | count |
| --- | --- |
| review_required | 5 |

## Decision Matrix
| decision_item | status | evidence | final_decision |
| --- | --- | --- | --- |
| state_card_schema_locked | pass | 20 output fields | state_card_ready_internal_cross_manufacturer_partial_external_runtime |
| m1_full_gate_internal | pass | fault_gate_locked_for_runtime_v1_with_threshold_review; task_gate_locked_as_state_detector_v1; activity_gate_locked_for_runtime_v1; fault_pre_event_gate_v1_locked_for_M1; baseline_28_keep_as_policy_v1 | state_card_ready_internal_cross_manufacturer_partial_external_runtime |
| m1_m2_cross_manufacturer_pre_event | partial | LightGBM threshold 0.5 min_BA=0.7604, min_recall=0.6923, max_normal_FPR=0.1714 | state_card_ready_internal_cross_manufacturer_partial_external_runtime |
| xai4heat_state_card_runtime | blocked_by_missing_features | 5/5 files review_required; feature availability=0.7692 | state_card_ready_internal_cross_manufacturer_partial_external_runtime |
| xai4heat_label_performance | not_applicable | XAI4HEAT has no fault/task/activity or report-date labels for this validation | state_card_ready_internal_cross_manufacturer_partial_external_runtime |

## 한계
- XAI4HEAT에는 fault/task/activity 라벨과 고장 report date가 없어 BA, precision, recall, f1을 계산할 수 없다.
- XAI4HEAT는 1시간 해상도이고, PreDist M1/M2는 10분 해상도 기준이라 feature 의미가 완전히 같지 않다.
- M1↔M2 검증은 제조사 간 검증이지 완전 독립 외부 현장 검증은 아니다.
- 현재 XAI4HEAT는 `p_net_meter_flow` 등 일부 required feature가 없어 front gate inference가 차단된다.

## 다음 작업 순서
1. 상태카드 출력 스키마를 joblib inference wrapper의 반환 형식으로 맞춘다.
2. 외부 현장 데이터 요청 포맷을 이 상태카드 필드 기준으로 정리한다.
3. report date가 있는 외부 district-heating fault 데이터가 확보되면 이 실험라인에 `performance_validation_external`을 추가한다.
4. XAI4HEAT 대응을 계속하려면 누락 feature 허용 모델 또는 별도 SCADA-compatible feature set을 설계한다.

## Quality Audit
| check | pass | evidence |
| --- | --- | --- |
| state_card_required_columns_present | True | missing=[] |
| non_fault_no_priority_score | True | priority score only populated on fault branch |
| m1_full_gate_rows_included | True | 179 |
| m1_m2_lightgbm_holdout_rows | True | rows=2 |
| xai4heat_no_label_metrics | True | {'external_runtime_validation_only': 5} |
| xai4heat_missing_features_recorded | True | {True: 50, False: 15} |
| predist_original_not_modified | True | clean |
| xai4heat_original_not_modified | True | clean |
