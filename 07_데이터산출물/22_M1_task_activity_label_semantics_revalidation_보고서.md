# M1 Task/Activity Label Semantics Revalidation Report

## Conclusion
- final_decision: `task/activity_as_event_context_classifiers`
- task_decision: `task_as_event_context_classifier`
- activity_decision: `activity_predictive_candidate_overlap_sensitive`
- primary baseline: `compact13 + random_forest_balanced_depth3 + threshold 0.5`
- task interpretation: task passes only on the post 1d window, so it should be described as an event-context classifier, not advance prediction.
- activity interpretation: activity passes on pre 1d and post 1d, but the no-overlap reference fails; keep it as an overlap-sensitive predictive candidate.

## Semantic Criteria
| criterion | value |
| --- | --- |
| balanced_accuracy | >= 0.75 |
| target_recall | >= 0.8 |
| normal_fpr | <= 0.25 |
| target_overlap_rate | <= 0.1 |
| fold_balanced_accuracy_std | <= 0.15 |
| fold_target_recall_std | <= 0.25 |
| fold_normal_fpr_std | <= 0.3 |
| group overlap | 0 |

## Primary Baseline Results
| target_class | dataset | window_direction | window_days | balanced_accuracy | target_recall | normal_fpr | target_overlap_rate | fold_balanced_accuracy_std | semantic_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activity | activity_no_overlap | no_overlap | 7d_no_overlap | 0.736957 | 0.673913 | 0.2 | 0 | 0.149797 | False |
| activity | activity_post_1d | post | 1d | 1 | 1 | 0 | 0.0869565 | 0 | True |
| activity | activity_post_3d | post | 3d | 0.589441 | 0.521739 | 0.342857 | 0.108696 | 0.136876 | False |
| activity | activity_post_all | post | 7d_reference | 0.604348 | 0.608696 | 0.4 | 0.108696 | 0.0558411 | False |
| activity | activity_pre_1d | pre | 1d | 1 | 1 | 0 | 0.0425532 | 0 | True |
| activity | activity_pre_3d | pre | 3d | 0.758055 | 0.744681 | 0.228571 | 0.0851064 | 0.0764257 | False |
| activity | activity_pre_all | pre | 7d_reference | 0.775988 | 0.723404 | 0.171429 | 0.0851064 | 0.0636382 | False |
| task | task_no_overlap | no_overlap | 7d_no_overlap | 0.652124 | 0.675676 | 0.371429 | 0 | 0.170559 | False |
| task | task_post_1d | post | 1d | 1 | 1 | 0 | 0.047619 | 0 | True |
| task | task_post_3d | post | 3d | 0.716667 | 0.690476 | 0.257143 | 0.0714286 | 0.0938022 | False |
| task | task_post_all | post | 7d_reference | 0.722997 | 0.731707 | 0.285714 | 0.097561 | 0.0397731 | False |
| task | task_pre_1d | pre | 1d | 1 | 1 | 0 | 0.4 | 0 | False |
| task | task_pre_3d | pre | 3d | 0.785714 | 0.8 | 0.228571 | 0.6 | 0.110571 | False |
| task | task_pre_all | pre | 7d_reference | 0.750579 | 0.72973 | 0.228571 | 0.72973 | 0.0940411 | False |

## Semantics Decision Matrix
| target_class | best_pre_candidate | best_pre_dataset | best_pre_balanced_accuracy | best_pre_target_recall | best_pre_normal_fpr | best_pre_target_overlap_rate | best_post_candidate | best_post_dataset | best_post_balanced_accuracy | best_post_target_recall | best_post_normal_fpr | best_post_target_overlap_rate | best_no_overlap_candidate | best_no_overlap_dataset | best_no_overlap_balanced_accuracy | best_no_overlap_target_recall | best_no_overlap_normal_fpr | pre_pass | post_pass | no_overlap_pass | overlap_sensitive | semantic_decision | recommended_usage | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activity | activity_pre_1d\|compact13\|random_forest_balanced_depth3\|t=0.5 | activity_pre_1d | 1 | 1 | 0 | 0.0425532 | activity_post_1d\|compact13\|random_forest_balanced_depth3\|t=0.5 | activity_post_1d | 1 | 1 | 0 | 0.0869565 | activity_no_overlap\|compact13\|random_forest_balanced_depth3\|t=0.5 | activity_no_overlap | 0.736957 | 0.673913 | 0.2 | True | True | False | True | activity_predictive_candidate_overlap_sensitive | predictive_candidate_needs_overlap_review | pre window passes, but no-overlap reference does not pass; keep as predictive candidate with reliability caveat. |
| task | task_pre_1d\|compact13\|random_forest_balanced_depth3\|t=0.5 | task_pre_1d | 1 | 1 | 0 | 0.4 | task_post_1d\|compact13\|random_forest_balanced_depth3\|t=0.5 | task_post_1d | 1 | 1 | 0 | 0.047619 | task_no_overlap\|compact13\|random_forest_balanced_depth3\|t=0.5 | task_no_overlap | 0.652124 | 0.675676 | 0.371429 | False | True | False | True | task_as_event_context_classifier | post_event_context_classifier | post window passes while pre window does not; do not describe this as advance prediction. |

## Dataset Quality Summary
| dataset | target_class | rows | normal_rows | target_rows | substation_count | target_overlap_rows | target_overlap_rate | normal_collision_rows | coverage_min | coverage_median | window_direction | window_days | compact13_feature_any_missing_rate | expanded154_feature_any_missing_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| task_pre_all | task | 72 | 35 | 37 | 30 | 27 | 0.72973 | 0 | 1 | 1 | pre | 7d_reference | 0.230769 | 0.181818 |
| task_post_all | task | 76 | 35 | 41 | 31 | 4 | 0.097561 | 0 | 0.982143 | 1 | post | 7d_reference | 0.230769 | 0.123377 |
| task_no_overlap | task | 72 | 35 | 37 | 31 | 0 | 0 | 0 | 0.982143 | 1 | no_overlap | 7d_no_overlap | 0.230769 | 0.123377 |
| activity_pre_all | activity | 82 | 35 | 47 | 27 | 4 | 0.0851064 | 0 | 0.99504 | 1 | pre | 7d_reference | 0.307692 | 0.584416 |
| activity_post_all | activity | 81 | 35 | 46 | 27 | 5 | 0.108696 | 0 | 0.99504 | 1 | post | 7d_reference | 0.307692 | 0.584416 |
| activity_no_overlap | activity | 81 | 35 | 46 | 27 | 0 | 0 | 0 | 0.99504 | 1 | no_overlap | 7d_no_overlap | 0.307692 | 0.584416 |
| task_pre_3d | task | 75 | 35 | 40 | 31 | 24 | 0.6 | 1 | 0.983796 | 1 | pre | 3d | 0.230769 | 0.181818 |
| task_pre_1d | task | 75 | 35 | 40 | 31 | 16 | 0.4 | 0 | 0.986111 | 1 | pre | 1d | 0.769231 | 0.350649 |
| task_post_3d | task | 77 | 35 | 42 | 31 | 3 | 0.0714286 | 0 | 0.958333 | 1 | post | 3d | 0.230769 | 0.123377 |
| task_post_1d | task | 77 | 35 | 42 | 31 | 2 | 0.047619 | 0 | 1 | 1 | post | 1d | 0.769231 | 0.350649 |
| activity_pre_3d | activity | 82 | 35 | 47 | 27 | 4 | 0.0851064 | 0 | 0.988426 | 1 | pre | 3d | 0.307692 | 0.584416 |
| activity_pre_1d | activity | 82 | 35 | 47 | 27 | 2 | 0.0425532 | 0 | 0.965278 | 1 | pre | 1d | 0.615385 | 0.649351 |
| activity_post_3d | activity | 81 | 35 | 46 | 27 | 5 | 0.108696 | 0 | 0.997685 | 1 | post | 3d | 0.307692 | 0.584416 |
| activity_post_1d | activity | 81 | 35 | 46 | 27 | 4 | 0.0869565 | 0 | 0.993056 | 1 | post | 1d | 0.615385 | 0.649351 |

## Error Audit
- Saved primary-baseline core-candidate errors to `m1_task_activity_semantics_error_audit.csv`.
- error_audit_rows: 139

## Feature Importance
- Saved full-dataset-fit audit-only importance to `m1_task_activity_semantics_feature_importance.csv`.
- feature_importance_rows: 260
- This file is for interpretation only, not model selection.

## Quality Checks
| check | pass/detail |
| --- | --- |
| metric_recompute | True |
| normal_35_retained_all_datasets | True |
| group_overlap_zero_all_metrics | True |
| source_metrics_rows | 252 |
| error_audit_rows | 139 |
| feature_importance_rows | 260 |

## Next Steps
1. Treat task as `post_event_context_classifier` and avoid calling it advance prediction.
2. Keep activity as a predictive candidate, but do not lock it as a final predictive gate until overlap/relabel audit is complete.
3. Keep fault at `fault_gate_lock_pending_threshold_review`.
4. Redesign final multiclass strategy as fault predictive gate plus task/activity context classifiers.
