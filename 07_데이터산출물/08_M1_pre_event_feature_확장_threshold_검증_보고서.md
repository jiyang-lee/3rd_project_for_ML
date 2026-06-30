# M1 pre-event feature 확장 threshold 검증 보고서

## 결론

- 질문: 라벨은 그대로 잠그고 threshold 0.6 기준에서 feature 확장만 했을 때 성능이 좋아지는가?
- 결론: feature 확장만으로는 부족, normal negative 재설계 또는 센서 컬럼 확장 필요.
- 개선은 있었다. 다만 main dataset의 balanced accuracy 개선폭이 사전 채택 기준 `+0.0300`에 비해 +0.0014만큼 부족해 자동 채택으로 보지는 않았다.
- main dataset `strict_no_event20`의 threshold 0.6 balanced accuracy 변화는 +0.0286, recall 변화는 +0.0000, false positive rate 변화는 -0.0571이다.
- Event 67 제외 민감도 dataset의 threshold 0.6 balanced accuracy 변화는 +0.0473이다.
- 이번 실험은 모델 고도화가 아니라 feature 확장 효과 검증이며, `normal vs fault_event` 전환은 보류했다.

## 데이터 구성

| 항목 | 값 |
|---|---:|
| accepted normal rows | 35 |
| accepted positive rows | 14 |
| audit positive rows | 17 |
| base feature count | 70 |
| expanded feature count | 154 |
| decision threshold | 0.6 |

## Dataset Summary

| dataset_id | rows | normal_rows | positive_rows | positive_event_ids | event20_included | event34_included | event67_included | event69_included | base_feature_count | expanded_feature_count | coverage_min | coverage_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict_no_event20 | 49 | 35 | 14 | 1,3,7,10,15,40,44,47,49,52,53,57,64,67 | False | False | True | False | 70 | 154 | 0.9950 | 1.0000 |
| strict_no_event20_no_event67 | 48 | 35 | 13 | 1,3,7,10,15,40,44,47,49,52,53,57,64 | False | False | False | False | 70 | 154 | 0.9950 | 1.0000 |

## Threshold 0.6 Decision Matrix

| dataset_id | threshold | base_balanced_accuracy | expanded_balanced_accuracy | balanced_accuracy_delta | base_recall | expanded_recall | recall_delta | base_false_positive_rate | expanded_false_positive_rate | false_positive_rate_delta | base_f1 | expanded_f1 | f1_delta | base_fp | expanded_fp | base_fn | expanded_fn | passes_main_bacc | passes_main_recall | passes_main_fpr | passes_sensitivity_bacc | feature_expansion_adopted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict_no_event20 | 0.6 | 0.6214 | 0.6500 | 0.0286 | 0.5000 | 0.5000 | 0.0000 | 0.2571 | 0.2000 | -0.0571 | 0.4667 | 0.5000 | 0.0333 | 9 | 7 | 7 | 7 | False | True | True | False | False |
| strict_no_event20_no_event67 | 0.6 | 0.6121 | 0.6593 | 0.0473 | 0.5385 | 0.4615 | -0.0769 | 0.3143 | 0.1429 | -0.1714 | 0.4516 | 0.5000 | 0.0484 | 11 | 5 | 6 | 7 | False | False | False | True | False |

## Group CV 평균 성능

| dataset_id | feature_set | model | balanced_accuracy | precision | recall | f1 | roc_auc | fp | fn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict_no_event20 | base70 | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.8000 |
| strict_no_event20 | base70 | logistic_balanced | 0.5738 | 0.3000 | 0.5000 | 0.3714 | 0.6024 | 2.4000 | 1.4000 |
| strict_no_event20 | expanded154 | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.8000 |
| strict_no_event20 | expanded154 | logistic_balanced | 0.6220 | 0.3600 | 0.5667 | 0.4205 | 0.7123 | 2.2000 | 1.2000 |
| strict_no_event20_no_event67 | base70 | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.6000 |
| strict_no_event20_no_event67 | base70 | logistic_balanced | 0.5821 | 0.3333 | 0.5333 | 0.4024 | 0.5813 | 2.6000 | 1.2000 |
| strict_no_event20_no_event67 | expanded154 | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 2.6000 |
| strict_no_event20_no_event67 | expanded154 | logistic_balanced | 0.6810 | 0.5033 | 0.5667 | 0.5100 | 0.7135 | 1.4000 | 1.0000 |

## Threshold 0.4~0.7 성능

| accuracy | balanced_accuracy | precision | recall | f1 | roc_auc | tn | fp | fn | tp | dataset_id | feature_set | model | threshold | rows | normal_rows | positive_rows | false_positive_rate | false_negative_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.5510 | 0.5357 | 0.3182 | 0.5000 | 0.3889 | 0.6041 | 20 | 15 | 7 | 7 | strict_no_event20 | base70 | logistic_balanced | 0.4 | 49 | 35 | 14 | 0.4286 | 0.5000 |
| 0.6122 | 0.5786 | 0.3684 | 0.5000 | 0.4242 | 0.6041 | 23 | 12 | 7 | 7 | strict_no_event20 | base70 | logistic_balanced | 0.5 | 49 | 35 | 14 | 0.3429 | 0.5000 |
| 0.6735 | 0.6214 | 0.4375 | 0.5000 | 0.4667 | 0.6041 | 26 | 9 | 7 | 7 | strict_no_event20 | base70 | logistic_balanced | 0.6 | 49 | 35 | 14 | 0.2571 | 0.5000 |
| 0.6735 | 0.6000 | 0.4286 | 0.4286 | 0.4286 | 0.6041 | 27 | 8 | 8 | 6 | strict_no_event20 | base70 | logistic_balanced | 0.7 | 49 | 35 | 14 | 0.2286 | 0.5714 |
| 0.6122 | 0.6000 | 0.3810 | 0.5714 | 0.4571 | 0.6776 | 22 | 13 | 6 | 8 | strict_no_event20 | expanded154 | logistic_balanced | 0.4 | 49 | 35 | 14 | 0.3714 | 0.4286 |
| 0.6531 | 0.6286 | 0.4211 | 0.5714 | 0.4848 | 0.6776 | 24 | 11 | 6 | 8 | strict_no_event20 | expanded154 | logistic_balanced | 0.5 | 49 | 35 | 14 | 0.3143 | 0.4286 |
| 0.7143 | 0.6500 | 0.5000 | 0.5000 | 0.5000 | 0.6776 | 28 | 7 | 7 | 7 | strict_no_event20 | expanded154 | logistic_balanced | 0.6 | 49 | 35 | 14 | 0.2000 | 0.5000 |
| 0.7143 | 0.6286 | 0.5000 | 0.4286 | 0.4615 | 0.6776 | 29 | 6 | 8 | 6 | strict_no_event20 | expanded154 | logistic_balanced | 0.7 | 49 | 35 | 14 | 0.1714 | 0.5714 |
| 0.6042 | 0.5835 | 0.3500 | 0.5385 | 0.4242 | 0.6484 | 22 | 13 | 6 | 7 | strict_no_event20_no_event67 | base70 | logistic_balanced | 0.4 | 48 | 35 | 13 | 0.3714 | 0.4615 |
| 0.6042 | 0.5835 | 0.3500 | 0.5385 | 0.4242 | 0.6484 | 22 | 13 | 6 | 7 | strict_no_event20_no_event67 | base70 | logistic_balanced | 0.5 | 48 | 35 | 13 | 0.3714 | 0.4615 |
| 0.6458 | 0.6121 | 0.3889 | 0.5385 | 0.4516 | 0.6484 | 24 | 11 | 6 | 7 | strict_no_event20_no_event67 | base70 | logistic_balanced | 0.6 | 48 | 35 | 13 | 0.3143 | 0.4615 |
| 0.6667 | 0.6022 | 0.4000 | 0.4615 | 0.4286 | 0.6484 | 26 | 9 | 7 | 6 | strict_no_event20_no_event67 | base70 | logistic_balanced | 0.7 | 48 | 35 | 13 | 0.2571 | 0.5385 |
| 0.7292 | 0.7176 | 0.5000 | 0.6923 | 0.5806 | 0.7385 | 26 | 9 | 4 | 9 | strict_no_event20_no_event67 | expanded154 | logistic_balanced | 0.4 | 48 | 35 | 13 | 0.2571 | 0.3077 |
| 0.7500 | 0.7077 | 0.5333 | 0.6154 | 0.5714 | 0.7385 | 28 | 7 | 5 | 8 | strict_no_event20_no_event67 | expanded154 | logistic_balanced | 0.5 | 48 | 35 | 13 | 0.2000 | 0.3846 |
| 0.7500 | 0.6593 | 0.5455 | 0.4615 | 0.5000 | 0.7385 | 30 | 5 | 7 | 6 | strict_no_event20_no_event67 | expanded154 | logistic_balanced | 0.6 | 48 | 35 | 13 | 0.1429 | 0.5385 |
| 0.7500 | 0.6352 | 0.5556 | 0.3846 | 0.4545 | 0.7385 | 31 | 4 | 8 | 5 | strict_no_event20_no_event67 | expanded154 | logistic_balanced | 0.7 | 48 | 35 | 13 | 0.1143 | 0.6154 |

## Expanded Feature 중요도 상위 후보

| dataset_id | feature_set | feature | signal | stat | mean_coefficient | mean_abs_coefficient | std_coefficient |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict_no_event20 | expanded154 | outdoor_temperature__last_6h_mean_minus_prev_6h_mean | outdoor_temperature | last_6h_mean_minus_prev_6h_mean | 0.7623 | 0.7623 | 0.1929 |
| strict_no_event20 | expanded154 | p_return_gap__last_1d_mean_minus_prev_6d_mean | p_return_gap | last_1d_mean_minus_prev_6d_mean | 0.6156 | 0.6156 | 0.0558 |
| strict_no_event20 | expanded154 | p_net_return_temperature__last_1d_mean_minus_prev_6d_mean | p_net_return_temperature | last_1d_mean_minus_prev_6d_mean | -0.3966 | 0.3966 | 0.0925 |
| strict_no_event20 | expanded154 | p_hc1_return_temperature__last_1d_mean_minus_prev_6d_mean | p_hc1_return_temperature | last_1d_mean_minus_prev_6d_mean | -0.3696 | 0.3696 | 0.1047 |
| strict_no_event20 | expanded154 | outdoor_temperature__last_12h_mean_minus_prev_12h_mean | outdoor_temperature | last_12h_mean_minus_prev_12h_mean | -0.3467 | 0.3467 | 0.0490 |
| strict_no_event20 | expanded154 | s_hc1_supply_temperature__last_1d_std_minus_prev_6d_std | s_hc1_supply_temperature | last_1d_std_minus_prev_6d_std | -0.3350 | 0.3350 | 0.1971 |
| strict_no_event20 | expanded154 | s_hc1_supply_temperature__last_1d_mean_minus_prev_6d_mean | s_hc1_supply_temperature | last_1d_mean_minus_prev_6d_mean | -0.3237 | 0.3237 | 0.1276 |
| strict_no_event20 | expanded154 | s_hc1_supply_temperature_setpoint__last_1d_mean_minus_prev_6d_mean | s_hc1_supply_temperature_setpoint | last_1d_mean_minus_prev_6d_mean | -0.3173 | 0.3173 | 0.0899 |
| strict_no_event20 | expanded154 | p_net_meter_flow__last_1d_std_minus_prev_6d_std | p_net_meter_flow | last_1d_std_minus_prev_6d_std | -0.2977 | 0.2977 | 0.0292 |
| strict_no_event20 | expanded154 | s_hc1_supply_temperature__last_6h_mean_minus_prev_6h_mean | s_hc1_supply_temperature | last_6h_mean_minus_prev_6h_mean | -0.2451 | 0.2921 | 0.2192 |
| strict_no_event20_no_event67 | expanded154 | p_return_gap__last_1d_mean_minus_prev_6d_mean | p_return_gap | last_1d_mean_minus_prev_6d_mean | 0.6316 | 0.6316 | 0.1423 |
| strict_no_event20_no_event67 | expanded154 | outdoor_temperature__last_6h_mean_minus_prev_6h_mean | outdoor_temperature | last_6h_mean_minus_prev_6h_mean | 0.6176 | 0.6176 | 0.1400 |
| strict_no_event20_no_event67 | expanded154 | p_net_return_temperature__last_1d_mean_minus_prev_6d_mean | p_net_return_temperature | last_1d_mean_minus_prev_6d_mean | -0.3551 | 0.3551 | 0.0654 |
| strict_no_event20_no_event67 | expanded154 | p_net_meter_flow__last_1d_std_minus_prev_6d_std | p_net_meter_flow | last_1d_std_minus_prev_6d_std | -0.3509 | 0.3509 | 0.0803 |
| strict_no_event20_no_event67 | expanded154 | outdoor_temperature__last_12h_mean_minus_prev_12h_mean | outdoor_temperature | last_12h_mean_minus_prev_12h_mean | -0.3268 | 0.3268 | 0.0812 |
| strict_no_event20_no_event67 | expanded154 | p_hc1_return_temperature__last_1d_mean_minus_prev_6d_mean | p_hc1_return_temperature | last_1d_mean_minus_prev_6d_mean | -0.3163 | 0.3163 | 0.1308 |
| strict_no_event20_no_event67 | expanded154 | s_hc1_supply_temperature_setpoint__last_1d_mean_minus_prev_6d_mean | s_hc1_supply_temperature_setpoint | last_1d_mean_minus_prev_6d_mean | -0.3133 | 0.3133 | 0.0756 |
| strict_no_event20_no_event67 | expanded154 | s_hc1_supply_temperature__last_1d_mean_minus_prev_6d_mean | s_hc1_supply_temperature | last_1d_mean_minus_prev_6d_mean | -0.3111 | 0.3111 | 0.1018 |
| strict_no_event20_no_event67 | expanded154 | s_hc1_supply_temperature__last_1d_std_minus_prev_6d_std | s_hc1_supply_temperature | last_1d_std_minus_prev_6d_std | -0.3076 | 0.3076 | 0.1651 |
| strict_no_event20_no_event67 | expanded154 | p_net_supply_temperature__last_minus_first | p_net_supply_temperature | last_minus_first | -0.2626 | 0.2626 | 0.1262 |

## 해석

- `base70`과 `expanded154`는 같은 label/window/dataset split에서 비교했다.
- 학습 입력에서는 metadata, 날짜, event id, `substation_id`, `coverage_rate`, `sample_count`, label strength를 제외했다.
- Event 20, 34, 69는 어떤 학습 dataset에도 포함하지 않았다.
- threshold 0.6은 최종 운영값이 아니라 기존 baseline에서 recall 유지와 false positive 감소가 동시에 나온 비교 기준이다.

## 생성 산출물

- `06_노트북/08_m1_pre_event_feature_expansion_threshold_validation.ipynb`
- `07_데이터산출물/m1_feature_expansion_audit.csv`
- `07_데이터산출물/m1_feature_expansion_features.csv`
- `07_데이터산출물/m1_feature_expansion_dataset_summary.csv`
- `07_데이터산출물/m1_feature_expansion_cv_metrics.csv`
- `07_데이터산출물/m1_feature_expansion_cv_predictions.csv`
- `07_데이터산출물/m1_feature_expansion_threshold_metrics.csv`
- `07_데이터산출물/m1_feature_expansion_feature_importance.csv`
- `07_데이터산출물/m1_feature_expansion_decision_matrix.csv`