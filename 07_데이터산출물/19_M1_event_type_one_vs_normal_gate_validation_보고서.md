# M1 Event Type One-vs-Normal Gate 검증 보고서

## 결론
- 최종 판단: `partial_one_vs_normal_gate_candidate`
- 기준을 만족한 target: `fault`
- `normal vs event` 단일 gate보다 class별 gate가 어느 target에서 가능한지 확인하는 단계이며, 4분류 확정은 아직 보류한다.

## 근거
| target_class | dataset | feature_set | model | balanced_accuracy | macro_f1 | balanced_accuracy_lift_vs_dummy | recall_target | normal_fpr | fp | fn | passes_gate_criteria | target_decision_at_t0_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fault | fault_no_overlap | compact13 | random_forest_balanced_depth3 | 0.8454545454545455 | 0.8472385428907168 | 0.34545454545454546 | 0.8909090909090909 | 0.2 | 7 | 6 | True | one_vs_normal_gate_candidate_locked |
| activity | activity_pre_all | expanded154 | random_forest_balanced_depth3 | 0.8261398176291793 | 0.8047619047619048 | 0.3261398176291793 | 0.6808510638297872 | 0.02857142857142857 | 1 | 15 | False | one_vs_normal_gate_iteration_needed |
| task | task_pre_all | compact13 | extra_trees_balanced_depth3 | 0.7521235521235521 | 0.7492260061919505 | 0.2737451737451737 | 0.6756756756756757 | 0.17142857142857143 | 6 | 12 | False | one_vs_normal_gate_iteration_needed |

## Class별 Sample 수
| dataset | target_class | policy_variant | normal_rows | target_rows | target_overlap_rows | coverage_min | coverage_median |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fault_pre_all | fault | pre_all | 35 | 62 | 7 | 0.9950396825396826 | 1.0 |
| fault_no_overlap | fault | no_overlap | 35 | 55 | 0 | 0.9950396825396826 | 1.0 |
| task_pre_all | task | pre_all | 35 | 37 | 27 | 1.0 | 1.0 |
| task_post_all | task | post_all | 35 | 41 | 4 | 0.9821428571428572 | 1.0 |
| task_no_overlap | task | no_overlap | 35 | 37 | 0 | 0.9821428571428572 | 1.0 |
| activity_pre_all | activity | pre_all | 35 | 47 | 4 | 0.9950396825396826 | 1.0 |
| activity_post_all | activity | post_all | 35 | 46 | 5 | 0.9950396825396826 | 1.0 |
| activity_no_overlap | activity | no_overlap | 35 | 46 | 0 | 0.9950396825396826 | 1.0 |

## Class별 Precision/Recall/F1
| target_class | dataset | feature_set | model | class_label | precision | recall | f1 | support |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activity | activity_pre_all | expanded154 | random_forest_balanced_depth3 | normal | 0.6938775510204082 | 0.9714285714285714 | 0.8095238095238095 | 35 |
| activity | activity_pre_all | expanded154 | random_forest_balanced_depth3 | activity | 0.9696969696969697 | 0.6808510638297872 | 0.8 | 47 |
| fault | fault_no_overlap | compact13 | random_forest_balanced_depth3 | normal | 0.8235294117647058 | 0.8 | 0.8115942028985508 | 35 |
| fault | fault_no_overlap | compact13 | random_forest_balanced_depth3 | fault | 0.875 | 0.8909090909090909 | 0.8828828828828829 | 55 |
| task | task_pre_all | compact13 | extra_trees_balanced_depth3 | normal | 0.7073170731707317 | 0.8285714285714286 | 0.7631578947368421 | 35 |
| task | task_pre_all | compact13 | extra_trees_balanced_depth3 | task | 0.8064516129032258 | 0.6756756756756757 | 0.7352941176470589 | 37 |

## Confusion Matrix
| target_class | dataset | feature_set | model | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| activity | activity_pre_all | expanded154 | random_forest_balanced_depth3 | 34 | 1 | 15 | 32 |
| fault | fault_no_overlap | compact13 | random_forest_balanced_depth3 | 28 | 7 | 6 | 49 |
| task | task_pre_all | compact13 | extra_trees_balanced_depth3 | 29 | 6 | 12 | 25 |

## 품질 검증
- 생성 CSV를 다시 읽어 balanced accuracy와 macro F1을 독립 재계산했고, 저장 metric과 일치하는지 확인했다.
- 모든 계산은 16번 M1 taxonomy/window audit 산출물 기준으로 수행했다.
- 비대상 제조사 문자열/경로/계산 결과는 새 산출물에 포함하지 않았다.
- 원본 ZIP 존재와 `05_데이터셋/PreDist` 하위 git status clean을 확인했다.
- Event 20/34/69/67 및 Event 19/68/35/48 처리 기준은 special event audit으로 유지했다.
| check_name | pass_all | rows |
| --- | --- | --- |
| metric_recompute | True | 192 |
| source_metadata_clean | True | 1 |
| source_zip_exists | True | 1 |
| special_event_audit_present | True | 1 |

## 한계
- normal은 35건으로 고정되어 있어 normal FPR 추정이 fold 구성에 민감하다.
- event type별 샘플 수와 window 정책이 서로 다르기 때문에, one-vs-normal 결과를 바로 4분류 성능으로 해석하면 안 된다.
- threshold 0.5 기준을 우선했으며, 운영 threshold 튜닝은 아직 하지 않았다.

## 다음 작업 순서
1. 기준을 만족한 target이 있으면 해당 class gate를 후보로 잠근다.
2. 기준 미달 target은 window 정책 또는 normal 후보 보강을 먼저 재검토한다.
3. class별 gate가 2개 이상 안정화된 뒤에만 `fault/task/activity` 내부 다중분류를 다시 검토한다.
