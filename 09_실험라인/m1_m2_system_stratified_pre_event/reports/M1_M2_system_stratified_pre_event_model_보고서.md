# M1+M2 System-Stratified Pre-Event Model 보고서

## 결론
최종 판단: **system_aux_model_candidate_only**

시스템별 threshold 보정과 시스템별 보조모델을 모두 검증했다.
전체 runtime에 바로 넣을 수 있는 `system_specific_threshold` 후보는 아직 잠금 기준을 통과하지 못했지만, 일부 system group 내부 보조모델은 후보로 남길 수 있다.
따라서 joblib 패키지는 운영 확정 모델이 아니라 `global_not_locked_aux_candidates_available` 상태의 재검증용 후보로 저장했다.

## 핵심 결과
- 시스템별 threshold 보정은 일부 FPR을 줄였지만 full runtime 기준 recall을 안정적으로 넘기지 못했다.
- 시스템별 보조모델은 `dhw_storage`, `dhw_storage_return`, `heating_common_only`에서 후보가 나왔지만, 일부 그룹은 제조사/라벨 분포가 치우쳐 있어 보조모델로만 취급한다.
- `dhw_return`, `dhw_supply`는 positive sample이 없어 audit 전용이다.
- 결론적으로 다음은 모델 추가가 아니라 `system group × fault label/window` 재설계가 우선이다.

## System Group Dataset
| system_capability_group | manufacturer | label | rows | substations |
| --- | --- | --- | --- | --- |
| dhw_return | M1 | normal | 2 | 1 |
| dhw_storage | M1 | normal | 19 | 12 |
| dhw_storage | M1 | pre_event | 14 | 10 |
| dhw_storage | M2 | normal | 15 | 9 |
| dhw_storage | M2 | pre_event | 13 | 12 |
| dhw_storage_return | M1 | normal | 9 | 6 |
| dhw_storage_return | M1 | pre_event | 10 | 7 |
| dhw_storage_return | M2 | normal | 3 | 2 |
| dhw_supply | M2 | normal | 1 | 1 |
| heating_common_only | M1 | normal | 5 | 3 |
| heating_common_only | M1 | pre_event | 2 | 2 |
| heating_common_only | M2 | normal | 11 | 8 |
| heating_common_only | M2 | pre_event | 8 | 8 |

## Decision Matrix
| candidate_type | feature_set | model | threshold_policy | min_leave_manufacturer_ba | min_recall | max_normal_fpr | candidate_pass | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| system_aux_model | common13 | lightgbm_depth3 | dhw_storage_return@0.4 |  | 0.9000 | 0.1667 | True | system_aux_model_candidate |
| system_aux_model | common13 | lightgbm_depth3 | dhw_storage_return@0.5 |  | 0.9000 | 0.1667 | True | system_aux_model_candidate |
| system_aux_model | common13 | random_forest_depth3 | heating_common_only@0.4 |  | 0.9000 | 0.1875 | True | system_aux_model_candidate |
| system_aux_model | common13 | extra_trees_depth3 | dhw_storage@0.5 |  | 0.8148 | 0.1176 | True | system_aux_model_candidate |
| system_aux_model | common13 | logistic_balanced | dhw_storage@0.5 |  | 0.8148 | 0.1176 | True | system_aux_model_candidate |
| system_aux_model | common13 | logistic_balanced | dhw_storage@0.6 |  | 0.7037 | 0.0294 | True | system_aux_model_candidate |
| system_aux_model | common13 | lightgbm_depth3 | dhw_storage_return@0.6 |  | 0.8000 | 0.1667 | True | system_aux_model_candidate |
| system_aux_model | common13 | xgboost_depth3 | dhw_storage_return@0.6 |  | 0.7000 | 0.0833 | True | system_aux_model_candidate |
| system_aux_model | common13 | logistic_balanced | dhw_storage@0.4 |  | 0.8148 | 0.2353 | True | system_aux_model_candidate |
| system_aux_model | common13 | lightgbm_depth3 | heating_common_only@0.4 |  | 0.7000 | 0.1250 | True | system_aux_model_candidate |

## System Threshold Metrics 상위
| strategy | evaluation_scope | feature_set | model | fallback_threshold | rows | normal_rows | pre_event_rows | balanced_accuracy | precision | recall | f1 | normal_fpr | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| system_specific_threshold | M2_CV | common13 | extra_trees_depth5 | 0.5000 | 51 | 30 | 21 | 0.9119 | 0.9474 | 0.8571 | 0.9000 | 0.0333 | 29 | 1 | 3 | 18 |
| system_specific_threshold | M2_CV | common13 | extra_trees_depth5 | 0.6000 | 51 | 30 | 21 | 0.9119 | 0.9474 | 0.8571 | 0.9000 | 0.0333 | 29 | 1 | 3 | 18 |
| system_specific_threshold | M2_CV | common13 | extra_trees_depth3 | 0.5000 | 51 | 30 | 21 | 0.8952 | 0.9000 | 0.8571 | 0.8780 | 0.0667 | 28 | 2 | 3 | 18 |
| system_specific_threshold | M2_CV | common13 | extra_trees_depth3 | 0.6000 | 51 | 30 | 21 | 0.8952 | 0.9000 | 0.8571 | 0.8780 | 0.0667 | 28 | 2 | 3 | 18 |
| system_specific_threshold | M2_CV | common13 | extra_trees_depth5 | 0.4000 | 51 | 30 | 21 | 0.8952 | 0.9000 | 0.8571 | 0.8780 | 0.0667 | 28 | 2 | 3 | 18 |
| system_specific_threshold | M2_CV | common13 | logistic_balanced | 0.4000 | 51 | 30 | 21 | 0.8952 | 0.9000 | 0.8571 | 0.8780 | 0.0667 | 28 | 2 | 3 | 18 |
| system_specific_threshold | M2_CV | common13 | logistic_balanced | 0.5000 | 51 | 30 | 21 | 0.8952 | 0.9000 | 0.8571 | 0.8780 | 0.0667 | 28 | 2 | 3 | 18 |
| system_specific_threshold | M2_CV | common13 | logistic_balanced | 0.6000 | 51 | 30 | 21 | 0.8952 | 0.9000 | 0.8571 | 0.8780 | 0.0667 | 28 | 2 | 3 | 18 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | lightgbm_depth3 | 0.4000 | 112 | 65 | 47 | 0.8900 | 0.8723 | 0.8723 | 0.8723 | 0.0923 | 59 | 6 | 6 | 41 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | lightgbm_depth3 | 0.5000 | 112 | 65 | 47 | 0.8900 | 0.8723 | 0.8723 | 0.8723 | 0.0923 | 59 | 6 | 6 | 41 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | lightgbm_depth3 | 0.6000 | 112 | 65 | 47 | 0.8900 | 0.8723 | 0.8723 | 0.8723 | 0.0923 | 59 | 6 | 6 | 41 |
| system_specific_threshold | M2_CV | common13 | extra_trees_depth3 | 0.4000 | 51 | 30 | 21 | 0.8786 | 0.8571 | 0.8571 | 0.8571 | 0.1000 | 27 | 3 | 3 | 18 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | hist_gradient_boosting | 0.4000 | 112 | 65 | 47 | 0.8746 | 0.8367 | 0.8723 | 0.8542 | 0.1231 | 57 | 8 | 6 | 41 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | hist_gradient_boosting | 0.5000 | 112 | 65 | 47 | 0.8746 | 0.8367 | 0.8723 | 0.8542 | 0.1231 | 57 | 8 | 6 | 41 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | hist_gradient_boosting | 0.6000 | 112 | 65 | 47 | 0.8746 | 0.8367 | 0.8723 | 0.8542 | 0.1231 | 57 | 8 | 6 | 41 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | xgboost_depth3 | 0.4000 | 112 | 65 | 47 | 0.8717 | 0.8511 | 0.8511 | 0.8511 | 0.1077 | 58 | 7 | 7 | 40 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | xgboost_depth3 | 0.5000 | 112 | 65 | 47 | 0.8717 | 0.8511 | 0.8511 | 0.8511 | 0.1077 | 58 | 7 | 7 | 40 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | xgboost_depth3 | 0.6000 | 112 | 65 | 47 | 0.8717 | 0.8511 | 0.8511 | 0.8511 | 0.1077 | 58 | 7 | 7 | 40 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | logistic_balanced | 0.5000 | 112 | 65 | 47 | 0.8552 | 0.8810 | 0.7872 | 0.8315 | 0.0769 | 60 | 5 | 10 | 37 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | logistic_balanced | 0.6000 | 112 | 65 | 47 | 0.8552 | 0.8810 | 0.7872 | 0.8315 | 0.0769 | 60 | 5 | 10 | 37 |
| system_specific_threshold | M2_CV | common13 | random_forest_depth3 | 0.4000 | 51 | 30 | 21 | 0.8548 | 0.8500 | 0.8095 | 0.8293 | 0.1000 | 27 | 3 | 4 | 17 |
| system_specific_threshold | M2_CV | common13 | random_forest_depth3 | 0.5000 | 51 | 30 | 21 | 0.8548 | 0.8500 | 0.8095 | 0.8293 | 0.1000 | 27 | 3 | 4 | 17 |
| system_specific_threshold | M2_CV | common13 | random_forest_depth3 | 0.6000 | 51 | 30 | 21 | 0.8548 | 0.8500 | 0.8095 | 0.8293 | 0.1000 | 27 | 3 | 4 | 17 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | logistic_balanced | 0.4000 | 112 | 65 | 47 | 0.8475 | 0.8605 | 0.7872 | 0.8222 | 0.0923 | 59 | 6 | 10 | 37 |
| system_specific_threshold | Pooled_M1_M2_group_CV | common13 | random_forest_depth3 | 0.4000 | 112 | 65 | 47 | 0.8475 | 0.8605 | 0.7872 | 0.8222 | 0.0923 | 59 | 6 | 10 | 37 |

## System Auxiliary Model Metrics 상위
| system_capability_group | model | threshold | rows | normal_rows | pre_event_rows | balanced_accuracy | precision | recall | f1 | normal_fpr | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dhw_storage_return | lightgbm_depth3 | 0.4000 | 22 | 12 | 10 | 0.8667 | 0.8182 | 0.9000 | 0.8571 | 0.1667 | 10 | 2 | 1 | 9 |
| dhw_storage_return | lightgbm_depth3 | 0.5000 | 22 | 12 | 10 | 0.8667 | 0.8182 | 0.9000 | 0.8571 | 0.1667 | 10 | 2 | 1 | 9 |
| heating_common_only | random_forest_depth3 | 0.4000 | 26 | 16 | 10 | 0.8562 | 0.7500 | 0.9000 | 0.8182 | 0.1875 | 13 | 3 | 1 | 9 |
| dhw_storage | logistic_balanced | 0.5000 | 61 | 34 | 27 | 0.8486 | 0.8462 | 0.8148 | 0.8302 | 0.1176 | 30 | 4 | 5 | 22 |
| dhw_storage | extra_trees_depth3 | 0.5000 | 61 | 34 | 27 | 0.8486 | 0.8462 | 0.8148 | 0.8302 | 0.1176 | 30 | 4 | 5 | 22 |
| dhw_storage | logistic_balanced | 0.6000 | 61 | 34 | 27 | 0.8371 | 0.9500 | 0.7037 | 0.8085 | 0.0294 | 33 | 1 | 8 | 19 |
| dhw_storage_return | lightgbm_depth3 | 0.6000 | 22 | 12 | 10 | 0.8167 | 0.8000 | 0.8000 | 0.8000 | 0.1667 | 10 | 2 | 2 | 8 |
| dhw_storage_return | xgboost_depth3 | 0.6000 | 22 | 12 | 10 | 0.8083 | 0.8750 | 0.7000 | 0.7778 | 0.0833 | 11 | 1 | 3 | 7 |
| dhw_storage | hist_gradient_boosting | 0.4000 | 61 | 34 | 27 | 0.7936 | 0.7188 | 0.8519 | 0.7797 | 0.2647 | 25 | 9 | 4 | 23 |
| dhw_storage | logistic_balanced | 0.4000 | 61 | 34 | 27 | 0.7898 | 0.7333 | 0.8148 | 0.7719 | 0.2353 | 26 | 8 | 5 | 22 |
| heating_common_only | lightgbm_depth3 | 0.4000 | 26 | 16 | 10 | 0.7875 | 0.7778 | 0.7000 | 0.7368 | 0.1250 | 14 | 2 | 3 | 7 |
| heating_common_only | lightgbm_depth3 | 0.5000 | 26 | 16 | 10 | 0.7875 | 0.7778 | 0.7000 | 0.7368 | 0.1250 | 14 | 2 | 3 | 7 |
| heating_common_only | lightgbm_depth3 | 0.6000 | 26 | 16 | 10 | 0.7875 | 0.7778 | 0.7000 | 0.7368 | 0.1250 | 14 | 2 | 3 | 7 |
| dhw_storage | xgboost_depth3 | 0.6000 | 61 | 34 | 27 | 0.7821 | 0.7692 | 0.7407 | 0.7547 | 0.1765 | 28 | 6 | 7 | 20 |
| dhw_storage | xgboost_depth3 | 0.5000 | 61 | 34 | 27 | 0.7751 | 0.7097 | 0.8148 | 0.7586 | 0.2647 | 25 | 9 | 5 | 22 |
| heating_common_only | random_forest_depth3 | 0.5000 | 26 | 16 | 10 | 0.7688 | 0.8571 | 0.6000 | 0.7059 | 0.0625 | 15 | 1 | 4 | 6 |
| dhw_storage | random_forest_depth3 | 0.5000 | 61 | 34 | 27 | 0.7674 | 0.7407 | 0.7407 | 0.7407 | 0.2059 | 27 | 7 | 7 | 20 |
| dhw_storage | lightgbm_depth3 | 0.5000 | 61 | 34 | 27 | 0.7674 | 0.7407 | 0.7407 | 0.7407 | 0.2059 | 27 | 7 | 7 | 20 |
| dhw_storage_return | xgboost_depth3 | 0.5000 | 22 | 12 | 10 | 0.7667 | 0.7778 | 0.7000 | 0.7368 | 0.1667 | 10 | 2 | 3 | 7 |
| dhw_storage_return | random_forest_depth3 | 0.5000 | 22 | 12 | 10 | 0.7583 | 0.8571 | 0.6000 | 0.7059 | 0.0833 | 11 | 1 | 4 | 6 |
| dhw_storage | lightgbm_depth3 | 0.4000 | 61 | 34 | 27 | 0.7527 | 0.7143 | 0.7407 | 0.7273 | 0.2353 | 26 | 8 | 7 | 20 |
| heating_common_only | logistic_balanced | 0.5000 | 26 | 16 | 10 | 0.7500 | 1.0000 | 0.5000 | 0.6667 | 0.0000 | 16 | 0 | 5 | 5 |
| heating_common_only | logistic_balanced | 0.6000 | 26 | 16 | 10 | 0.7500 | 1.0000 | 0.5000 | 0.6667 | 0.0000 | 16 | 0 | 5 | 5 |
| dhw_storage | xgboost_depth3 | 0.4000 | 61 | 34 | 27 | 0.7456 | 0.6667 | 0.8148 | 0.7333 | 0.3235 | 23 | 11 | 5 | 22 |
| heating_common_only | xgboost_depth3 | 0.4000 | 26 | 16 | 10 | 0.7438 | 0.6154 | 0.8000 | 0.6957 | 0.3125 | 11 | 5 | 2 | 8 |

## Threshold Policy 예시
| feature_set | model | fallback_threshold | system_capability_group | selected_threshold | selection_reason | threshold | rows | normal_rows | pre_event_rows | balanced_accuracy | precision | recall | f1 | normal_fpr | tn | fp | fn | tp | rank_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| common13 | dummy_most_frequent | 0.4000 | dhw_return | 0.4000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | dummy_most_frequent | 0.4000 | dhw_storage | 0.3000 | best_available_no_threshold_meets_recall_fpr | 0.3000 | 61.0000 | 34.0000 | 27.0000 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 34.0000 | 0.0000 | 27.0000 | 0.0000 | 0.5000 |
| common13 | dummy_most_frequent | 0.4000 | dhw_storage_return | 0.3000 | best_available_no_threshold_meets_recall_fpr | 0.3000 | 22.0000 | 12.0000 | 10.0000 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 12.0000 | 0.0000 | 10.0000 | 0.0000 | 0.5000 |
| common13 | dummy_most_frequent | 0.4000 | dhw_supply | 0.4000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | dummy_most_frequent | 0.4000 | heating_common_only | 0.3000 | best_available_no_threshold_meets_recall_fpr | 0.3000 | 26.0000 | 16.0000 | 10.0000 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 16.0000 | 0.0000 | 10.0000 | 0.0000 | 0.5000 |
| common13 | dummy_most_frequent | 0.5000 | dhw_return | 0.5000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | dummy_most_frequent | 0.5000 | dhw_storage | 0.3000 | best_available_no_threshold_meets_recall_fpr | 0.3000 | 61.0000 | 34.0000 | 27.0000 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 34.0000 | 0.0000 | 27.0000 | 0.0000 | 0.5000 |
| common13 | dummy_most_frequent | 0.5000 | dhw_storage_return | 0.3000 | best_available_no_threshold_meets_recall_fpr | 0.3000 | 22.0000 | 12.0000 | 10.0000 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 12.0000 | 0.0000 | 10.0000 | 0.0000 | 0.5000 |
| common13 | dummy_most_frequent | 0.5000 | dhw_supply | 0.5000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | dummy_most_frequent | 0.5000 | heating_common_only | 0.3000 | best_available_no_threshold_meets_recall_fpr | 0.3000 | 26.0000 | 16.0000 | 10.0000 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 16.0000 | 0.0000 | 10.0000 | 0.0000 | 0.5000 |
| common13 | dummy_most_frequent | 0.6000 | dhw_return | 0.6000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | dummy_most_frequent | 0.6000 | dhw_storage | 0.3000 | best_available_no_threshold_meets_recall_fpr | 0.3000 | 61.0000 | 34.0000 | 27.0000 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 34.0000 | 0.0000 | 27.0000 | 0.0000 | 0.5000 |
| common13 | dummy_most_frequent | 0.6000 | dhw_storage_return | 0.3000 | best_available_no_threshold_meets_recall_fpr | 0.3000 | 22.0000 | 12.0000 | 10.0000 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 12.0000 | 0.0000 | 10.0000 | 0.0000 | 0.5000 |
| common13 | dummy_most_frequent | 0.6000 | dhw_supply | 0.6000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | dummy_most_frequent | 0.6000 | heating_common_only | 0.3000 | best_available_no_threshold_meets_recall_fpr | 0.3000 | 26.0000 | 16.0000 | 10.0000 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 16.0000 | 0.0000 | 10.0000 | 0.0000 | 0.5000 |
| common13 | extra_trees_depth3 | 0.4000 | dhw_return | 0.4000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | extra_trees_depth3 | 0.4000 | dhw_storage | 0.5000 | best_available_no_threshold_meets_recall_fpr | 0.5000 | 61.0000 | 34.0000 | 27.0000 | 0.8039 | 0.9000 | 0.6667 | 0.7660 | 0.0588 | 32.0000 | 2.0000 | 9.0000 | 18.0000 | 1.4118 |
| common13 | extra_trees_depth3 | 0.4000 | dhw_storage_return | 0.5000 | meets_group_recall_fpr | 0.5000 | 22.0000 | 12.0000 | 10.0000 | 0.7750 | 0.7273 | 0.8000 | 0.7619 | 0.2500 | 9.0000 | 3.0000 | 2.0000 | 8.0000 | 0.9250 |
| common13 | extra_trees_depth3 | 0.4000 | dhw_supply | 0.4000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | extra_trees_depth3 | 0.4000 | heating_common_only | 0.5000 | best_available_no_threshold_meets_recall_fpr | 0.5000 | 26.0000 | 16.0000 | 10.0000 | 0.7688 | 0.8571 | 0.6000 | 0.7059 | 0.0625 | 15.0000 | 1.0000 | 4.0000 | 6.0000 | 1.3062 |
| common13 | extra_trees_depth3 | 0.5000 | dhw_return | 0.5000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | extra_trees_depth3 | 0.5000 | dhw_storage | 0.5000 | best_available_no_threshold_meets_recall_fpr | 0.5000 | 61.0000 | 34.0000 | 27.0000 | 0.8039 | 0.9000 | 0.6667 | 0.7660 | 0.0588 | 32.0000 | 2.0000 | 9.0000 | 18.0000 | 1.4118 |
| common13 | extra_trees_depth3 | 0.5000 | dhw_storage_return | 0.5000 | meets_group_recall_fpr | 0.5000 | 22.0000 | 12.0000 | 10.0000 | 0.7750 | 0.7273 | 0.8000 | 0.7619 | 0.2500 | 9.0000 | 3.0000 | 2.0000 | 8.0000 | 0.9250 |
| common13 | extra_trees_depth3 | 0.5000 | dhw_supply | 0.5000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | extra_trees_depth3 | 0.5000 | heating_common_only | 0.5000 | best_available_no_threshold_meets_recall_fpr | 0.5000 | 26.0000 | 16.0000 | 10.0000 | 0.7688 | 0.8571 | 0.6000 | 0.7059 | 0.0625 | 15.0000 | 1.0000 | 4.0000 | 6.0000 | 1.3062 |
| common13 | extra_trees_depth3 | 0.6000 | dhw_return | 0.6000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | extra_trees_depth3 | 0.6000 | dhw_storage | 0.5000 | best_available_no_threshold_meets_recall_fpr | 0.5000 | 61.0000 | 34.0000 | 27.0000 | 0.8039 | 0.9000 | 0.6667 | 0.7660 | 0.0588 | 32.0000 | 2.0000 | 9.0000 | 18.0000 | 1.4118 |
| common13 | extra_trees_depth3 | 0.6000 | dhw_storage_return | 0.5000 | meets_group_recall_fpr | 0.5000 | 22.0000 | 12.0000 | 10.0000 | 0.7750 | 0.7273 | 0.8000 | 0.7619 | 0.2500 | 9.0000 | 3.0000 | 2.0000 | 8.0000 | 0.9250 |
| common13 | extra_trees_depth3 | 0.6000 | dhw_supply | 0.6000 | insufficient_group_data |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| common13 | extra_trees_depth3 | 0.6000 | heating_common_only | 0.5000 | best_available_no_threshold_meets_recall_fpr | 0.5000 | 26.0000 | 16.0000 | 10.0000 | 0.7688 | 0.8571 | 0.6000 | 0.7059 | 0.0625 | 15.0000 | 1.0000 | 4.0000 | 6.0000 | 1.3062 |

## Candidate Model Package
- path: `C:\3rd_Project\HeatGridAgent\09_실험라인\m1_m2_system_stratified_pre_event\models\m1_m2_system_stratified_pre_event_candidate.joblib`
- status: `global_not_locked_aux_candidates_available`
- 운영 사용 금지: 이번 패키지는 후속 실험 재현용 후보이며, 전체 runtime 모델 잠금은 아니다.

## 다음 작업
1. `dhw_storage`, `heating_common_only`, `dhw_storage_return` 별로 fault label 분포를 다시 본다.
2. system group별로 `report_pre_7d`가 같은 의미인지 window를 재검토한다.
3. DHW 고장은 DHW 전용 sensor/window를 쓰는 보조 pre_event 정의를 따로 만든다.
4. 재설계 후 이번 script를 다시 실행해 같은 기준으로 pass/fail을 비교한다.

## 품질 검증
| quality_check | passed | detail |
| --- | --- | --- |
| base_outputs_exist | True | C:\3rd_Project\HeatGridAgent\09_실험라인\m1_m2_standard_pre_event\outputs |
| candidate_model_saved | True | C:\3rd_Project\HeatGridAgent\09_실험라인\m1_m2_system_stratified_pre_event\models\m1_m2_system_stratified_pre_event_candidate.joblib |
| m1_m2_original_zip_exists | True | C:\3rd_Project\HeatGridAgent\05_데이터셋\PreDist\predist_dataset.zip |
| manufacturer_not_used_as_feature | True | common13 feature list only |
| system_groups_have_audit | True | groups=5 |
| candidate_pass_count | True | 17 |

source commit: `49bc689f24380cc3b0783153c09a878c93d61db5`
