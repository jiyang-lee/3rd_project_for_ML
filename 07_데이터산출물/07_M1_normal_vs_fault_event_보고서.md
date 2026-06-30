# M1 normal vs fault event 보고서

## 결론

- 이번 실험은 조기탐지가 아니라 `normal`과 `fault_event` 상태를 구분하는 재라벨링 실험이다.
- `fault_event`는 M1 `faults.csv`에 존재하는 fault record로 정의했다.
- `unknown` fault label은 negative나 비라벨 이벤트로 단정하지 않았다. Event 34는 `fault_label_unknown=True`인 fault event로 audit에 기록했고, 포함/제외 민감도로만 판단했다.
- Event 20은 7일 window coverage가 낮아 학습에서 제외하고 audit에만 남겼다.
- Event 69는 요청 기준에 따라 학습에서 제외하고 audit에만 남겼다.
- 현재 최고 평균 balanced accuracy dataset은 `fault_event_known_only`이며, logistic 평균 balanced accuracy는 0.5363, 평균 f1은 0.4824이다.
- Event 34 판단: Event 34 audit 전용 유지 권장. 포함 시 balanced accuracy 변화는 -0.1197, threshold 0.5 false positive rate 변화는 +0.0286이다.
- Event 67 제외 민감도: `fault_event_with_unknown34` 대비 balanced accuracy 변화는 +0.0137이다.
- 최종 판단은 목표 전환 보류다. `fault_event_known_only`만 Dummy보다 소폭 개선됐고, Event 34 포함 dataset과 Event 67 제외 dataset은 모두 불안정했다. 기존 expanded weak positive 기준보다 threshold 0.5 성능도 좋아지지 않아 다음 단계는 모델 변경보다 feature 확장 또는 normal negative 재설계가 우선이다.

## 데이터 구성

| 항목 | 값 |
|---|---:|
| M1 fault audit row | 33 |
| normal reference row | 35 |
| feature pool row | 66 |
| 학습 feature 수 | 70 |
| 센서 수 | 10 |
| 통계 수 | 7 |

## Dataset Summary

| dataset_id | rows | normal_rows | positive_rows | positive_event_ids | contains_event20 | contains_event34 | contains_event67 | contains_event69 | unknown_fault_rows | incomplete_training_metadata_rows | min_coverage_rate | median_coverage_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fault_event_known_only | 65 | 35 | 30 | 1\|3\|5\|6\|7\|10\|11\|13\|15\|23\|24\|29\|32\|36\|37\|38\|40\|44\|45\|47\|49\|52\|53\|57\|60\|62\|63\|64\|65\|67 | False | False | True | False | 0 | 4 | 0.9950 | 1.0000 |
| fault_event_with_unknown34 | 66 | 35 | 31 | 1\|3\|5\|6\|7\|10\|11\|13\|15\|23\|24\|29\|32\|34\|36\|37\|38\|40\|44\|45\|47\|49\|52\|53\|57\|60\|62\|63\|64\|65\|67 | False | True | True | False | 1 | 4 | 0.9950 | 1.0000 |
| fault_event_no_event67 | 65 | 35 | 30 | 1\|3\|5\|6\|7\|10\|11\|13\|15\|23\|24\|29\|32\|34\|36\|37\|38\|40\|44\|45\|47\|49\|52\|53\|57\|60\|62\|63\|64\|65 | False | True | False | False | 1 | 4 | 0.9950 | 1.0000 |

## Group CV 평균 성능

| dataset_id | model | balanced_accuracy | precision | recall | f1 | roc_auc | fp | fn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fault_event_known_only | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 6.0000 |
| fault_event_known_only | logistic_balanced | 0.5363 | 0.5022 | 0.5171 | 0.4824 | 0.5305 | 3.2000 | 3.0000 |
| fault_event_no_event67 | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 6.0000 |
| fault_event_no_event67 | logistic_balanced | 0.4304 | 0.3581 | 0.4000 | 0.3737 | 0.3966 | 3.8000 | 3.6000 |
| fault_event_with_unknown34 | dummy_most_frequent | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 6.2000 |
| fault_event_with_unknown34 | logistic_balanced | 0.4167 | 0.3343 | 0.3190 | 0.3231 | 0.3748 | 3.4000 | 4.2000 |

## Threshold 0.3~0.6 성능

| accuracy | balanced_accuracy | precision | recall | f1 | roc_auc | tn | fp | fn | tp | dataset_id | model | threshold | rows | normal_rows | positive_rows | false_positive_rate | false_negative_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.5077 | 0.5214 | 0.4773 | 0.7000 | 0.5676 | 0.5343 | 12 | 23 | 9 | 21 | fault_event_known_only | logistic_balanced | 0.3 | 65 | 35 | 30 | 0.6571 | 0.3000 |
| 0.5231 | 0.5262 | 0.4857 | 0.5667 | 0.5231 | 0.5343 | 17 | 18 | 13 | 17 | fault_event_known_only | logistic_balanced | 0.4 | 65 | 35 | 30 | 0.5143 | 0.4333 |
| 0.5231 | 0.5214 | 0.4839 | 0.5000 | 0.4918 | 0.5343 | 19 | 16 | 15 | 15 | fault_event_known_only | logistic_balanced | 0.5 | 65 | 35 | 30 | 0.4571 | 0.5000 |
| 0.5231 | 0.5167 | 0.4815 | 0.4333 | 0.4561 | 0.5343 | 21 | 14 | 17 | 13 | fault_event_known_only | logistic_balanced | 0.6 | 65 | 35 | 30 | 0.4000 | 0.5667 |
| 0.4000 | 0.4095 | 0.3902 | 0.5333 | 0.4507 | 0.3829 | 10 | 25 | 14 | 16 | fault_event_no_event67 | logistic_balanced | 0.3 | 65 | 35 | 30 | 0.7143 | 0.4667 |
| 0.4000 | 0.4048 | 0.3784 | 0.4667 | 0.4179 | 0.3829 | 12 | 23 | 16 | 14 | fault_event_no_event67 | logistic_balanced | 0.4 | 65 | 35 | 30 | 0.6571 | 0.5333 |
| 0.4308 | 0.4286 | 0.3871 | 0.4000 | 0.3934 | 0.3829 | 16 | 19 | 18 | 12 | fault_event_no_event67 | logistic_balanced | 0.5 | 65 | 35 | 30 | 0.5429 | 0.6000 |
| 0.3846 | 0.3762 | 0.3077 | 0.2667 | 0.2857 | 0.3829 | 17 | 18 | 22 | 8 | fault_event_no_event67 | logistic_balanced | 0.6 | 65 | 35 | 30 | 0.5143 | 0.7333 |
| 0.3939 | 0.3972 | 0.3784 | 0.4516 | 0.4118 | 0.3889 | 12 | 23 | 17 | 14 | fault_event_with_unknown34 | logistic_balanced | 0.3 | 66 | 35 | 31 | 0.6571 | 0.5484 |
| 0.3788 | 0.3774 | 0.3438 | 0.3548 | 0.3492 | 0.3889 | 14 | 21 | 20 | 11 | fault_event_with_unknown34 | logistic_balanced | 0.4 | 66 | 35 | 31 | 0.6000 | 0.6452 |
| 0.4242 | 0.4184 | 0.3704 | 0.3226 | 0.3448 | 0.3889 | 18 | 17 | 21 | 10 | fault_event_with_unknown34 | logistic_balanced | 0.5 | 66 | 35 | 31 | 0.4857 | 0.6774 |
| 0.4394 | 0.4327 | 0.3846 | 0.3226 | 0.3509 | 0.3889 | 19 | 16 | 21 | 10 | fault_event_with_unknown34 | logistic_balanced | 0.6 | 66 | 35 | 31 | 0.4571 | 0.6774 |

## Decision Matrix

| dataset_id | rows | normal_rows | positive_rows | contains_event34 | contains_event67 | dummy_balanced_accuracy_mean | logistic_balanced_accuracy_mean | balanced_accuracy_lift_vs_dummy | logistic_precision_mean | logistic_recall_mean | logistic_f1_mean | logistic_roc_auc_mean | threshold05_false_positive_rate | threshold05_false_negative_rate | unknown_fault_rows | incomplete_training_metadata_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fault_event_known_only | 65 | 35 | 30 | False | True | 0.5000 | 0.5363 | 0.0363 | 0.5022 | 0.5171 | 0.4824 | 0.5305 | 0.4571 | 0.5000 | 0 | 4 |
| fault_event_with_unknown34 | 66 | 35 | 31 | True | True | 0.5000 | 0.4167 | -0.0833 | 0.3343 | 0.3190 | 0.3231 | 0.3748 | 0.4857 | 0.6774 | 1 | 4 |
| fault_event_no_event67 | 65 | 35 | 30 | True | False | 0.5000 | 0.4304 | -0.0696 | 0.3581 | 0.4000 | 0.3737 | 0.3966 | 0.5429 | 0.6000 | 1 | 4 |

## 이전 확장 positive 실험과의 참고 비교

기존 expanded weak positive의 threshold 0.5 balanced accuracy는 0.5549, f1은 0.5091, false positive rate는 0.4286였다. 이번 best dataset(fault_event_known_only)의 threshold 0.5 balanced accuracy는 0.5214, f1은 0.4918, false positive rate는 0.4571이다.

## 주요 feature 후보

| dataset_id | feature | mean_coefficient | mean_abs_coefficient | std_coefficient |
| --- | --- | --- | --- | --- |
| fault_event_known_only | p_hc1_return_temperature__min | -0.7593 | 0.7593 | 0.0800 |
| fault_event_known_only | s_hc1_supply_temperature__std | -0.6954 | 0.6954 | 0.3202 |
| fault_event_known_only | p_net_return_temperature__min | -0.6118 | 0.6332 | 0.3813 |
| fault_event_known_only | p_net_supply_temperature__min | -0.5992 | 0.5992 | 0.1864 |
| fault_event_known_only | p_hc1_return_temperature__last_minus_first | -0.5874 | 0.5874 | 0.3898 |
| fault_event_known_only | p_hc1_return_temperature__std | 0.5510 | 0.5510 | 0.2348 |
| fault_event_known_only | p_net_return_temperature__last_minus_first | -0.5362 | 0.5362 | 0.2904 |
| fault_event_known_only | p_net_meter_flow__min | 0.5066 | 0.5066 | 0.2603 |
| fault_event_no_event67 | p_net_return_temperature__min | -0.6827 | 0.6890 | 0.5100 |
| fault_event_no_event67 | s_hc1_supply_temperature_setpoint__min | 0.5999 | 0.5999 | 0.2883 |
| fault_event_no_event67 | p_net_return_temperature__last_minus_first | -0.5763 | 0.5763 | 0.2378 |
| fault_event_no_event67 | p_hc1_return_temperature__min | -0.5342 | 0.5342 | 0.0821 |
| fault_event_no_event67 | p_net_supply_temperature__min | -0.5128 | 0.5128 | 0.2487 |
| fault_event_no_event67 | p_net_meter_flow__std | -0.5029 | 0.5029 | 0.1634 |
| fault_event_no_event67 | s_hc1_supply_temperature_setpoint__last_minus_first | -0.2601 | 0.4907 | 0.5077 |
| fault_event_no_event67 | p_net_meter_flow__min | 0.4726 | 0.4726 | 0.3698 |
| fault_event_with_unknown34 | p_hc1_return_temperature__min | -0.6669 | 0.6669 | 0.2426 |
| fault_event_with_unknown34 | s_hc1_supply_temperature_setpoint__min | 0.5961 | 0.6314 | 0.4390 |
| fault_event_with_unknown34 | p_net_return_temperature__min | -0.5792 | 0.6181 | 0.4079 |
| fault_event_with_unknown34 | p_hc1_return_temperature__last_minus_first | -0.5952 | 0.5952 | 0.1499 |
| fault_event_with_unknown34 | s_hc1_supply_temperature_setpoint__median | -0.5500 | 0.5500 | 0.2245 |
| fault_event_with_unknown34 | p_net_return_temperature__last_minus_first | -0.5158 | 0.5158 | 0.3232 |
| fault_event_with_unknown34 | p_net_meter_flow__min | 0.5004 | 0.5004 | 0.2777 |
| fault_event_with_unknown34 | s_hc1_supply_temperature_setpoint__std | -0.4934 | 0.4934 | 0.1474 |

## Audit 해석 메모

- Event 34는 `fault_label_unknown=True`이고 7일 window coverage가 1.0000이다.
- Event 67은 장기 anomaly flag로만 기록했고, 학습 metadata로 모델 입력에는 넣지 않았다.
- Training metadata 불완전 fault event ID는 [11, 36, 60, 63, 69]이다. 이번 실험에서는 요청된 Event 69만 학습 제외로 고정하고, 나머지는 `training_metadata_complete=False`로 audit에 남겼다.
- fault metadata, 날짜, event id, `substation_id`, coverage는 학습 입력에서 제외했다.

## 생성 산출물

- `06_노트북/07_m1_normal_vs_fault_event_training.ipynb`
- `07_데이터산출물/m1_fault_event_audit.csv`
- `07_데이터산출물/m1_fault_event_features.csv`
- `07_데이터산출물/m1_fault_event_dataset_summary.csv`
- `07_데이터산출물/m1_fault_event_cv_metrics.csv`
- `07_데이터산출물/m1_fault_event_cv_predictions.csv`
- `07_데이터산출물/m1_fault_event_threshold_metrics.csv`
- `07_데이터산출물/m1_fault_event_feature_importance.csv`
- `07_데이터산출물/m1_fault_event_decision_matrix.csv`

## 검증 결과

- M1 `faults.csv` 전체 33건을 audit에 기록했다.
- Event 20과 Event 69는 학습 dataset에서 제외되고 audit에만 남았다.
- Event 34는 audit에 `fault_label_unknown=True`로 기록되며, `fault_event_known_only`에서는 제외되고 `fault_event_with_unknown34`에는 포함된다.
- `fault_event_known_only`: normal 35 + positive 30
- `fault_event_with_unknown34`: normal 35 + positive 31
- `fault_event_no_event67`: normal 35 + positive 30
- group CV에서 같은 `substation_id`가 train/test에 동시에 들어가지 않음을 fold별 assert로 확인했다.
- 학습 입력은 M1 공통 10개 센서 기반 70개 feature만 사용했다.