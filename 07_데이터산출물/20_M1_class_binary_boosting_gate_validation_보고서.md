# M1 Class Binary Boosting Gate 검증 보고서

## 결론
- 최종 판단: `return_to_window_label_design`
- class별 binary gate에서 Logistic 기준선 대비 LightGBM/XGBoost를 비교했다.
- boosting은 class별로만 채택하며, 모든 class에 일괄 적용하지 않는다.

## 근거
| target_class | dataset | feature_set | model | balanced_accuracy | macro_f1 | recall_target | normal_fpr | fold_balanced_accuracy_std | delta_ba_vs_logistic | delta_recall_vs_logistic | delta_fpr_vs_logistic | passes_boosting_vs_logistic | decision_candidate | target_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activity | activity_post_all | expanded154 | xgboost_balanced | 0.7409937888198758 | 0.7381868554717561 | 0.7391304347826086 | 0.2571428571428571 | 0.09956061744981885 | 0.08229813664596275 | 0.021739130434782594 | -0.1428571428571429 | True | gate_iteration_needed | gate_iteration_needed |
| task | task_post_all | expanded154 | lightgbm_balanced | 0.686411149825784 | 0.683991683991684 | 0.6585365853658537 | 0.2857142857142857 | 0.07898188743284132 | 0.11184668989547042 | 0.1951219512195122 | -0.02857142857142858 | True | gate_iteration_needed | gate_iteration_needed |
| fault | fault_no_overlap | expanded154 | xgboost_balanced | 0.8207792207792208 | 0.8302801724137931 | 0.9272727272727272 | 0.2857142857142857 | 0.10635223346421446 | 0.11428571428571432 | 0.19999999999999996 | -0.02857142857142858 | False | gate_iteration_needed | gate_iteration_needed |

## Class별 의사결정
| target_class | target_decision |
| --- | --- |
| activity | gate_iteration_needed |
| fault | gate_iteration_needed |
| task | gate_iteration_needed |

## Class별 Sample 수
| dataset | target_class | policy_variant | rows | normal_rows | target_rows | substation_count | target_substation_count | target_overlap_rows | coverage_min | coverage_median | window_policies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fault_no_overlap | fault | no_overlap | 90 | 35 | 55 | 31 | 26 | 0 | 0.9950396825396826 | 1.0 | fault_pre_7d |
| task_pre_all | task | pre_all | 72 | 35 | 37 | 30 | 21 | 27 | 1.0 | 1.0 | task_pre_7d |
| task_post_all | task | post_all | 76 | 35 | 41 | 31 | 22 | 4 | 0.9821428571428572 | 1.0 | task_post_7d |
| task_no_overlap | task | no_overlap | 72 | 35 | 37 | 31 | 22 | 0 | 0.9821428571428572 | 1.0 | task_post_7d |
| activity_pre_all | activity | pre_all | 82 | 35 | 47 | 27 | 19 | 4 | 0.9950396825396826 | 1.0 | activity_pre_7d |
| activity_post_all | activity | post_all | 81 | 35 | 46 | 27 | 19 | 5 | 0.9950396825396826 | 1.0 | activity_post_7d |
| activity_no_overlap | activity | no_overlap | 81 | 35 | 46 | 27 | 19 | 0 | 0.9950396825396826 | 1.0 | activity_post_7d|activity_pre_7d |

## Class별 Precision/Recall/F1
| target_class | dataset | feature_set | model | class_label | precision | recall | f1 | support |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activity | activity_post_all | expanded154 | xgboost_balanced | normal | 0.6842105263157895 | 0.7428571428571429 | 0.7123287671232876 | 35 |
| activity | activity_post_all | expanded154 | xgboost_balanced | activity | 0.7906976744186046 | 0.7391304347826086 | 0.7640449438202247 | 46 |
| fault | fault_no_overlap | expanded154 | xgboost_balanced | normal | 0.8620689655172413 | 0.7142857142857143 | 0.78125 | 35 |
| fault | fault_no_overlap | expanded154 | xgboost_balanced | fault | 0.8360655737704918 | 0.9272727272727272 | 0.8793103448275862 | 55 |
| task | task_post_all | expanded154 | lightgbm_balanced | normal | 0.6410256410256411 | 0.7142857142857143 | 0.6756756756756757 | 35 |
| task | task_post_all | expanded154 | lightgbm_balanced | task | 0.7297297297297297 | 0.6585365853658537 | 0.6923076923076923 | 41 |

## Confusion Matrix
| target_class | dataset | feature_set | model | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| activity | activity_post_all | expanded154 | xgboost_balanced | 26 | 9 | 12 | 34 |
| fault | fault_no_overlap | expanded154 | xgboost_balanced | 25 | 10 | 4 | 51 |
| task | task_post_all | expanded154 | lightgbm_balanced | 25 | 10 | 14 | 27 |

## Fold 안정성
| target_class | dataset | feature_set | model | fold_balanced_accuracy_mean | fold_balanced_accuracy_std | fold_recall_std | fold_normal_fpr_std |
| --- | --- | --- | --- | --- | --- | --- | --- |
| activity | activity_post_all | expanded154 | xgboost_balanced | 0.7354761904761904 | 0.09956061744981885 | 0.15864491758812574 | 0.26777776601650316 |
| fault | fault_no_overlap | expanded154 | xgboost_balanced | 0.8154220779220779 | 0.10635223346421446 | 0.09958591954639379 | 0.13339178140702213 |
| task | task_post_all | expanded154 | lightgbm_balanced | 0.6838888888888889 | 0.07898188743284132 | 0.19072165070428448 | 0.26975518001116705 |

## 품질 검증
- 생성 CSV를 다시 읽어 balanced accuracy와 macro F1을 독립 재계산했고 저장 수치와 대조했다.
- M1 산출물만 사용했고 비대상 제조사 문자열/경로/계산 결과는 새 산출물에 포함하지 않았다.
- 원본 ZIP 존재와 metadata/source directory clean 상태를 확인했다.
- Event 20/34/69/67, Event 19/68/35/48 처리 기준은 19번 audit에서 유지된 것을 확인했다.
| check_name | pass_all | rows |
| --- | --- | --- |
| metric_recompute | True | 168 |
| source_metadata_clean | True | 1 |
| source_zip_exists | True | 1 |
| special_event_policy_retained | True | 1 |

## 한계
- normal 35건 고정이라 normal FPR이 fold 구성에 민감하다.
- boosting은 작은 데이터에서 과적합 위험이 있어 fold 안정성을 반드시 같이 봐야 한다.
- 이번 결과는 class별 gate 비교이며 최종 4분류 성능이 아니다.

## 다음 작업 순서
1. 안정적인 class gate부터 후보로 잠근다.
2. boosting이 명확히 안정적인 class에만 boosting을 채택한다.
3. 불안정한 task/activity는 window/label 정책 재검토 후 다시 비교한다.
4. class별 gate가 2개 이상 안정화되면 4분류 전략을 다시 설계한다.
