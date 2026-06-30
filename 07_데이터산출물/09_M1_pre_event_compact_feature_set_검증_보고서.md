# M1 pre-event compact feature set 검증 보고서

## 결론

- 최종 판단: compact13_overlap compact feature set 채택
- 선택 feature set: `compact13_overlap` (13개 feature)
- threshold는 0.6으로 고정했고, 라벨/window 기준은 08번과 동일하게 유지했다.
- compact 후보는 154개 feature 대비 feature 수를 크게 줄였지만, 채택 기준을 모두 만족한 후보만 최종 후보로 인정했다.

## Feature Set Summary

| feature_set | feature_count | selection_rule |
| --- | --- | --- |
| base70 | 70 | original common 10 signals x 7 stats |
| expanded154 | 154 | base70 plus derived and temporal expansion |
| compact13_overlap | 13 | intersection of top20 expanded features from both datasets |
| compact20_main | 20 | top20 expanded features from strict_no_event20 |
| compact27_union | 27 | union of top20 expanded features from both datasets |

## Threshold 0.6 Decision Matrix

| dataset_id | feature_set | feature_count | balanced_accuracy | recall | f1 | false_positive_rate | fp | fn | ba_delta_vs_expanded154 | recall_delta_vs_expanded154 | fpr_delta_vs_expanded154 | candidate_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict_no_event20 | base70 | 70 | 0.6214 | 0.5000 | 0.4667 | 0.2571 | 9 | 7 | -0.0286 | 0.0000 | 0.0571 |  |
| strict_no_event20_no_event67 | base70 | 70 | 0.6121 | 0.5385 | 0.4516 | 0.3143 | 11 | 6 | -0.0473 | 0.0769 | 0.1714 |  |
| strict_no_event20 | expanded154 | 154 | 0.6500 | 0.5000 | 0.5000 | 0.2000 | 7 | 7 | 0.0000 | 0.0000 | 0.0000 |  |
| strict_no_event20_no_event67 | expanded154 | 154 | 0.6593 | 0.4615 | 0.5000 | 0.1429 | 5 | 7 | 0.0000 | 0.0000 | 0.0000 |  |
| strict_no_event20 | compact13_overlap | 13 | 0.8286 | 0.7143 | 0.7692 | 0.0571 | 2 | 4 | 0.1786 | 0.2143 | -0.1429 | True |
| strict_no_event20_no_event67 | compact13_overlap | 13 | 0.8176 | 0.6923 | 0.7500 | 0.0571 | 2 | 4 | 0.1582 | 0.2308 | -0.0857 | True |
| strict_no_event20 | compact20_main | 20 | 0.7786 | 0.6429 | 0.6923 | 0.0857 | 3 | 5 | 0.1286 | 0.1429 | -0.1143 | True |
| strict_no_event20_no_event67 | compact20_main | 20 | 0.8560 | 0.7692 | 0.8000 | 0.0571 | 2 | 3 | 0.1967 | 0.3077 | -0.0857 | True |
| strict_no_event20 | compact27_union | 27 | 0.8643 | 0.7857 | 0.8148 | 0.0571 | 2 | 3 | 0.2143 | 0.2857 | -0.1429 | True |
| strict_no_event20_no_event67 | compact27_union | 27 | 0.8703 | 0.7692 | 0.8333 | 0.0286 | 1 | 3 | 0.2110 | 0.3077 | -0.1143 | True |

## Candidate Pass Summary

| feature_set | priority | ba_pass | recall_pass | fpr_pass | feature_count_pass | candidate_pass |
| --- | --- | --- | --- | --- | --- | --- |
| compact13_overlap | 1 | True | True | True | True | True |
| compact20_main | 2 | True | True | True | True | True |
| compact27_union | 3 | True | True | True | True | True |

## Group CV 평균 성능

| dataset_id | feature_set | model | balanced_accuracy | precision | recall | f1 | roc_auc | fp | fn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict_no_event20 | base70 | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.8000 |
| strict_no_event20 | base70 | logistic_balanced | 0.5738 | 0.3000 | 0.5000 | 0.3714 | 0.6024 | 2.4000 | 1.4000 |
| strict_no_event20 | compact13_overlap | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.8000 |
| strict_no_event20 | compact13_overlap | logistic_balanced | 0.8065 | 0.7333 | 0.7333 | 0.6829 | 0.9111 | 0.8000 | 0.8000 |
| strict_no_event20 | compact20_main | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.8000 |
| strict_no_event20 | compact20_main | logistic_balanced | 0.7923 | 0.8500 | 0.6667 | 0.6648 | 0.9079 | 0.6000 | 1.0000 |
| strict_no_event20 | compact27_union | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.8000 |
| strict_no_event20 | compact27_union | logistic_balanced | 0.8732 | 0.8833 | 0.8000 | 0.7914 | 0.8944 | 0.4000 | 0.6000 |
| strict_no_event20 | expanded154 | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.8000 |
| strict_no_event20 | expanded154 | logistic_balanced | 0.6220 | 0.3600 | 0.5667 | 0.4205 | 0.7123 | 2.2000 | 1.2000 |
| strict_no_event20_no_event67 | base70 | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.6000 |
| strict_no_event20_no_event67 | base70 | logistic_balanced | 0.5821 | 0.3333 | 0.5333 | 0.4024 | 0.5813 | 2.6000 | 1.2000 |
| strict_no_event20_no_event67 | compact13_overlap | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.6000 |
| strict_no_event20_no_event67 | compact13_overlap | logistic_balanced | 0.8381 | 0.8167 | 0.7667 | 0.7581 | 0.8611 | 0.6000 | 0.6000 |
| strict_no_event20_no_event67 | compact20_main | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.6000 |
| strict_no_event20_no_event67 | compact20_main | logistic_balanced | 0.8405 | 0.8500 | 0.7667 | 0.7581 | 0.8639 | 0.6000 | 0.6000 |
| strict_no_event20_no_event67 | compact27_union | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.6000 |
| strict_no_event20_no_event67 | compact27_union | logistic_balanced | 0.8381 | 0.7000 | 0.7333 | 0.6933 | 0.9500 | 0.4000 | 0.6000 |
| strict_no_event20_no_event67 | expanded154 | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.6000 |
| strict_no_event20_no_event67 | expanded154 | logistic_balanced | 0.6810 | 0.5033 | 0.5667 | 0.5100 | 0.7135 | 1.4000 | 1.0000 |

## 중요 feature 유형 요약

| type | evidence |
| --- | --- |
| 최근 6시간/12시간 변화 | outdoor_temperature 및 supply temperature 변화 feature가 양쪽 top20에 반복 등장 |
| 최근 1일 vs 이전 6일 변화 | p_return_gap, return temperature, supply temperature 계열이 상위권 |
| return temperature gap | p_return_gap feature가 main/sensitivity 모두 최상위 |
| supply temperature / setpoint | s_hc1_supply_temperature 및 setpoint 변화 feature가 공통 feature set에 포함 |

## 생성 이미지

- `07_데이터산출물/m1_compact_feature_importance_top20_main.png`
- `07_데이터산출물/m1_compact_feature_importance_top20_no_event67.png`
- `07_데이터산출물/m1_compact_feature_set_overlap.png`

## 해석

- `expanded154`의 개선 신호는 주로 최근 변화량과 온도차 계열에서 나왔다.
- compact feature set은 중요 feature를 압축해 검증하기 위한 후보이며, 최종 운영 모델 저장이나 배포는 하지 않았다.
- 이번 compact 선정은 08번의 전체 CV 중요도 결과를 사용한 post-hoc feature selection이므로 성능이 낙관적으로 보일 수 있다. 따라서 채택은 다음 실험 후보 채택이지 운영 확정이 아니다.
- compact 후보가 기준을 통과하지 못하면 `expanded154`를 유지하고, 다음 단계에서 normal negative 재설계 또는 센서 컬럼 확장을 검토한다.