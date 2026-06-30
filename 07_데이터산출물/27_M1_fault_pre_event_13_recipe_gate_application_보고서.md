# M1 Fault Pre-Event Gate 13번 Recipe 적용 보고서

## 결론
- final_decision: `fault_pre_event_13_recipe_applied_with_fixed_eval_caveat`
- fault gate recipe: `expanded_compact13_logistic_balanced_threshold_0.6`
- task/activity 정책은 변경하지 않는다.
- 13번은 `strict_no_event20 fixed eval 49행 + 확장학습` 기반이므로, 25번 `fault_no_overlap 90행` nested search와 직접 동일 평가로 비교하지 않는다.

## 적용 Recipe
| 항목 | 값 |
| --- | --- |
| target | fault pre-event risk / efd_possible positive |
| window | report/fault/event 이전 7일 |
| feature | compact13_overlap 13개 |
| model | SimpleImputer(median) + StandardScaler + LogisticRegression(class_weight="balanced") |
| threshold | 0.6 |
| training | fixed_eval + accepted weak_positive + accepted candidate_normal |

## Decision Matrix
| final_decision | fault_gate_recipe | target_interpretation | fixed_eval_rows | normal_rows | positive_rows | expanded_train_rows_full | feature_set | feature_count | threshold | balanced_accuracy | recall | normal_fpr | false_positive_count | false_negative_count | sensitivity_balanced_accuracy | sensitivity_recall | sensitivity_normal_fpr | reference_13_balanced_accuracy | best25_decision | best25_baseline_recall | best25_baseline_normal_fpr | main_13_reproduced | sensitivity_13_reproduced | group_overlap_zero | hard_normal_35_48_fp_zero | weak_positive_coverage_ok | candidate_normal_overlap_ok | feature_leakage_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fault_pre_event_13_recipe_applied_with_fixed_eval_caveat | expanded_compact13_logistic_balanced_threshold_0.6 | fault_pre_event_risk_from_efd_possible | 49 | 35 | 14 | 131 | compact13_overlap | 13 | 0.6 | 0.85 | 0.785714 | 0.0857143 | 3 | 3 | 0.862554 | 0.785714 | 0.0606061 | 0.828571 | keep_existing_fault_gate | 0.890909 | 0.2 | True | True | True | True | True | True | True |

## Dataset Summary
| pool_role | candidate_type | label | y | rows | substation_count | coverage_min | coverage_median | feature_set | feature_count | model_recipe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expansion_candidate | candidate_normal | candidate_normal | 0 | 70 | 35 | 0.953373 | 1 | compact13_overlap | 13 | expanded_compact13_logistic_balanced_threshold_0.6 |
| expansion_candidate | weak_positive | efd_possible | 1 | 12 | 8 | 1 | 1 | compact13_overlap | 13 | expanded_compact13_logistic_balanced_threshold_0.6 |
| fixed_eval | fixed_eval | efd_possible | 1 | 14 | 14 | 0.99504 | 1 | compact13_overlap | 13 | expanded_compact13_logistic_balanced_threshold_0.6 |
| fixed_eval | fixed_eval | normal | 0 | 35 | 22 | 1 | 1 | compact13_overlap | 13 | expanded_compact13_logistic_balanced_threshold_0.6 |

## Metric Summary
| strategy | evaluation_scope | fold | n | normal_n | positive_n | balanced_accuracy | precision | recall | f1 | false_positive_count | false_negative_count | false_positive_rate | hard_normal_35_48_fp_count | review_required_19_68_fp_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dummy_most_frequent | main_all_49 | all | 49 | 35 | 14 | 0.5 | 0 | 0 | 0 | 0 | 14 | 0 | 0 | 0 |
| dummy_most_frequent | sensitivity_exclude_review_required_19_68 | all | 47 | 33 | 14 | 0.5 | 0 | 0 | 0 | 0 | 14 | 0 | 0 | 0 |
| expanded_compact13 | main_all_49 | all | 49 | 35 | 14 | 0.85 | 0.785714 | 0.785714 | 0.785714 | 3 | 3 | 0.0857143 | 0 | 1 |
| expanded_compact13 | sensitivity_exclude_review_required_19_68 | all | 47 | 33 | 14 | 0.862554 | 0.846154 | 0.785714 | 0.814815 | 2 | 3 | 0.0606061 | 0 | 0 |
| reference_compact13 | main_all_49 | all | 49 | 35 | 14 | 0.828571 | 0.833333 | 0.714286 | 0.769231 | 2 | 4 | 0.0571429 | 0 | 1 |
| reference_compact13 | sensitivity_exclude_review_required_19_68 | all | 47 | 33 | 14 | 0.841991 | 0.909091 | 0.714286 | 0.8 | 1 | 4 | 0.030303 | 0 | 0 |

## 25번과의 관계
- 25번 결론은 `keep_existing_fault_gate`이며, RF 기준 fault gate를 유지한다는 검증이었다.
- 이번 27번은 사용자가 지정한 13번 pre-event recipe를 fault gate 후보로 적용하는 별도 검증이다.
- 따라서 27번은 25번을 폐기하지 않고, `fault pre-event gate`의 구현 recipe를 13번 방식으로 문서화/검증한다.

## Error Audit
- expanded_compact13 false positives: 3
- expanded_compact13 false negatives: 3
- hard normal 35/48 false positives: 0
- saved file: `m1_fault_pre_event_13_recipe_error_audit.csv`

## Hierarchical Policy Update
| source_policy | fault_policy_previous | fault_policy_update | fault_policy_decision | fault_probability_column | fault_prediction_column | final_fault_label | task_policy_unchanged | activity_policy_unchanged | task_activity_pre_event_applied | policy_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m1_hierarchical_policy | compact13\|random_forest_balanced_depth3\|threshold_0.5 | expanded_compact13_logistic_balanced\|threshold_0.6 | fault_pre_event_13_recipe_applied_with_fixed_eval_caveat | fault_pre_event_probability_13_recipe | fault_pre_event_pred_13_recipe | predictive_fault_risk | post_event_context_classifier | overlap_sensitive_predictive_candidate | False | 13_expanded_compact13_pre_event_gate_threshold_0.6 |

## Quality Checks
| check | pass |
| --- | --- |
| main_13_reproduced | True |
| sensitivity_13_reproduced | True |
| group_overlap_zero | True |
| fixed_eval_49_retained | True |
| normal_35_retained | True |
| positive_14_retained | True |
| accepted_weak_positive_coverage_ge_0_95 | True |
| accepted_candidate_normal_no_overlap | True |
| compact13_only | True |
| feature_leakage_ok | True |
| hierarchy_task_activity_unchanged | True |

## 해석
- fault에는 pre-event gate를 붙인다.
- task는 post-event context classifier로 유지한다.
- activity는 overlap/missingness-sensitive candidate signal로 유지한다.
- 13번 recipe는 fixed eval 기준에서 재현됐고, 운영 적용 전에는 25번 기준 데이터셋과 평가 기준 차이를 caveat로 유지한다.
