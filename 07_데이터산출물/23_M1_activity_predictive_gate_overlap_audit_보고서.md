# M1 Activity Predictive Gate Overlap Audit Report

## Conclusion
- final_decision: `activity_predictive_gate_pending_overlap_review`
- recommended_usage: `overlap_sensitive_predictive_candidate`
- reason: pre_1d passes, but strict no-overlap or missingness stress test prevents locking.
- primary baseline: `compact13 + random_forest_balanced_depth3 + threshold 0.5`
- lock rule: strict pre-1d no-overlap must pass BA >= 0.75, recall >= 0.8, normal FPR <= 0.25, fold BA std <= 0.15, and missingness-only BA < 0.65.

## Decision Matrix
| target_class | final_decision | recommended_usage | reason | activity_pre_1d_ba | activity_pre_1d_recall | activity_pre_1d_normal_fpr | activity_pre_1d_strict_no_overlap_ba | activity_pre_1d_strict_no_overlap_recall | activity_pre_1d_strict_no_overlap_normal_fpr | activity_pre_1d_strict_no_overlap_fold_ba_std | activity_post_1d_ba | activity_post_1d_recall | activity_post_1d_normal_fpr | activity_no_overlap_ba | activity_no_overlap_recall | activity_no_overlap_normal_fpr | missingness_only_pre_1d_ba | missingness_only_pre_1d_strict_ba | strict_pass | missingness_ok | pre_post_probability_spearman | pre_post_top5_feature_overlap | proximity_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activity | activity_predictive_gate_pending_overlap_review | overlap_sensitive_predictive_candidate | pre_1d passes, but strict no-overlap or missingness stress test prevents locking. | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 0.736957 | 0.673913 | 0.2 | 1 | 1 | True | False | -0.0544558 | 5 | False |

## Dataset Summary
| dataset | rows | normal_rows | activity_rows | substation_count | activity_substation_count | target_overlap_rows | target_overlap_rate | normal_collision_rows | coverage_min | coverage_median | compact13_any_missing_rate | compact13_cell_missing_rate | window_policies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activity_pre_1d | 82 | 35 | 47 | 27 | 19 | 2 | 0.0425532 | 0 | 0.965278 | 1 | 0.615385 | 0.333959 | activity_pre_1d |
| activity_pre_1d_strict_no_overlap | 80 | 35 | 45 | 27 | 19 | 0 | 0 | 0 | 0.965278 | 1 | 0.615385 | 0.327885 | activity_pre_1d |
| activity_post_1d | 81 | 35 | 46 | 27 | 19 | 4 | 0.0869565 | 0 | 0.993056 | 1 | 0.615385 | 0.322887 | activity_post_1d |
| activity_post_1d_strict_no_overlap | 77 | 35 | 42 | 27 | 19 | 0 | 0 | 0 | 1 | 1 | 0.615385 | 0.310689 | activity_post_1d |
| activity_no_overlap | 81 | 35 | 46 | 27 | 19 | 0 | 0 | 0 | 0.99504 | 1 | 0.307692 | 0.0978158 | activity_post_7d\|activity_pre_7d |

## Primary Stress Test Metrics
| dataset | feature_variant | model | threshold | balanced_accuracy | activity_recall | normal_fpr | fold_balanced_accuracy_std | fold_activity_recall_std | fold_normal_fpr_std | feature_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activity_no_overlap | compact13 | random_forest_balanced_depth3 | 0.5 | 0.736957 | 0.673913 | 0.2 | 0.133983 | 0.0985558 | 0.218426 | 13 |
| activity_no_overlap | compact13_high_missing_removed | random_forest_balanced_depth3 | 0.5 | 0.736957 | 0.673913 | 0.2 | 0.133983 | 0.0985558 | 0.218426 | 13 |
| activity_no_overlap | compact13_indicator | random_forest_balanced_depth3 | 0.5 | 0.77236 | 0.630435 | 0.0857143 | 0.0752153 | 0.146164 | 0.114286 | 13 |
| activity_no_overlap | missingness_only | random_forest_balanced_depth3 | 0.5 | 0.782609 | 0.565217 | 0 | 0.0623907 | 0.124781 | 0 | 13 |
| activity_post_1d | compact13 | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |
| activity_post_1d | compact13_high_missing_removed | random_forest_balanced_depth3 | 0.5 | 0.719876 | 0.782609 | 0.342857 | 0.0959944 | 0.126759 | 0.140052 | 6 |
| activity_post_1d | compact13_indicator | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |
| activity_post_1d | missingness_only | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |
| activity_post_1d_strict_no_overlap | compact13 | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |
| activity_post_1d_strict_no_overlap | compact13_high_missing_removed | random_forest_balanced_depth3 | 0.5 | 0.666667 | 0.761905 | 0.428571 | 0.0789987 | 0.130171 | 0.0897685 | 6 |
| activity_post_1d_strict_no_overlap | compact13_indicator | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |
| activity_post_1d_strict_no_overlap | missingness_only | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |
| activity_pre_1d | compact13 | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |
| activity_pre_1d | compact13_high_missing_removed | random_forest_balanced_depth3 | 0.5 | 0.718845 | 0.723404 | 0.285714 | 0.0716212 | 0.124418 | 0.126527 | 6 |
| activity_pre_1d | compact13_indicator | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |
| activity_pre_1d | missingness_only | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |
| activity_pre_1d_strict_no_overlap | compact13 | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |
| activity_pre_1d_strict_no_overlap | compact13_high_missing_removed | random_forest_balanced_depth3 | 0.5 | 0.74127 | 0.711111 | 0.228571 | 0.109637 | 0.112349 | 0.157305 | 6 |
| activity_pre_1d_strict_no_overlap | compact13_indicator | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |
| activity_pre_1d_strict_no_overlap | missingness_only | random_forest_balanced_depth3 | 0.5 | 1 | 1 | 0 | 0 | 0 | 0 | 13 |

## No-overlap Failure Audit
- `activity_no_overlap` primary errors: 22 rows
- false negatives: 15
- false positives: 7
- saved file: `m1_activity_predictive_gate_error_audit.csv`

## Pre/Post Proximity
| check | value |
| --- | --- |
| common pre/post activity events | 46 |
| pre/post probability spearman | -0.0544558 |
| pre/post top5 feature overlap | 5 |
| proximity_high | False |

## Quality Checks
| check | pass/detail |
| --- | --- |
| metric_recompute | True |
| fold_group_overlap_zero | True |
| normal_35_all_datasets | True |
| pre_1d_22_reproduced | True |
| decision_written | True |

## Next Steps
1. If decision is `activity_predictive_gate_locked`, use activity as a predictive gate in the hierarchical design.
2. If decision is `activity_predictive_gate_pending_overlap_review`, keep activity as a candidate but do not claim final advance prediction.
3. If decision is `activity_context_classifier_only`, move activity beside task as an event-context classifier.
4. Fault and task remain unchanged: fault is `fault_gate_lock_pending_threshold_review`, task is `post_event_context_classifier`.
