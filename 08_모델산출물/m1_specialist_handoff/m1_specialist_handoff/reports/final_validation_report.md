# Final Validation Report

## Current Active Contract
- Official agent `priority_score` and `priority_level` are M1 hybrid priority outputs.
- M1 hybrid priority = 0.65 * current-best priority + 0.35 * M1 specialist priority.
- Original current-best priority is preserved as `current_best_priority_score` and `current_best_priority_level`.
- `m1_specialist_*` fields are active evidence fields, not standalone replacements for risk or leadtime.

## Source Trace
- [current best] Mahalanobis + IsolationForest anomaly, risk, leadtime, priority body
- [M1 specialist] fault/task/activity/pre-event gate, fault group, review flag

## Run Metadata
- generated_at_utc: 2026-07-02T02:53:23.235600+00:00
- source_best_root: C:\Project3\HeatGrid_Agent\best

## Row Reconciliation
| source_stage | target_stage | source_rows | target_rows | source_duplicate_keys | target_duplicate_keys | missing_from_target | missing_pre_fault | missing_normal | missing_label_distribution | missing_split_distribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| canonical_windows | priority_scores | 1252 | 1226 | 0 | 0 | 26 | 26 | 0 | pre_fault=26 | train=23; validation=3 |
| canonical_windows | agent_card | 1252 | 1226 | 0 | 0 | 26 | 26 | 0 | pre_fault=26 | train=23; validation=3 |
| priority_scores | merged_scores | 1226 | 1226 | 0 | 0 | 0 | 0 | 0 |  |  |
| priority_scores | agent_card | 1226 | 1226 | 0 | 0 | 0 | 0 | 0 |  |  |
| agent_card | canonical_windows | 1226 | 1252 | 0 | 0 | 0 | 0 | 0 |  |  |

## Threshold Sweep Sample
| threshold | tp | fp | fn | tn | precision | recall | f1 | false_positive_rate | score_name |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.1 | 295 | 931 | 0 | 0 | 0.2406199021207178 | 1.0 | 0.3879026955950033 | 1.0 | anomaly_ensemble_score |
| 0.2 | 295 | 931 | 0 | 0 | 0.2406199021207178 | 1.0 | 0.3879026955950033 | 1.0 | anomaly_ensemble_score |
| 0.3 | 295 | 931 | 0 | 0 | 0.2406199021207178 | 1.0 | 0.3879026955950033 | 1.0 | anomaly_ensemble_score |
| 0.4 | 295 | 907 | 0 | 24 | 0.2454242928452579 | 1.0 | 0.3941215764863059 | 0.97422126745435 | anomaly_ensemble_score |
| 0.5 | 278 | 605 | 17 | 326 | 0.3148357870894677 | 0.9423728813559322 | 0.4719864176570458 | 0.6498388829215896 | anomaly_ensemble_score |
| 0.6 | 206 | 356 | 89 | 575 | 0.3665480427046263 | 0.6983050847457627 | 0.4807467911318553 | 0.3823845327604726 | anomaly_ensemble_score |
| 0.7000000000000001 | 161 | 200 | 134 | 731 | 0.445983379501385 | 0.5457627118644067 | 0.4908536585365853 | 0.2148227712137486 | anomaly_ensemble_score |
| 0.8 | 130 | 127 | 165 | 804 | 0.5058365758754864 | 0.4406779661016949 | 0.4710144927536231 | 0.1364124597207304 | anomaly_ensemble_score |
| 0.9 | 118 | 108 | 177 | 823 | 0.5221238938053098 | 0.4 | 0.4529750479846449 | 0.1160042964554242 | anomaly_ensemble_score |
| 0.1 | 295 | 241 | 0 | 690 | 0.5503731343283582 | 1.0 | 0.7099879663056559 | 0.2588614393125671 | risk_score |
| 0.2 | 291 | 161 | 4 | 770 | 0.6438053097345132 | 0.9864406779661016 | 0.7791164658634536 | 0.1729323308270676 | risk_score |
| 0.3 | 285 | 118 | 10 | 813 | 0.707196029776675 | 0.9661016949152542 | 0.816618911174785 | 0.1267454350161117 | risk_score |

## Active Policy Ablation
| variant | tp | fp | fn | tn | precision | recall | false_positive_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official_anomaly_evidence_event | 60 | 94 | 235 | 837 | 0.3896103896103896 | 0.2033898305084746 | 0.1009667024704618 |
| risk_high_or_critical | 220 | 12 | 75 | 919 | 0.9482758620689656 | 0.7457627118644068 | 0.0128893662728249 |
| m1_specialist_high_or_urgent | 97 | 124 | 198 | 807 | 0.4389140271493212 | 0.3288135593220339 | 0.1331901181525241 |
| priority_high_or_urgent | 211 | 13 | 84 | 918 | 0.9419642857142856 | 0.7152542372881356 | 0.0139634801288936 |
| anomaly_or_risk_high | 226 | 106 | 69 | 825 | 0.6807228915662651 | 0.7661016949152543 | 0.1138560687432867 |

## Priority Sensitivity
| scenario | w_risk | w_leadtime | w_context | top10_overlap_rate | review_required_in_top10 | mean_top10_score |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_best | 0.55 | 0.3 | 0.15 | 0.2 | 8 | 96.04116029109296 |
| risk_heavy | 0.7 | 0.2 | 0.1 | 0.2 | 8 | 97.3607735273953 |
| leadtime_heavy | 0.45 | 0.4 | 0.15 | 0.2 | 8 | 95.9715470547906 |
| balanced | 0.5 | 0.3 | 0.2 | 0.2 | 8 | 94.79116029109296 |

## Hard Normal Review Count

106
