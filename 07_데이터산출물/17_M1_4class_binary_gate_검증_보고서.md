# M1 4class Binary Gate 검증 보고서

## 결론
- 최종 판단: `binary_gate_unstable`
- 해석: threshold 0.5 기준에서 채택 조건을 만족한 조합이 없다. 4분류로 바로 확정하기보다 window policy 또는 normal/event 후보 선별을 먼저 재검토해야 한다.
- 최고 기본 threshold 조합: `pre_event_all` / `expanded154` / `random_forest_balanced_depth3`
- 최고 기본 threshold 성능: balanced accuracy `0.7258`, event recall `0.7945`, normal FPR `0.3429`

## Dataset 구성
| dataset | rows | normal_rows | event_rows | fault_rows | task_rows | activity_rows | substation_count | coverage_min | coverage_median | overlap_rows | window_policies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre_event_all | 181 | 35 | 146 | 62 | 37 | 47 | 33 | 0.9950396825396826 | 1.0 | 38 | activity_pre_7d|fault_pre_7d|normal_event_7d|task_pre_7d |
| low_overlap_hybrid | 185 | 35 | 150 | 62 | 41 | 47 | 33 | 0.9821428571428572 | 1.0 | 15 | activity_pre_7d|fault_pre_7d|normal_event_7d|task_post_7d |

## Threshold 0.5 주요 결과
| dataset | feature_set | model | balanced_accuracy | balanced_accuracy_lift_vs_dummy | recall_event | normal_fpr | precision_event | f1_event | fp | fn | passes_gate_criteria |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre_event_all | expanded154 | random_forest_balanced_depth3 | 0.7258317025440313 | 0.2258317025440313 | 0.7945205479452054 | 0.34285714285714286 | 0.90625 | 0.8467153284671532 | 12 | 30 | False |
| pre_event_all | compact13 | extra_trees_balanced_depth3 | 0.7076320939334638 | 0.20763209393346382 | 0.6438356164383562 | 0.22857142857142856 | 0.9215686274509803 | 0.7580645161290323 | 8 | 52 | False |
| low_overlap_hybrid | expanded154 | extra_trees_balanced_depth3 | 0.7038095238095238 | 0.20380952380952377 | 0.49333333333333335 | 0.08571428571428572 | 0.961038961038961 | 0.6519823788546255 | 3 | 76 | False |
| low_overlap_hybrid | expanded154 | logistic_balanced | 0.699047619047619 | 0.19904761904761903 | 0.8266666666666667 | 0.42857142857142855 | 0.8920863309352518 | 0.8581314878892734 | 15 | 26 | False |
| pre_event_all | expanded154 | extra_trees_balanced_depth3 | 0.6968688845401174 | 0.19686888454011742 | 0.4794520547945205 | 0.08571428571428572 | 0.958904109589041 | 0.639269406392694 | 3 | 76 | False |
| low_overlap_hybrid | expanded154 | random_forest_balanced_depth3 | 0.6857142857142857 | 0.18571428571428572 | 0.8 | 0.42857142857142855 | 0.8888888888888888 | 0.8421052631578947 | 15 | 30 | False |
| low_overlap_hybrid | compact13 | logistic_balanced | 0.6752380952380952 | 0.1752380952380952 | 0.6933333333333334 | 0.34285714285714286 | 0.896551724137931 | 0.7819548872180451 | 12 | 46 | False |
| low_overlap_hybrid | compact13 | extra_trees_balanced_depth3 | 0.6619047619047619 | 0.16190476190476188 | 0.6666666666666666 | 0.34285714285714286 | 0.8928571428571429 | 0.7633587786259542 | 12 | 50 | False |
| pre_event_all | compact13 | logistic_balanced | 0.6504892367906067 | 0.15048923679060666 | 0.6438356164383562 | 0.34285714285714286 | 0.8867924528301887 | 0.746031746031746 | 12 | 52 | False |
| pre_event_all | compact13 | random_forest_balanced_depth3 | 0.6338551859099804 | 0.13385518590998036 | 0.7534246575342466 | 0.4857142857142857 | 0.8661417322834646 | 0.8058608058608059 | 17 | 36 | False |

## Threshold 참고 결과
- 0.5를 기본 판단 기준으로 유지했다.
- 0.4는 event recall 보완 가능성 확인용, 0.6은 normal 오탐 억제 가능성 확인용이다.
| threshold | dataset | feature_set | model | balanced_accuracy | recall_event | normal_fpr | fp | fn | passes_gate_criteria |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.4 | pre_event_all | compact13 | logistic_balanced | 0.6481409001956947 | 0.7534246575342466 | 0.45714285714285713 | 16 | 36 | False |
| 0.4 | low_overlap_hybrid | expanded154 | logistic_balanced | 0.6376190476190476 | 0.8466666666666667 | 0.5714285714285714 | 20 | 23 | False |
| 0.4 | low_overlap_hybrid | compact13 | logistic_balanced | 0.6361904761904762 | 0.7866666666666666 | 0.5142857142857142 | 18 | 32 | False |
| 0.4 | pre_event_all | expanded154 | logistic_balanced | 0.6183953033268101 | 0.8082191780821918 | 0.5714285714285714 | 20 | 28 | False |
| 0.4 | pre_event_all | expanded154 | random_forest_balanced_depth3 | 0.6045988258317025 | 0.952054794520548 | 0.7428571428571429 | 26 | 7 | False |
| 0.5 | pre_event_all | expanded154 | random_forest_balanced_depth3 | 0.7258317025440313 | 0.7945205479452054 | 0.34285714285714286 | 12 | 30 | False |
| 0.5 | pre_event_all | compact13 | extra_trees_balanced_depth3 | 0.7076320939334638 | 0.6438356164383562 | 0.22857142857142856 | 8 | 52 | False |
| 0.5 | low_overlap_hybrid | expanded154 | extra_trees_balanced_depth3 | 0.7038095238095238 | 0.49333333333333335 | 0.08571428571428572 | 3 | 76 | False |
| 0.5 | low_overlap_hybrid | expanded154 | logistic_balanced | 0.699047619047619 | 0.8266666666666667 | 0.42857142857142855 | 15 | 26 | False |
| 0.5 | pre_event_all | expanded154 | extra_trees_balanced_depth3 | 0.6968688845401174 | 0.4794520547945205 | 0.08571428571428572 | 3 | 76 | False |
| 0.6 | pre_event_all | expanded154 | random_forest_balanced_depth3 | 0.7373776908023484 | 0.589041095890411 | 0.11428571428571428 | 4 | 60 | False |
| 0.6 | low_overlap_hybrid | expanded154 | random_forest_balanced_depth3 | 0.7338095238095238 | 0.5533333333333333 | 0.08571428571428572 | 3 | 67 | False |
| 0.6 | low_overlap_hybrid | expanded154 | logistic_balanced | 0.720952380952381 | 0.8133333333333334 | 0.37142857142857144 | 13 | 28 | False |
| 0.6 | low_overlap_hybrid | compact13 | logistic_balanced | 0.6514285714285715 | 0.56 | 0.2571428571428571 | 9 | 66 | False |
| 0.6 | pre_event_all | expanded154 | extra_trees_balanced_depth3 | 0.6500978473581214 | 0.3287671232876712 | 0.02857142857142857 | 1 | 98 | False |

## 검증 사항
- 모든 입력은 16번 M1 taxonomy 산출물에서만 사용했다.
- normal 35건은 그대로 유지했다.
- 학습 입력에는 metadata, 날짜, event id, substation, coverage를 넣지 않았다.
- `compact13`은 13개, `expanded154`는 154개 feature로 분리했다.
- group CV train/test substation overlap은 모든 fold에서 0이다.
- 비대상 제조사 문자열/경로/계산 결과는 새 산출물에 포함하지 않았다.

## 다음 단계
- 4분류 모델 확정 전에 event window policy와 normal/event 후보 선별 기준을 재검토한다.
