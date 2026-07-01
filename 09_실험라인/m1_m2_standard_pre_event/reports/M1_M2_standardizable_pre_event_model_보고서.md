# M1+M2 Standardizable Pre-Event Model 보고서

## 결론
최종 판단: **label_window_recheck_required**

이번 실험은 M1 전용 성능을 올리는 것이 아니라, M1/M2를 함께 놓고 다른 현장으로 옮겨갈 수 있는 `normal vs pre_event` 표준 구조를 검증했다.

핵심 결론은 다음과 같다.

- M1/M2 모두 같은 `standard_sensor_schema`로 feature를 계산했다.
- `manufacturer` 값은 학습 feature에 넣지 않고, 검증/분할 metadata로만 사용했다.
- system capability tag는 audit-only와 feature 사용 버전을 분리해 비교했다.
- M2를 학습에 포함한 결과는 외부 성능이 아니라 cross-manufacturer 표준화 검증으로 해석해야 한다.

## 최상위 후보
| feature_set | model | threshold | m1_to_m2_balanced_accuracy | m2_to_m1_balanced_accuracy | pooled_balanced_accuracy | min_leave_manufacturer_ba | leave_manufacturer_ba_gap | min_recall | max_normal_fpr | m2_normal_fpr_vs_old_0_60 | m2_fpr_improved_vs_old_failure | candidate_pass | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| common13 | lightgbm_depth3 | 0.5000 | 0.8071 | 0.7604 | 0.8610 | 0.7604 | 0.0467 | 0.6923 | 0.1714 | 0.1000 | True | False | label_window_recheck_required |

## Dataset 구성
| scope | manufacturer | rows | normal_rows | pre_event_rows | substation_count | coverage_median | excluded_rows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_index | M1 | 64 | 35 | 29 | 31 | 1.0000 | 3 |
| all_index | M2 | 56 | 30 | 26 | 28 | 1.0000 | 5 |
| main_eligible | M1 | 61 | 35 | 26 | 31 | 1.0000 | 0 |
| main_eligible | M2 | 51 | 30 | 21 | 28 | 1.0000 | 0 |
| sensitivity_no_long_anomaly | M1 | 60 | 35 | 25 | 31 | 1.0000 | 0 |
| sensitivity_no_long_anomaly | M2 | 51 | 30 | 21 | 28 | 1.0000 | 0 |

## System Capability 요약
| manufacturer | substations | common10_ready | dhw_supply_available | dhw_storage_available | dhw_return_available | multi_circuit_available |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | 33 | 33 | 25 | 28 | 11 | 7 |
| M2 | 38 | 36 | 17 | 21 | 4 | 4 |

## 표준 Sensor Schema 요약
| schema_role | system_specific | sensor_count |
| --- | --- | --- |
| derived_required_from_common10 | False | 4 |
| optional | True | 6 |
| required | False | 10 |

## 주요 성능표
아래 표는 threshold 0.4/0.5/0.6 후보 중 최상위 decision 후보 중심으로 표시했다.

| evaluation_scope | feature_set | model | threshold | rows | normal_rows | pre_event_rows | balanced_accuracy | precision | recall | f1 | normal_fpr | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1_CV | common13 | hist_gradient_boosting | 0.4000 | 61 | 35 | 26 | 0.7896 | 0.7241 | 0.8077 | 0.7636 | 0.2286 | 27 | 8 | 5 | 21 |
| M1_CV | common13 | lightgbm_depth3 | 0.4000 | 61 | 35 | 26 | 0.6890 | 0.6207 | 0.6923 | 0.6545 | 0.3143 | 24 | 11 | 8 | 18 |
| M1_CV | common13 | lightgbm_depth3 | 0.5000 | 61 | 35 | 26 | 0.6456 | 0.6000 | 0.5769 | 0.5882 | 0.2857 | 25 | 10 | 11 | 15 |
| M1_CV | common13 | lightgbm_depth3 | 0.6000 | 61 | 35 | 26 | 0.6742 | 0.6522 | 0.5769 | 0.6122 | 0.2286 | 27 | 8 | 11 | 15 |
| M1_CV | common13 | random_forest_depth3 | 0.5000 | 61 | 35 | 26 | 0.8132 | 0.8000 | 0.7692 | 0.7843 | 0.1429 | 30 | 5 | 6 | 20 |
| M1_CV | common13 | xgboost_depth3 | 0.4000 | 61 | 35 | 26 | 0.8280 | 0.7419 | 0.8846 | 0.8070 | 0.2286 | 27 | 8 | 3 | 23 |
| M1_CV | common13 | xgboost_depth3 | 0.5000 | 61 | 35 | 26 | 0.7846 | 0.7407 | 0.7692 | 0.7547 | 0.2000 | 28 | 7 | 6 | 20 |
| M1_CV | common13 | xgboost_depth3 | 0.6000 | 61 | 35 | 26 | 0.7027 | 0.7143 | 0.5769 | 0.6383 | 0.1714 | 29 | 6 | 11 | 15 |
| M1_to_M2 | common13 | hist_gradient_boosting | 0.4000 | 51 | 30 | 21 | 0.7976 | 0.7619 | 0.7619 | 0.7619 | 0.1667 | 25 | 5 | 5 | 16 |
| M1_to_M2 | common13 | lightgbm_depth3 | 0.4000 | 51 | 30 | 21 | 0.7905 | 0.7895 | 0.7143 | 0.7500 | 0.1333 | 26 | 4 | 6 | 15 |
| M1_to_M2 | common13 | lightgbm_depth3 | 0.5000 | 51 | 30 | 21 | 0.8071 | 0.8333 | 0.7143 | 0.7692 | 0.1000 | 27 | 3 | 6 | 15 |
| M1_to_M2 | common13 | lightgbm_depth3 | 0.6000 | 51 | 30 | 21 | 0.7929 | 0.9286 | 0.6190 | 0.7429 | 0.0333 | 29 | 1 | 8 | 13 |
| M1_to_M2 | common13 | random_forest_depth3 | 0.5000 | 51 | 30 | 21 | 0.6857 | 0.6667 | 0.5714 | 0.6154 | 0.2000 | 24 | 6 | 9 | 12 |
| M1_to_M2 | common13 | xgboost_depth3 | 0.4000 | 51 | 30 | 21 | 0.7738 | 0.7500 | 0.7143 | 0.7317 | 0.1667 | 25 | 5 | 6 | 15 |
| M1_to_M2 | common13 | xgboost_depth3 | 0.5000 | 51 | 30 | 21 | 0.7595 | 0.8125 | 0.6190 | 0.7027 | 0.1000 | 27 | 3 | 8 | 13 |
| M1_to_M2 | common13 | xgboost_depth3 | 0.6000 | 51 | 30 | 21 | 0.7524 | 0.8571 | 0.5714 | 0.6857 | 0.0667 | 28 | 2 | 9 | 12 |
| M2_CV | common13 | hist_gradient_boosting | 0.4000 | 51 | 30 | 21 | 0.8048 | 0.7391 | 0.8095 | 0.7727 | 0.2000 | 24 | 6 | 4 | 17 |
| M2_CV | common13 | lightgbm_depth3 | 0.4000 | 51 | 30 | 21 | 0.8143 | 0.8000 | 0.7619 | 0.7805 | 0.1333 | 26 | 4 | 5 | 16 |
| M2_CV | common13 | lightgbm_depth3 | 0.5000 | 51 | 30 | 21 | 0.8143 | 0.8000 | 0.7619 | 0.7805 | 0.1333 | 26 | 4 | 5 | 16 |
| M2_CV | common13 | lightgbm_depth3 | 0.6000 | 51 | 30 | 21 | 0.8310 | 0.8421 | 0.7619 | 0.8000 | 0.1000 | 27 | 3 | 5 | 16 |
| M2_CV | common13 | random_forest_depth3 | 0.5000 | 51 | 30 | 21 | 0.8452 | 0.7826 | 0.8571 | 0.8182 | 0.1667 | 25 | 5 | 3 | 18 |
| M2_CV | common13 | xgboost_depth3 | 0.4000 | 51 | 30 | 21 | 0.8452 | 0.7826 | 0.8571 | 0.8182 | 0.1667 | 25 | 5 | 3 | 18 |
| M2_CV | common13 | xgboost_depth3 | 0.5000 | 51 | 30 | 21 | 0.8452 | 0.7826 | 0.8571 | 0.8182 | 0.1667 | 25 | 5 | 3 | 18 |
| M2_CV | common13 | xgboost_depth3 | 0.6000 | 51 | 30 | 21 | 0.8214 | 0.7727 | 0.8095 | 0.7907 | 0.1667 | 25 | 5 | 4 | 17 |
| M2_to_M1 | common13 | hist_gradient_boosting | 0.4000 | 61 | 35 | 26 | 0.6940 | 0.6129 | 0.7308 | 0.6667 | 0.3429 | 23 | 12 | 7 | 19 |
| M2_to_M1 | common13 | lightgbm_depth3 | 0.4000 | 61 | 35 | 26 | 0.7319 | 0.6923 | 0.6923 | 0.6923 | 0.2286 | 27 | 8 | 8 | 18 |
| M2_to_M1 | common13 | lightgbm_depth3 | 0.5000 | 61 | 35 | 26 | 0.7604 | 0.7500 | 0.6923 | 0.7200 | 0.1714 | 29 | 6 | 8 | 18 |
| M2_to_M1 | common13 | lightgbm_depth3 | 0.6000 | 61 | 35 | 26 | 0.7412 | 0.7391 | 0.6538 | 0.6939 | 0.1714 | 29 | 6 | 9 | 17 |
| M2_to_M1 | common13 | random_forest_depth3 | 0.5000 | 61 | 35 | 26 | 0.7604 | 0.7500 | 0.6923 | 0.7200 | 0.1714 | 29 | 6 | 8 | 18 |
| M2_to_M1 | common13 | xgboost_depth3 | 0.4000 | 61 | 35 | 26 | 0.7462 | 0.7200 | 0.6923 | 0.7059 | 0.2000 | 28 | 7 | 8 | 18 |

## Decision Matrix
| feature_set | model | threshold | m1_to_m2_balanced_accuracy | m2_to_m1_balanced_accuracy | pooled_balanced_accuracy | min_leave_manufacturer_ba | leave_manufacturer_ba_gap | min_recall | max_normal_fpr | m2_normal_fpr_vs_old_0_60 | m2_fpr_improved_vs_old_failure | candidate_pass | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| common13 | lightgbm_depth3 | 0.5000 | 0.8071 | 0.7604 | 0.8610 | 0.7604 | 0.0467 | 0.6923 | 0.1714 | 0.1000 | True | False | label_window_recheck_required |
| common13 | xgboost_depth3 | 0.4000 | 0.7738 | 0.7462 | 0.8746 | 0.7462 | 0.0277 | 0.6923 | 0.2000 | 0.1667 | True | False | label_window_recheck_required |
| common13 | lightgbm_depth3 | 0.4000 | 0.7905 | 0.7319 | 0.8746 | 0.7319 | 0.0586 | 0.6923 | 0.2286 | 0.1333 | True | False | label_window_recheck_required |
| common13 | lightgbm_depth3 | 0.6000 | 0.7929 | 0.7412 | 0.8155 | 0.7412 | 0.0516 | 0.6190 | 0.1714 | 0.0333 | True | False | label_window_recheck_required |
| common13 | xgboost_depth3 | 0.5000 | 0.7595 | 0.7412 | 0.8368 | 0.7412 | 0.0183 | 0.6190 | 0.1714 | 0.1000 | True | False | label_window_recheck_required |
| common13 | xgboost_depth3 | 0.6000 | 0.7524 | 0.7170 | 0.8232 | 0.7170 | 0.0353 | 0.5714 | 0.1429 | 0.0667 | True | False | label_window_recheck_required |
| common13 | hist_gradient_boosting | 0.4000 | 0.7976 | 0.6940 | 0.8516 | 0.6940 | 0.1037 | 0.7308 | 0.3429 | 0.1667 | True | False | label_window_recheck_required |
| common13 | random_forest_depth3 | 0.5000 | 0.6857 | 0.7604 | 0.8427 | 0.6857 | 0.0747 | 0.5714 | 0.2000 | 0.2000 | True | False | label_window_recheck_required |
| common13 | random_forest_depth5 | 0.5000 | 0.6857 | 0.7462 | 0.8244 | 0.6857 | 0.0604 | 0.5714 | 0.2000 | 0.2000 | True | False | label_window_recheck_required |
| common13 | random_forest_depth3 | 0.6000 | 0.6976 | 0.7121 | 0.7777 | 0.6976 | 0.0145 | 0.4286 | 0.1143 | 0.0333 | True | False | label_window_recheck_required |
| common13 | random_forest_depth5 | 0.6000 | 0.6976 | 0.7121 | 0.7700 | 0.6976 | 0.0145 | 0.4286 | 0.1143 | 0.0333 | True | False | label_window_recheck_required |
| common13 | random_forest_depth5 | 0.4000 | 0.7048 | 0.6654 | 0.8296 | 0.6654 | 0.0394 | 0.7308 | 0.4000 | 0.4000 | True | False | label_window_recheck_required |
| common13 | hist_gradient_boosting | 0.6000 | 0.7381 | 0.7077 | 0.8049 | 0.7077 | 0.0304 | 0.4762 | 0.2000 | 0.0000 | True | False | label_window_recheck_required |
| common13 | random_forest_depth3 | 0.4000 | 0.7119 | 0.6654 | 0.8296 | 0.6654 | 0.0465 | 0.7308 | 0.4333 | 0.4333 | True | False | label_window_recheck_required |
| common13 | extra_trees_depth5 | 0.5000 | 0.6548 | 0.6549 | 0.7943 | 0.6548 | 0.0002 | 0.4762 | 0.2286 | 0.1667 | True | False | label_window_recheck_required |
| common13 | extra_trees_depth5 | 0.4000 | 0.7095 | 0.6280 | 0.7278 | 0.6280 | 0.0815 | 0.8846 | 0.6286 | 0.5333 | True | False | label_window_recheck_required |
| common13 | extra_trees_depth3 | 0.5000 | 0.7024 | 0.6214 | 0.7943 | 0.6214 | 0.0810 | 0.5000 | 0.2571 | 0.1667 | True | False | label_window_recheck_required |
| common13 | hist_gradient_boosting | 0.5000 | 0.7381 | 0.6698 | 0.8746 | 0.6698 | 0.0683 | 0.4762 | 0.3143 | 0.0000 | True | False | label_window_recheck_required |
| common13 | extra_trees_depth3 | 0.4000 | 0.6500 | 0.5901 | 0.6462 | 0.5901 | 0.0599 | 0.9231 | 0.7429 | 0.7000 | False | False | label_window_recheck_required |
| common13 | extra_trees_depth5 | 0.6000 | 0.5548 | 0.5484 | 0.6519 | 0.5484 | 0.0064 | 0.1429 | 0.0571 | 0.0333 | True | False | label_window_recheck_required |

## 해석
- `standard_common`은 공통 10개 센서 기반으로 모든 현장에 가장 쉽게 이식할 수 있는 기준이다.
- `standard_common_plus_system`은 시스템 구성을 반영하지만, 제조사/설비 구성에 과적합할 수 있어 양방향 제조사 검증을 반드시 통과해야 한다.
- `standard_optional_dhw`는 DHW 센서가 있는 현장에서만 의미가 있으므로, 전체 운영 모델이 아니라 보조 모델 후보로만 본다.
- 복잡한 tree/boosting 모델은 Logistic보다 좋아 보여도 `M1→M2`, `M2→M1` 중 한쪽이 무너지면 표준 모델 후보로 잠그지 않는다.

## 한계
- M1/M2는 같은 PreDist 계열이므로 완전히 독립된 외부 기관 검증은 아니다.
- `efd_possible=True` 자체가 fault 내부 metadata이므로, 조기탐지 가능 라벨의 품질 한계가 남아 있다.
- system tag는 실제 설비 구성을 완벽히 설명하는 엔지니어링 메타데이터가 아니라 raw sensor 보유 상태 기반 proxy다.
- DHW 보조 모델은 샘플 수와 센서 보유 편향을 함께 확인해야 한다.

## 다음 작업 순서
1. decision matrix의 최상위 후보가 `*_candidate` 또는 `*_ready`이면 해당 조합으로 final joblib 후보를 별도 검증한다.
2. 후보가 `label_window_recheck_required`이면 모델 확장보다 positive/normal window 정책을 다시 검토한다.
3. DHW subset이 유효하면 DHW 보조 gate를 별도 산출물로 분리한다.
4. 완전히 독립된 라벨 포함 SCADA 데이터가 생기면 현재 schema로 external validation을 추가한다.

## 품질 검증
실패한 품질 검증 없음

## 산출물
- `standard_sensor_schema.csv`
- `system_capability_audit.csv`
- `pre_event_dataset_index.csv`
- `standard_feature_pool.csv`
- `model_selection_metrics.csv`
- `leave_manufacturer_out_metrics.csv`
- `calibration_threshold_audit.csv`
- `standard_model_decision_matrix.csv`
- `quality_audit.csv`

source commit: `eae89855b7ae81438945d1ba0790b4c894f42256`
