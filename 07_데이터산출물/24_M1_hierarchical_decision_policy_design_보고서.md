# M1 Hierarchical Decision Policy Design Report

## Conclusion
- final_policy_decision: `fault_first_context_augmented_routing`
- fault: predictive gate candidate, using `compact13 + random_forest_balanced_depth3 + threshold 0.5`.
- task: post-event context classifier, not a predictive target.
- activity: overlap/missingness-sensitive candidate signal; use only as supporting context, not a locked predictive label.
- This is not a new 4-class model. It is an explainable routing policy for Agent input.

## Decision Matrix
| policy_name | final_policy_decision | fault_policy | fault_model | fault_final_decision_source | fault_balanced_accuracy | fault_recall | fault_normal_fpr | task_policy | task_semantic_decision | activity_policy | activity_final_decision | activity_missingness_ok | routing_rows | predictive_fault_risk_rows | maintenance_context_event_rows | activity_context_or_candidate_signal_rows | normal_or_monitor_rows | review_required_rows | fault_priority_over_context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hierarchical_m1_decision_policy | fault_first_context_augmented_routing | predictive_gate_candidate | compact13\|random_forest_balanced_depth3\|threshold_0.5 | fault_gate_lock_pending_threshold_review | 0.845455 | 0.890909 | 0.2 | post_event_context_classifier | task_as_event_context_classifier | overlap_sensitive_predictive_candidate | activity_predictive_gate_pending_overlap_review | False | 179 | 56 | 42 | 47 | 34 | 57 | True |

## Operational Labels
| final_operational_label | priority | definition | operator_action |
| --- | --- | --- | --- |
| predictive_fault_risk | 1 | Fault predictive gate is positive. Treat as risk-first routing; context tags remain secondary. | Review risk evidence and prepare inspection/dispatch candidate. |
| maintenance_context_event | 2 | Fault gate is not positive, task post-event context classifier is positive. | Use as maintenance/work context, not advance prediction. |
| activity_context_or_candidate_signal | 3 | Activity pre/post candidate signal is positive, but activity is missingness-sensitive and not locked as predictive. | Treat as review-required context/candidate signal. |
| normal_or_monitor | 4 | No selected fault/task/activity signal is positive. | Monitor normally. |

## Routing Counts
| final_operational_label | rows |
| --- | --- |
| predictive_fault_risk | 56 |
| activity_context_or_candidate_signal | 47 |
| maintenance_context_event | 42 |
| normal_or_monitor | 34 |

## Known Class vs Final Routing
| known_class | final_operational_label | rows | audit_type |
| --- | --- | --- | --- |
| activity | activity_context_or_candidate_signal | 47 | known_class_by_final_label |
| fault | normal_or_monitor | 6 | known_class_by_final_label |
| fault | predictive_fault_risk | 49 | known_class_by_final_label |
| normal | normal_or_monitor | 28 | known_class_by_final_label |
| normal | predictive_fault_risk | 7 | known_class_by_final_label |
| task | maintenance_context_event | 42 | known_class_by_final_label |

## Review Required Rules
`review_required=True` when any of the following is true:
- activity candidate/context signal is positive, because activity is missingness-sensitive.
- fault probability is near the threshold range [0.45, 0.55].
- multiple selected signals are positive and the policy had to prioritize fault over context.

## Quality Checks
| check | pass |
| --- | --- |
| fault_threshold_0_5_reproduced | True |
| task_decision_matches_22 | True |
| activity_decision_matches_23 | True |
| one_label_per_row | True |
| fault_priority_check | True |
| review_required_has_policy_conditions | True |

## Limitations
- Fault is still `fault_gate_lock_pending_threshold_review`, so this policy should be presented as M1 routing, not production-ready automation.
- Task and activity are context/candidate signals. They should not be described as advance prediction success.
- Some event types are scored only by their relevant validated gate/context classifier; absent probabilities mean not evaluated by that policy layer.

## Next Step
Use this hierarchy as the Agent input contract: risk first, then context tags, then review-required routing.
