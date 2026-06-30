# M1 positive 확장학습 보고서

## 개요

strict positive만으로는 positive 샘플이 너무 작아, `efd_possible=True`지만 `Possible anomaly start`가 없는 M1 후보를 `weak_positive`로 분리해 추가 검증했다. 목적은 모델 고도화가 아니라 positive 확장만으로 최소 학습 신호가 안정되는지 확인하는 것이다.

## 결론

positive 확장만으로는 부족, 라벨 재검토/feature 확장 필요

- 판단 이유: weak positive 추가가 안정적인 개선으로 이어지는지, 또는 false positive를 충분히 낮추는지 확인되지 않았다.
- accepted weak positive: 12건
- unknown fault label Event 34/69는 학습에서 제외하고 audit에만 남겼다.
- Event 20은 계속 학습에서 제외했다.
- top-10 feature overlap(strict vs expanded): 6개, Jaccard 0.4286

## Positive audit 요약

| label_strength | expansion_status | rows | coverage_min | coverage_median |
| --- | --- | --- | --- | --- |
| strict_positive | event20_excluded | 1 | 0.7242 | 0.7242 |
| strict_positive | strict_accepted | 14 | 0.9950 | 1.0000 |
| weak_positive | unknown_review | 2 | 1.0000 | 1.0000 |
| weak_positive | weak_accepted | 12 | 1.0000 | 1.0000 |

## Dataset 요약

| dataset_id | rows | normal_rows | positive_rows | strict_positive_rows | weak_positive_rows | event20_included | event67_included | coverage_min | learning_feature_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict_no_event20 | 49 | 35 | 14 | 14 | 0 | False | True | 0.9950 | 70 |
| strict_no_event20_no_event67 | 48 | 35 | 13 | 13 | 0 | False | False | 0.9950 | 70 |
| expanded_weak_positive | 61 | 35 | 26 | 14 | 12 | False | True | 0.9950 | 70 |

## Group CV 요약

| dataset_id | model | balanced_accuracy_mean | precision_mean | recall_mean | f1_mean | roc_auc_mean | fp_sum | fn_sum | balanced_accuracy_lift_vs_dummy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expanded_weak_positive | logistic_balanced | 0.5695 | 0.5752 | 0.5533 | 0.4895 | 0.5854 | 15 | 12 | 0.0695 |
| strict_no_event20 | logistic_balanced | 0.5738 | 0.3000 | 0.5000 | 0.3714 | 0.6024 | 12 | 7 | 0.0738 |
| strict_no_event20_no_event67 | logistic_balanced | 0.5821 | 0.3333 | 0.5333 | 0.4024 | 0.5813 | 13 | 6 | 0.0821 |

## Threshold 0.3~0.6 비교

| dataset_id | threshold | balanced_accuracy | precision | recall | f1 | fp | fn | false_positive_rate | false_negative_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expanded_weak_positive | 0.3000 | 0.5319 | 0.4500 | 0.6923 | 0.5455 | 22 | 8 | 0.6286 | 0.3077 |
| expanded_weak_positive | 0.4000 | 0.5363 | 0.4571 | 0.6154 | 0.5246 | 19 | 10 | 0.5429 | 0.3846 |
| expanded_weak_positive | 0.5000 | 0.5549 | 0.4828 | 0.5385 | 0.5091 | 15 | 12 | 0.4286 | 0.4615 |
| expanded_weak_positive | 0.6000 | 0.5544 | 0.5000 | 0.4231 | 0.4583 | 11 | 15 | 0.3143 | 0.5769 |
| strict_no_event20 | 0.3000 | 0.5500 | 0.3214 | 0.6429 | 0.4286 | 19 | 5 | 0.5429 | 0.3571 |
| strict_no_event20 | 0.4000 | 0.5357 | 0.3182 | 0.5000 | 0.3889 | 15 | 7 | 0.4286 | 0.5000 |
| strict_no_event20 | 0.5000 | 0.5786 | 0.3684 | 0.5000 | 0.4242 | 12 | 7 | 0.3429 | 0.5000 |
| strict_no_event20 | 0.6000 | 0.6214 | 0.4375 | 0.5000 | 0.4667 | 9 | 7 | 0.2571 | 0.5000 |
| strict_no_event20_no_event67 | 0.3000 | 0.5549 | 0.3182 | 0.5385 | 0.4000 | 15 | 6 | 0.4286 | 0.4615 |
| strict_no_event20_no_event67 | 0.4000 | 0.5835 | 0.3500 | 0.5385 | 0.4242 | 13 | 6 | 0.3714 | 0.4615 |
| strict_no_event20_no_event67 | 0.5000 | 0.5835 | 0.3500 | 0.5385 | 0.4242 | 13 | 6 | 0.3714 | 0.4615 |
| strict_no_event20_no_event67 | 0.6000 | 0.6121 | 0.3889 | 0.5385 | 0.4516 | 11 | 6 | 0.3143 | 0.4615 |

## 상위 feature 후보

| dataset_id | rank_abs_coefficient | feature | coefficient_mean | abs_coefficient_mean |
| --- | --- | --- | --- | --- |
| expanded_weak_positive | 1 | p_net_return_temperature__last_minus_first | -0.7727 | 0.7727 |
| expanded_weak_positive | 2 | p_hc1_return_temperature__min | -0.7028 | 0.7028 |
| expanded_weak_positive | 3 | s_hc1_supply_temperature_setpoint__min | 0.6756 | 0.6756 |
| expanded_weak_positive | 4 | p_hc1_return_temperature__last_minus_first | -0.6096 | 0.6096 |
| expanded_weak_positive | 5 | outdoor_temperature__max | 0.5705 | 0.5705 |
| expanded_weak_positive | 6 | s_hc1_supply_temperature__min | -0.5541 | 0.5541 |
| expanded_weak_positive | 7 | p_net_return_temperature__min | -0.4765 | 0.5236 |
| expanded_weak_positive | 8 | p_net_supply_temperature__min | -0.5023 | 0.5023 |
| strict_no_event20 | 1 | p_net_return_temperature__last_minus_first | -0.5137 | 0.5137 |
| strict_no_event20 | 2 | outdoor_temperature__last_minus_first | 0.4985 | 0.4985 |
| strict_no_event20 | 3 | p_hc1_return_temperature__last_minus_first | -0.3518 | 0.4760 |
| strict_no_event20 | 4 | p_net_supply_temperature__max | 0.4552 | 0.4552 |
| strict_no_event20 | 5 | p_net_supply_temperature__min | -0.4465 | 0.4465 |
| strict_no_event20 | 6 | s_hc1_supply_temperature__last_minus_first | -0.4407 | 0.4407 |
| strict_no_event20 | 7 | s_hc1_supply_temperature__min | -0.4315 | 0.4315 |
| strict_no_event20 | 8 | p_hc1_return_temperature__mean | 0.4299 | 0.4299 |
| strict_no_event20_no_event67 | 1 | s_hc1_supply_temperature__last_minus_first | -0.5183 | 0.5183 |
| strict_no_event20_no_event67 | 2 | p_hc1_return_temperature__std | 0.4692 | 0.4692 |
| strict_no_event20_no_event67 | 3 | p_net_return_temperature__std | 0.4654 | 0.4654 |
| strict_no_event20_no_event67 | 4 | p_net_return_temperature__min | -0.4644 | 0.4644 |
| strict_no_event20_no_event67 | 5 | p_net_return_temperature__last_minus_first | -0.4248 | 0.4433 |
| strict_no_event20_no_event67 | 6 | outdoor_temperature__max | 0.4314 | 0.4314 |
| strict_no_event20_no_event67 | 7 | p_net_meter_flow__min | -0.3544 | 0.4164 |
| strict_no_event20_no_event67 | 8 | p_hc1_return_temperature__last_minus_first | -0.3426 | 0.4080 |

## 해석

- weak positive는 strict positive와 섞지 않고 `label_strength`로 구분했다.
- unknown fault label은 빠른 확장 학습에서 제외했기 때문에 후속 검토가 필요하다.
- feature 중요도는 샘플이 적은 상태의 반복 검증 후보이며 확정 근거가 아니다.
- 다음 단계는 결과가 안정적이면 weak positive 정책을 문서화하고, 불안정하면 라벨 재검토 또는 feature 확장으로 넘어가는 것이다.

## 생성 파일

- `07_데이터산출물/m1_positive_expansion_audit.csv`
- `07_데이터산출물/m1_positive_expansion_features.csv`
- `07_데이터산출물/m1_positive_expansion_dataset_summary.csv`
- `07_데이터산출물/m1_positive_expansion_cv_metrics.csv`
- `07_데이터산출물/m1_positive_expansion_cv_predictions.csv`
- `07_데이터산출물/m1_positive_expansion_threshold_metrics.csv`
- `07_데이터산출물/m1_positive_expansion_feature_importance.csv`

## 한계와 주의점

- weak positive는 anomaly start가 없어 strict positive보다 라벨 신뢰도가 낮다.
- group CV는 누수를 줄이지만, positive 수가 여전히 작아 fold별 변동이 크다.
- 모델 파일 저장과 운영 threshold 확정은 이번 단계에 포함하지 않았다.