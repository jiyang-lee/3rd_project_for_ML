# M1 Specialist Report

This report compares the M1-only current best priority with the 3rd_project_for_ML M1 specialist priority.

## Scope

- manufacturer filter: `manufacturer 1`
- This package is fitted and scored on M1 rows only.
- `priority_score` and `priority_level` are promoted to `m1_hybrid_priority_score` / `m1_hybrid_priority_level` for the official M1 agent card.
- The original current-best priority is preserved as `current_best_priority_score` and `current_best_priority_level`.
- `m1_specialist_*` columns are preserved as parallel 3rd_project_for_ML evidence.

## Thresholds

- m1_specialist high threshold: 77.500
- m1_specialist urgent threshold: 92.500
- m1_hybrid high threshold: 67.500
- m1_hybrid urgent threshold: 82.500

## Holdout Metrics
| policy | split | metric_scope | row_count | precision | recall | false_positive_rate | tp | fp | fn | tn | mean_score | fault_events | detected_fault_events | fault_event_recall | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_priority | holdout | row | 183.0 | 0.725 | 0.7532467532467533 | 0.20754716981132076 | 58.0 | 22.0 | 19.0 | 84.0 | 55.04589398907104 |  |  |  |  |
| current_best_priority | holdout | fault_event |  |  |  |  |  |  |  |  |  | 8.0 | 7.0 | 0.875 | normal-event false alarm is not computed in current best contract; use row false_positive_rate as comparable guardrail |
| m1_specialist_priority | holdout | row | 183.0 | 0.64 | 0.4155844155844156 | 0.16981132075471697 | 32.0 | 18.0 | 45.0 | 88.0 | 58.05319207467691 |  |  |  |  |
| m1_specialist_priority | holdout | fault_event |  |  |  |  |  |  |  |  |  | 8.0 | 7.0 | 0.875 | normal-event false alarm is not computed in current best contract; use row false_positive_rate as comparable guardrail |
| m1_hybrid_priority | holdout | row | 183.0 | 0.896551724137931 | 0.6753246753246753 | 0.05660377358490566 | 52.0 | 6.0 | 25.0 | 100.0 | 56.098448319033096 |  |  |  |  |
| m1_hybrid_priority | holdout | fault_event |  |  |  |  |  |  |  |  |  | 8.0 | 7.0 | 0.875 | normal-event false alarm is not computed in current best contract; use row false_positive_rate as comparable guardrail |