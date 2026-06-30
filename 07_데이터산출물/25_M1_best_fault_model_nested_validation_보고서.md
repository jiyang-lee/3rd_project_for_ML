# M1 Best Fault Model Nested Validation Report

## Conclusion
- final_decision: `keep_existing_fault_gate`
- selected_fault_policy: `legacy_fault_gate_retained`
- optimization: fault recall first, with normal FPR primary limit `0.2` and relaxed limit `0.25`.
- validation: nested StratifiedGroupKFold by `substation_id`.
- task/activity policies are unchanged from the hierarchical policy.

## Decision Matrix
| final_decision | selected_fault_policy | optimization_goal | validation | selected_fault_recall | selected_balanced_accuracy | selected_normal_fpr | selected_macro_f1 | selected_fold_ba_std | baseline_fault_recall | baseline_balanced_accuracy | baseline_normal_fpr | baseline_macro_f1 | baseline_fold_ba_std | recall_improved | fpr_primary_pass | fpr_relaxed_pass | fold_stable | outer_selected_candidates |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| keep_existing_fault_gate | legacy_fault_gate_retained | maximize_fault_recall_subject_to_normal_fpr | nested_stratified_group_cv_by_substation | 0.945455 | 0.82987 | 0.285714 | 0.84127 | 0.0877988 | 0.890909 | 0.845455 | 0.2 | 0.847239 | 0.0854526 | True | False | False | True | ensemble_top3_interpretable\|compact20_main__missing_indicator__extra_trees_balanced_depth2\|compact20_main__base__random_forest_balanced_depth2\|compact20_main__base__extra_trees_balanced_depth4\|compact13__missing_indicator__logistic_balanced_C1.0 |

## Aggregate Metrics
| metric_type | outer_fold | candidate_id | threshold | accuracy | balanced_accuracy | macro_f1 | roc_auc | normal_precision | normal_recall | normal_f1 | fault_precision | fault_recall | fault_f1 | normal_support | fault_support | normal_fpr | tn | fp | fn | tp | fold_balanced_accuracy_std | fold_fault_recall_std | fold_normal_fpr_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aggregate_baseline_fixed | all | legacy_compact13_rf_depth3 | 0.5 | 0.788889 | 0.775325 | 0.776733 | 0.883636 | 0.735294 | 0.714286 | 0.724638 | 0.821429 | 0.836364 | 0.828829 | 35 | 55 | 0.285714 | 25 | 10 | 9 | 46 | 0.0950004 | 0.120605 | 0.155966 |
| aggregate_selected_nested | all | mixed_by_fold | inner_selected | 0.855556 | 0.82987 | 0.84127 | 0.865455 | 0.892857 | 0.714286 | 0.793651 | 0.83871 | 0.945455 | 0.888889 | 35 | 55 | 0.285714 | 25 | 10 | 3 | 52 | 0.0877988 | 0.0727273 | 0.157647 |
| aggregate_21_reference_baseline | all | reference_21_compact13_rf_depth3 | 0.5 | 0.855556 | 0.845455 | 0.847239 | 0.881039 | 0.823529 | 0.8 | 0.811594 | 0.875 | 0.890909 | 0.882883 | 35 | 55 | 0.2 | 28 | 7 | 6 | 49 | 0.0854526 | 0.0680301 | 0.144121 |

## Selected Outer Fold Candidates
| outer_fold | candidate_id | feature_set | feature_variant | model_name | inner_selected_threshold | inner_constraint_level | inner_fault_recall | inner_normal_fpr | inner_balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ensemble_top3_interpretable | ensemble | top3_average | ensemble_top3_average | 0.4 | primary_fpr | 0.931818 | 0.137931 | 0.896944 |
| 2 | compact20_main__missing_indicator__extra_trees_balanced_depth2 | compact20_main | missing_indicator | extra_trees_balanced_depth2 | 0.45 | primary_fpr | 0.909091 | 0.185185 | 0.861953 |
| 3 | compact20_main__base__random_forest_balanced_depth2 | compact20_main | base | random_forest_balanced_depth2 | 0.5 | primary_fpr | 0.886364 | 0.178571 | 0.853896 |
| 4 | compact20_main__base__extra_trees_balanced_depth4 | compact20_main | base | extra_trees_balanced_depth4 | 0.45 | primary_fpr | 0.954545 | 0.178571 | 0.887987 |
| 5 | compact13__missing_indicator__logistic_balanced_C1.0 | compact13 | missing_indicator | logistic_balanced_C1.0 | 0.4 | primary_fpr | 0.863636 | 0.178571 | 0.842532 |

## Calibration Audit Summary
| outer_fold | candidate_id | calibration_method | threshold | accuracy | balanced_accuracy | macro_f1 | roc_auc | normal_precision | normal_recall | normal_f1 | fault_precision | fault_recall | fault_f1 | normal_support | fault_support | normal_fpr | tn | fp | fn | tp | balanced_accuracy_mean | fault_recall_mean | normal_fpr_mean | macro_f1_mean | fold_balanced_accuracy_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | selected_nested_by_fold | isotonic | fold_calibrated |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.724675 | 0.763636 | 0.314286 | 0.695564 | 0.0867898 |
| all | selected_nested_by_fold | raw | fold_calibrated |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.825108 | 0.945455 | 0.295238 | 0.834385 | 0.0877988 |
| all | selected_nested_by_fold | sigmoid | fold_calibrated |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.606494 | 0.327273 | 0.114286 | 0.500479 | 0.0801205 |

## Error Audit
- selected nested false positives: 10
- selected nested false negatives: 3
- saved file: `m1_best_fault_model_error_audit.csv`

## Hierarchical Policy Update
| source_policy | fault_policy_update | best_fault_model_decision | task_policy_unchanged | activity_policy_unchanged | selected_fault_recall | selected_normal_fpr | baseline_fault_recall | baseline_normal_fpr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m1_hierarchical_policy | legacy_fault_gate_retained | keep_existing_fault_gate | post_event_context_classifier | overlap_sensitive_predictive_candidate | 0.945455 | 0.285714 | 0.890909 | 0.2 |

## Quality Checks
| check | pass |
| --- | --- |
| metric_recompute | True |
| outer_group_overlap_zero | True |
| normal_35_retained | True |
| fault_55_retained | True |
| baseline_wrapper_reproduced_existing | True |
| no_metadata_features | True |
| hierarchical_task_activity_unchanged | True |

## Interpretation
- If `final_decision` is `best_fault_model_locked`, replace the 24번 fault gate with the selected nested model family.
- If `final_decision` is `best_fault_model_tradeoff_candidate`, report the recall/FPR tradeoff and keep operator review required.
- If `final_decision` is `keep_existing_fault_gate`, retain the 21번 fault gate because the larger search did not beat it reliably.
