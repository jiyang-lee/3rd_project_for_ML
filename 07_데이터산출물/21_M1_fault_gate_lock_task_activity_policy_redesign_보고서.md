# M1 Fault Gate Lock 및 Task/Activity Policy Redesign 보고서

## 결론
- 최종 판단: `fault_gate_pending_and_policy_redesign_continue`
- fault 판단: `fault_gate_lock_pending_threshold_review`
- task 판단: `task_window_candidate_selected`
- activity 판단: `activity_window_candidate_selected`
- fault는 19번 기준 조합을 재현했고, threshold 0.5에서 lock 기준을 만족했다.
- 다만 fault는 threshold 0.5 한 지점만 통과해 잠금 보류 성격의 threshold review가 필요하다.
- task/activity는 새 1일·3일 window까지 비교했고, overlap/recall/FPR 기준을 함께 본다.

## 근거
### Fault Lock
- 기준 후보: `fault_no_overlap + compact13 + random_forest_balanced_depth3 + threshold 0.5`
- balanced accuracy `0.8455`, recall `0.8909`, normal FPR `0.2000`, FP `7`, FN `6`
- 19번 결과 재현: `True`
- 비교 후보 `expanded154 + LightGBM + threshold 0.6`: BA `0.8325`, recall `0.8364`, normal FPR `0.1714`

| feature_set | model | threshold | balanced_accuracy | target_recall | normal_fpr | fp | fn | passes_lock_criteria | fault_final_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compact13 | random_forest_balanced_depth3 | 0.45 | 0.8350649350649351 | 0.9272727272727272 | 0.2571428571428571 | 9 | 4 | False | fault_gate_lock_pending_threshold_review |
| compact13 | random_forest_balanced_depth3 | 0.5 | 0.8454545454545455 | 0.8909090909090909 | 0.2 | 7 | 6 | True | fault_gate_lock_pending_threshold_review |
| compact13 | random_forest_balanced_depth3 | 0.55 | 0.790909090909091 | 0.7818181818181819 | 0.2 | 7 | 12 | False | fault_gate_lock_pending_threshold_review |
| compact13 | random_forest_balanced_depth3 | 0.6 | 0.7649350649350649 | 0.6727272727272727 | 0.1428571428571428 | 5 | 18 | False | fault_gate_lock_pending_threshold_review |
| expanded154 | lightgbm_balanced | 0.45 | 0.8064935064935065 | 0.9272727272727272 | 0.3142857142857143 | 11 | 4 | False | fault_gate_lock_pending_threshold_review |
| expanded154 | lightgbm_balanced | 0.5 | 0.8077922077922077 | 0.8727272727272727 | 0.2571428571428571 | 9 | 7 | False | fault_gate_lock_pending_threshold_review |
| expanded154 | lightgbm_balanced | 0.55 | 0.8038961038961039 | 0.8363636363636363 | 0.2285714285714285 | 8 | 9 | False | fault_gate_lock_pending_threshold_review |
| expanded154 | lightgbm_balanced | 0.6 | 0.8324675324675325 | 0.8363636363636363 | 0.1714285714285714 | 6 | 9 | False | fault_gate_lock_pending_threshold_review |

### Task/Activity Candidate Summary
| dataset | target_class | rows | normal_rows | target_rows | substation_count | target_substation_count | target_overlap_rows | target_overlap_rate | normal_collision_rows | coverage_min | coverage_median | window_policies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activity_no_overlap | activity | 81 | 35 | 46 | 27 | 19 | 0 | 0.0 | 0 | 0.9950396825396826 | 1.0 | activity_post_7d\|activity_pre_7d |
| activity_post_1d | activity | 81 | 35 | 46 | 27 | 19 | 4 | 0.0869565217391304 | 0 | 0.9930555555555556 | 1.0 | activity_post_1d |
| activity_post_3d | activity | 81 | 35 | 46 | 27 | 19 | 5 | 0.108695652173913 | 0 | 0.9976851851851852 | 1.0 | activity_post_3d |
| activity_post_all | activity | 81 | 35 | 46 | 27 | 19 | 5 | 0.108695652173913 | 0 | 0.9950396825396826 | 1.0 | activity_post_7d |
| activity_pre_1d | activity | 82 | 35 | 47 | 27 | 19 | 2 | 0.0425531914893617 | 0 | 0.9652777777777778 | 1.0 | activity_pre_1d |
| activity_pre_3d | activity | 82 | 35 | 47 | 27 | 19 | 4 | 0.0851063829787234 | 0 | 0.988425925925926 | 1.0 | activity_pre_3d |
| activity_pre_all | activity | 82 | 35 | 47 | 27 | 19 | 4 | 0.0851063829787234 | 0 | 0.9950396825396826 | 1.0 | activity_pre_7d |
| task_no_overlap | task | 72 | 35 | 37 | 31 | 22 | 0 | 0.0 | 0 | 0.9821428571428572 | 1.0 | task_post_7d |
| task_post_1d | task | 77 | 35 | 42 | 31 | 22 | 2 | 0.0476190476190476 | 0 | 1.0 | 1.0 | task_post_1d |
| task_post_3d | task | 77 | 35 | 42 | 31 | 22 | 3 | 0.0714285714285714 | 0 | 0.9583333333333334 | 1.0 | task_post_3d |
| task_post_all | task | 76 | 35 | 41 | 31 | 22 | 4 | 0.0975609756097561 | 0 | 0.9821428571428572 | 1.0 | task_post_7d |
| task_pre_1d | task | 75 | 35 | 40 | 31 | 22 | 16 | 0.4 | 0 | 0.9861111111111112 | 1.0 | task_pre_1d |
| task_pre_3d | task | 75 | 35 | 40 | 31 | 22 | 24 | 0.6 | 1 | 0.9837962962962964 | 1.0 | task_pre_3d |
| task_pre_all | task | 72 | 35 | 37 | 30 | 21 | 27 | 0.7297297297297297 | 0 | 1.0 | 1.0 | task_pre_7d |

### Task/Activity Selected Candidate Rows at Threshold 0.5
| target_class | dataset | feature_set | model | threshold | balanced_accuracy | target_recall | normal_fpr | target_overlap_rate | candidate_pass | target_policy_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activity | activity_pre_1d | compact13 | random_forest_balanced_depth3 | 0.5 | 1.0 | 1.0 | 0.0 | 0.0425531914893617 | True | activity_window_candidate_selected |
| task | task_post_1d | compact13 | random_forest_balanced_depth3 | 0.5 | 1.0 | 1.0 | 0.0 | 0.0476190476190476 | True | task_window_candidate_selected |

## 한계
- task/activity의 짧은 window는 기존 154개 temporal feature 중 일부가 비어 imputation에 의존한다.
- task는 원본 event duration/end가 없어 centered window는 audit 전용으로만 남겼다.
- fault lock은 class별 gate 기준이며 최종 4분류 전체 모델 확정은 아니다.
- normal 35건 고정이라 FPR은 fold 구성에 민감하다.

## 다음 작업 순서
1. fault gate는 threshold 0.5 기준 잠금 후보로 유지하되, 한 지점 통과라 threshold review를 보고한다.
2. task/activity는 선택 후보가 있으면 해당 window 기준으로 별도 재검증한다.
3. 후보가 없으면 task/activity label 정의와 event duration 확보 가능성을 먼저 검토한다.
4. fault + 하나 이상의 event type gate가 안정화되면 hierarchical 4분류 전략을 다시 설계한다.

## 품질 검증
| check | pass | detail |
| --- | --- | --- |
| fault_metric_recompute | True | ba_diff=0.0; f1_diff=0.0 |
| task_activity_metric_recompute | True | ba_diff=1.1102230246251565e-16; f1_diff=1.1102230246251565e-16 |
| non_target_manufacturer_absent | True | [] |
| source_zip_exists | True | C:\3rd_Project\HeatGridAgent\05_데이터셋\PreDist\predist_dataset.zip |
| source_metadata_clean | True |  |
| special_event_policy_retained | True | [19, 20, 34, 35, 48, 67, 68, 69] |
| normal_35_retained | True | 35 |
| group_overlap_zero | True | max overlap 0 |