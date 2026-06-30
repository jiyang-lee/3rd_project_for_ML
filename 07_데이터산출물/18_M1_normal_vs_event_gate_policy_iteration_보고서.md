# M1 Normal vs Event Gate Policy Iteration 보고서

## 결론
- 최종 판단: `gate_policy_iteration_needed`
- 해석: threshold 0.5 기준에서 최종 잠금은 어렵지만, overlap 제거/normal 증강 후보가 기준선과 비슷한 성능을 보여 추가 기준 반복이 필요하다.
- 최고 기본 threshold 조합: `low_overlap_only` / `expanded154` / `logistic_balanced`
- 최고 기본 threshold 성능: balanced accuracy `0.7323`, event recall `0.8074`, normal FPR `0.3429`
- 주요 병목: recall 우수 조합과 FPR 우수 조합이 서로 다르다.

## Dataset 구성
| dataset | evaluation_rows | normal_rows | event_rows | fault_rows | task_rows | activity_rows | substation_count | event_overlap_rows | coverage_min | coverage_median | train_candidate_normal_rows | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pre_event_all | 181 | 35 | 146 | 62 | 37 | 47 | 33 | 38 | 0.9950396825396826 | 1.0 | 0 | evaluation dataset |
| reference_low_overlap_hybrid | 185 | 35 | 150 | 62 | 41 | 47 | 33 | 15 | 0.9821428571428572 | 1.0 | 0 | evaluation dataset |
| strict_no_overlap | 173 | 35 | 138 | 55 | 37 | 46 | 33 | 0 | 0.9821428571428572 | 1.0 | 0 | evaluation dataset |
| low_overlap_only | 170 | 35 | 135 | 55 | 37 | 43 | 33 | 0 | 0.9821428571428572 | 1.0 | 0 | evaluation dataset |
| train_normal_expanded | 181 | 35 | 146 | 62 | 37 | 47 | 33 | 38 | 0.9950396825396826 | 1.0 | 70 | reference_pre_event_all evaluation; candidate normal is train-fold only and compact13 only |

## Policy Audit
| dataset | final_class | rows | substation_count | window_policies | coverage_min | coverage_median | overlap_rows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pre_event_all | activity | 47 | 19 | activity_pre_7d | 0.9950396825396826 | 1.0 | 4 |
| reference_pre_event_all | fault | 62 | 27 | fault_pre_7d | 0.9950396825396826 | 1.0 | 7 |
| reference_pre_event_all | normal | 35 | 22 | normal_event_7d | 1.0 | 1.0 | 0 |
| reference_pre_event_all | task | 37 | 21 | task_pre_7d | 1.0 | 1.0 | 27 |
| reference_low_overlap_hybrid | activity | 47 | 19 | activity_pre_7d | 0.9950396825396826 | 1.0 | 4 |
| reference_low_overlap_hybrid | fault | 62 | 27 | fault_pre_7d | 0.9950396825396826 | 1.0 | 7 |
| reference_low_overlap_hybrid | normal | 35 | 22 | normal_event_7d | 1.0 | 1.0 | 0 |
| reference_low_overlap_hybrid | task | 41 | 22 | task_post_7d | 0.9821428571428572 | 1.0 | 4 |
| strict_no_overlap | activity | 46 | 19 | activity_post_7d|activity_pre_7d | 0.9950396825396826 | 1.0 | 0 |
| strict_no_overlap | fault | 55 | 26 | fault_pre_7d | 0.9950396825396826 | 1.0 | 0 |
| strict_no_overlap | normal | 35 | 22 | normal_event_7d | 1.0 | 1.0 | 0 |
| strict_no_overlap | task | 37 | 22 | task_post_7d | 0.9821428571428572 | 1.0 | 0 |
| low_overlap_only | activity | 43 | 19 | activity_pre_7d | 0.9950396825396826 | 1.0 | 0 |
| low_overlap_only | fault | 55 | 26 | fault_pre_7d | 0.9950396825396826 | 1.0 | 0 |
| low_overlap_only | normal | 35 | 22 | normal_event_7d | 1.0 | 1.0 | 0 |
| low_overlap_only | task | 37 | 22 | task_post_7d | 0.9821428571428572 | 1.0 | 0 |

## Threshold 0.5 주요 결과
| dataset | feature_set | model | balanced_accuracy | balanced_accuracy_lift_vs_dummy | recall_event | normal_fpr | fp | fn | passes_gate_criteria | decision_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| low_overlap_only | expanded154 | logistic_balanced | 0.7322751322751323 | 0.2322751322751323 | 0.8074074074074075 | 0.34285714285714286 | 12 | 26 | False | gate_policy_iteration_needed |
| reference_pre_event_all | expanded154 | random_forest_balanced_depth3 | 0.7258317025440313 | 0.2258317025440313 | 0.7945205479452054 | 0.34285714285714286 | 12 | 30 | False | normal_vs_event_gate_unstable_keep_pre_event_binary |
| reference_pre_event_all | compact13 | extra_trees_balanced_depth3 | 0.7076320939334638 | 0.20763209393346382 | 0.6438356164383562 | 0.22857142857142856 | 8 | 52 | False | gate_policy_iteration_needed |
| reference_low_overlap_hybrid | expanded154 | extra_trees_balanced_depth3 | 0.7038095238095238 | 0.20380952380952377 | 0.49333333333333335 | 0.08571428571428572 | 3 | 76 | False | gate_policy_iteration_needed |
| reference_low_overlap_hybrid | expanded154 | logistic_balanced | 0.699047619047619 | 0.19904761904761903 | 0.8266666666666667 | 0.42857142857142855 | 15 | 26 | False | gate_policy_iteration_needed |
| train_normal_expanded | compact13 | extra_trees_balanced_depth3 | 0.6973581213307241 | 0.19735812133072406 | 0.6232876712328768 | 0.22857142857142856 | 8 | 55 | False | gate_policy_iteration_needed |
| reference_pre_event_all | expanded154 | extra_trees_balanced_depth3 | 0.6968688845401174 | 0.19686888454011742 | 0.4794520547945205 | 0.08571428571428572 | 3 | 76 | False | gate_policy_iteration_needed |
| low_overlap_only | compact13 | extra_trees_balanced_depth3 | 0.6910052910052911 | 0.19100529100529107 | 0.6962962962962963 | 0.3142857142857143 | 11 | 41 | False | normal_vs_event_gate_unstable_keep_pre_event_binary |
| reference_low_overlap_hybrid | expanded154 | random_forest_balanced_depth3 | 0.6857142857142857 | 0.18571428571428572 | 0.8 | 0.42857142857142855 | 15 | 30 | False | gate_policy_iteration_needed |
| low_overlap_only | expanded154 | extra_trees_balanced_depth3 | 0.6835978835978835 | 0.18359788359788354 | 0.48148148148148145 | 0.11428571428571428 | 4 | 70 | False | gate_policy_iteration_needed |
| strict_no_overlap | expanded154 | logistic_balanced | 0.6770186335403727 | 0.17701863354037273 | 0.782608695652174 | 0.42857142857142855 | 15 | 30 | False | normal_vs_event_gate_unstable_keep_pre_event_binary |
| train_normal_expanded | compact13 | random_forest_balanced_depth3 | 0.6756360078277887 | 0.17563600782778865 | 0.636986301369863 | 0.2857142857142857 | 10 | 53 | False | normal_vs_event_gate_unstable_keep_pre_event_binary |
| reference_low_overlap_hybrid | compact13 | logistic_balanced | 0.6752380952380952 | 0.1752380952380952 | 0.6933333333333334 | 0.34285714285714286 | 12 | 46 | False | normal_vs_event_gate_unstable_keep_pre_event_binary |
| strict_no_overlap | expanded154 | extra_trees_balanced_depth3 | 0.6747412008281574 | 0.17474120082815736 | 0.463768115942029 | 0.11428571428571428 | 4 | 74 | False | gate_policy_iteration_needed |
| strict_no_overlap | compact13 | extra_trees_balanced_depth3 | 0.668944099378882 | 0.168944099378882 | 0.6521739130434783 | 0.3142857142857143 | 11 | 48 | False | normal_vs_event_gate_unstable_keep_pre_event_binary |
| low_overlap_only | compact13 | random_forest_balanced_depth3 | 0.6677248677248677 | 0.16772486772486772 | 0.7925925925925926 | 0.45714285714285713 | 16 | 28 | False | normal_vs_event_gate_unstable_keep_pre_event_binary |
| reference_low_overlap_hybrid | compact13 | extra_trees_balanced_depth3 | 0.6619047619047619 | 0.16190476190476188 | 0.6666666666666666 | 0.34285714285714286 | 12 | 50 | False | normal_vs_event_gate_unstable_keep_pre_event_binary |
| strict_no_overlap | compact13 | logistic_balanced | 0.6546583850931678 | 0.15465838509316776 | 0.6521739130434783 | 0.34285714285714286 | 12 | 48 | False | normal_vs_event_gate_unstable_keep_pre_event_binary |
| train_normal_expanded | compact13 | logistic_balanced | 0.6539138943248533 | 0.15391389432485325 | 0.6506849315068494 | 0.34285714285714286 | 12 | 51 | False | normal_vs_event_gate_unstable_keep_pre_event_binary |
| strict_no_overlap | compact13 | random_forest_balanced_depth3 | 0.6518633540372671 | 0.15186335403726714 | 0.7608695652173914 | 0.45714285714285713 | 16 | 33 | False | normal_vs_event_gate_unstable_keep_pre_event_binary |

## Threshold 참고 결과
| threshold | dataset | feature_set | model | balanced_accuracy | recall_event | normal_fpr | fp | fn | passes_gate_criteria |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.4 | low_overlap_only | expanded154 | logistic_balanced | 0.6899470899470899 | 0.837037037037037 | 0.45714285714285713 | 16 | 22 | False |
| 0.4 | strict_no_overlap | compact13 | logistic_balanced | 0.6554865424430641 | 0.7681159420289855 | 0.45714285714285713 | 16 | 32 | False |
| 0.4 | reference_pre_event_all | compact13 | logistic_balanced | 0.6481409001956947 | 0.7534246575342466 | 0.45714285714285713 | 16 | 36 | False |
| 0.4 | low_overlap_only | compact13 | logistic_balanced | 0.6455026455026455 | 0.7481481481481481 | 0.45714285714285713 | 16 | 34 | False |
| 0.4 | strict_no_overlap | expanded154 | logistic_balanced | 0.6450310559006212 | 0.8043478260869565 | 0.5142857142857142 | 18 | 27 | False |
| 0.4 | low_overlap_only | compact13 | random_forest_balanced_depth3 | 0.644973544973545 | 0.9185185185185185 | 0.6285714285714286 | 22 | 11 | False |
| 0.4 | train_normal_expanded | compact13 | random_forest_balanced_depth3 | 0.6401174168297455 | 0.7945205479452054 | 0.5142857142857142 | 18 | 30 | False |
| 0.4 | reference_low_overlap_hybrid | expanded154 | logistic_balanced | 0.6376190476190476 | 0.8466666666666667 | 0.5714285714285714 | 20 | 23 | False |
| 0.5 | low_overlap_only | expanded154 | logistic_balanced | 0.7322751322751323 | 0.8074074074074075 | 0.34285714285714286 | 12 | 26 | False |
| 0.5 | reference_pre_event_all | expanded154 | random_forest_balanced_depth3 | 0.7258317025440313 | 0.7945205479452054 | 0.34285714285714286 | 12 | 30 | False |
| 0.5 | reference_pre_event_all | compact13 | extra_trees_balanced_depth3 | 0.7076320939334638 | 0.6438356164383562 | 0.22857142857142856 | 8 | 52 | False |
| 0.5 | reference_low_overlap_hybrid | expanded154 | extra_trees_balanced_depth3 | 0.7038095238095238 | 0.49333333333333335 | 0.08571428571428572 | 3 | 76 | False |
| 0.5 | reference_low_overlap_hybrid | expanded154 | logistic_balanced | 0.699047619047619 | 0.8266666666666667 | 0.42857142857142855 | 15 | 26 | False |
| 0.5 | train_normal_expanded | compact13 | extra_trees_balanced_depth3 | 0.6973581213307241 | 0.6232876712328768 | 0.22857142857142856 | 8 | 55 | False |
| 0.5 | reference_pre_event_all | expanded154 | extra_trees_balanced_depth3 | 0.6968688845401174 | 0.4794520547945205 | 0.08571428571428572 | 3 | 76 | False |
| 0.5 | low_overlap_only | compact13 | extra_trees_balanced_depth3 | 0.6910052910052911 | 0.6962962962962963 | 0.3142857142857143 | 11 | 41 | False |
| 0.6 | low_overlap_only | expanded154 | logistic_balanced | 0.7423280423280423 | 0.7703703703703704 | 0.2857142857142857 | 10 | 31 | False |
| 0.6 | reference_pre_event_all | expanded154 | random_forest_balanced_depth3 | 0.7373776908023484 | 0.589041095890411 | 0.11428571428571428 | 4 | 60 | False |
| 0.6 | reference_low_overlap_hybrid | expanded154 | random_forest_balanced_depth3 | 0.7338095238095238 | 0.5533333333333333 | 0.08571428571428572 | 3 | 67 | False |
| 0.6 | reference_low_overlap_hybrid | expanded154 | logistic_balanced | 0.720952380952381 | 0.8133333333333334 | 0.37142857142857144 | 13 | 28 | False |
| 0.6 | strict_no_overlap | expanded154 | random_forest_balanced_depth3 | 0.6932712215320911 | 0.5579710144927537 | 0.17142857142857143 | 6 | 61 | False |
| 0.6 | low_overlap_only | expanded154 | random_forest_balanced_depth3 | 0.6873015873015873 | 0.4888888888888889 | 0.11428571428571428 | 4 | 69 | False |
| 0.6 | strict_no_overlap | expanded154 | logistic_balanced | 0.6838509316770186 | 0.7391304347826086 | 0.37142857142857144 | 13 | 36 | False |
| 0.6 | train_normal_expanded | compact13 | logistic_balanced | 0.6819960861056751 | 0.5068493150684932 | 0.14285714285714285 | 5 | 72 | False |

## 진단
- label 기준: `event=fault+task+activity`로 유지했지만, event 내부 패턴 차이가 커서 단일 gate가 흔들린다.
- window overlap: strict/low-overlap 후보를 따로 검증했으나 threshold 0.5 채택 조건을 만족하지 못했다.
- normal 샘플: candidate normal train 증강은 compact13에서만 가능하며, 평가 normal 35건은 변경하지 않았다.
- feature/model: expanded154와 tree 모델이 기준선에서는 가장 강하지만, 오탐과 미탐 tradeoff가 아직 크다.

## 검증 사항
- 모든 계산은 M1 taxonomy 산출물 기준으로 수행했다.
- normal 35건 label은 변경하지 않았다.
- 학습 입력에서 metadata/date/event id/substation/coverage는 제외했다.
- group CV train/test substation overlap은 모든 fold에서 0이다.
- 비대상 제조사 문자열/경로/결과는 새 산출물에 포함하지 않았다.

## 다음 단계
- 바로 3분류로 가지 말고, event 내부를 한 번에 묶는 gate 대신 fault/task/activity별 one-vs-normal gate를 비교한다.
