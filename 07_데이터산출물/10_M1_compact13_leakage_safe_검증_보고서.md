# M1 compact13 leakage-safe 검증 보고서

## 결론

- 최종 판단: compact13을 다음 학습 기준으로 유지
- 기준 라벨/window/threshold는 유지했다.
- main dataset은 `strict_no_event20`, sensitivity dataset은 `strict_no_event20_no_event67`이다.
- threshold는 0.6만 의사결정 기준으로 사용했다.
- 핵심 해석: fold별 train-only feature selection에서도 expanded154 대비 성능 하락 기준을 넘지 않았고, 오탐률도 악화되지 않았다. 따라서 compact13 계열을 다음 학습 기준 후보로 유지한다.

## 검증 질문

09번의 `compact13_overlap`은 성능이 가장 좋아 보였지만, 08번 전체 CV 중요도를 본 뒤 feature를 고른 post-hoc feature selection 결과였다.
이번 검증은 outer fold의 test fold를 feature 선택에 전혀 쓰지 않고도 compact13 계열 성능이 유지되는지 확인한다.

## 입력과 Dataset

| dataset_id | rows | normal_rows | positive_rows | event67_rows | fault_event20_rows | fault_event34_rows | fault_event69_rows | substation_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| strict_no_event20 | 49 | 35 | 14 | 1 | 0 | 0 | 0 | 29 |
| strict_no_event20_no_event67 | 48 | 35 | 13 | 0 | 0 | 0 | 0 | 29 |

## 방법

- `expanded154`: 08번의 확장 feature 전체 154개를 그대로 사용했다.
- `locked_compact13`: 09번에서 선택된 13개 feature를 고정해 재평가했다.
- `fold_selected_compact13`: 각 outer fold에서 train fold 안에서만 logistic coefficient importance를 계산하고 top13 feature를 선택했다.
- 모든 모델 평가는 `substation_id` 기준 group CV out-of-fold prediction으로 했다.
- metadata, 날짜, event id, `substation_id`, coverage 계열은 학습 입력으로 쓰지 않았다.

## Threshold 0.6 Decision Matrix

| dataset_id | feature_strategy | feature_count | balanced_accuracy | recall | f1 | false_positive_rate | fp | fn | ba_delta_vs_expanded154 | recall_delta_vs_expanded154 | fpr_delta_vs_expanded154 | mean_pairwise_jaccard | features_selected_in_at_least_3_folds | candidate_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict_no_event20 | expanded154 | 154 | 0.6500 | 0.5000 | 0.5000 | 0.2000 | 7 | 7 | 0.0000 | 0.0000 | 0.0000 |  |  |  |
| strict_no_event20 | fold_selected_compact13 | 13 | 0.7000 | 0.5714 | 0.5714 | 0.1714 | 6 | 6 | 0.0500 | 0.0714 | -0.0286 | 0.3406 | 9.0000 | True |
| strict_no_event20 | locked_compact13 | 13 | 0.8286 | 0.7143 | 0.7692 | 0.0571 | 2 | 4 | 0.1786 | 0.2143 | -0.1429 |  |  |  |
| strict_no_event20_no_event67 | expanded154 | 154 | 0.6593 | 0.4615 | 0.5000 | 0.1429 | 5 | 7 | 0.0000 | 0.0000 | 0.0000 |  |  |  |
| strict_no_event20_no_event67 | fold_selected_compact13 | 13 | 0.7648 | 0.6154 | 0.6667 | 0.0857 | 3 | 5 | 0.1055 | 0.1538 | -0.0571 | 0.3980 | 10.0000 | True |
| strict_no_event20_no_event67 | locked_compact13 | 13 | 0.8176 | 0.6923 | 0.7500 | 0.0571 | 2 | 4 | 0.1582 | 0.2308 | -0.0857 |  |  |  |

## Group CV 평균 성능

| dataset_id | feature_strategy | balanced_accuracy | precision | recall | f1 | roc_auc | fp | fn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict_no_event20 | expanded154 | 0.6446 | 0.5000 | 0.5000 | 0.4524 | 0.7123 | 1.4000 | 1.4000 |
| strict_no_event20 | fold_selected_compact13 | 0.7113 | 0.5300 | 0.6000 | 0.5000 | 0.7159 | 1.2000 | 1.2000 |
| strict_no_event20 | locked_compact13 | 0.8357 | 0.8333 | 0.7333 | 0.7400 | 0.9111 | 0.4000 | 0.8000 |
| strict_no_event20_no_event67 | expanded154 | 0.6429 | 0.3500 | 0.4333 | 0.3848 | 0.7135 | 1.0000 | 1.4000 |
| strict_no_event20_no_event67 | fold_selected_compact13 | 0.7381 | 0.6333 | 0.5667 | 0.5933 | 0.7452 | 0.6000 | 1.0000 |
| strict_no_event20_no_event67 | locked_compact13 | 0.8048 | 0.8500 | 0.6667 | 0.7248 | 0.8611 | 0.4000 | 0.8000 |

## Fold별 Feature 선택 안정성

| dataset_id | feature_strategy | mean_pairwise_jaccard | features_selected_in_at_least_3_folds | unique_selected_feature_count | max_feature_frequency |
| --- | --- | --- | --- | --- | --- |
| strict_no_event20 | fold_selected_compact13 | 0.3406 | 9 | 32 | 5 |
| strict_no_event20_no_event67 | fold_selected_compact13 | 0.3980 | 10 | 30 | 5 |

## Fold-selected 상위 선택 빈도

| dataset_id | feature | selected_fold_count |
| --- | --- | --- |
| strict_no_event20 | outdoor_temperature__last_12h_mean_minus_prev_12h_mean | 5 |
| strict_no_event20 | outdoor_temperature__last_6h_mean_minus_prev_6h_mean | 5 |
| strict_no_event20 | p_return_gap__last_1d_mean_minus_prev_6d_mean | 5 |
| strict_no_event20 | p_hc1_return_temperature__last_1d_mean_minus_prev_6d_mean | 4 |
| strict_no_event20 | p_net_return_temperature__last_1d_mean_minus_prev_6d_mean | 4 |
| strict_no_event20 | s_hc1_supply_temperature__last_1d_mean_minus_prev_6d_mean | 4 |
| strict_no_event20 | s_hc1_supply_temperature_setpoint__last_1d_mean_minus_prev_6d_mean | 4 |
| strict_no_event20 | p_net_meter_flow__last_1d_std_minus_prev_6d_std | 3 |
| strict_no_event20 | s_hc1_supply_temperature__last_1d_std_minus_prev_6d_std | 3 |
| strict_no_event20 | outdoor_temperature__last_minus_first | 2 |
| strict_no_event20_no_event67 | outdoor_temperature__last_6h_mean_minus_prev_6h_mean | 5 |
| strict_no_event20_no_event67 | p_net_return_temperature__last_1d_mean_minus_prev_6d_mean | 5 |
| strict_no_event20_no_event67 | p_return_gap__last_1d_mean_minus_prev_6d_mean | 5 |
| strict_no_event20_no_event67 | p_hc1_return_temperature__last_1d_mean_minus_prev_6d_mean | 4 |
| strict_no_event20_no_event67 | p_net_meter_flow__last_1d_std_minus_prev_6d_std | 4 |
| strict_no_event20_no_event67 | s_hc1_supply_temperature__last_1d_mean_minus_prev_6d_mean | 4 |
| strict_no_event20_no_event67 | s_hc1_supply_temperature__last_1d_std_minus_prev_6d_std | 4 |
| strict_no_event20_no_event67 | s_hc1_supply_temperature_setpoint__last_1d_mean_minus_prev_6d_mean | 4 |
| strict_no_event20_no_event67 | outdoor_temperature__last_12h_mean_minus_prev_12h_mean | 3 |
| strict_no_event20_no_event67 | s_hc1_supply_temperature_error__last_minus_first | 3 |

## 오분류 요약

| dataset_id | feature_strategy | FP | FN |
| --- | --- | --- | --- |
| strict_no_event20 | expanded154 | 7 | 7 |
| strict_no_event20 | fold_selected_compact13 | 6 | 6 |
| strict_no_event20 | locked_compact13 | 2 | 4 |
| strict_no_event20_no_event67 | expanded154 | 5 | 7 |
| strict_no_event20_no_event67 | fold_selected_compact13 | 3 | 5 |
| strict_no_event20_no_event67 | locked_compact13 | 2 | 4 |

## 생성 이미지

- `07_데이터산출물/m1_compact13_selected_feature_frequency.png`
- `07_데이터산출물/m1_compact13_misclassification_heatmap.png`

## 검증 결과

- Event 20/34/69는 학습 dataset에 없다.
- Event 67은 `strict_no_event20`에만 있고 `strict_no_event20_no_event67`에는 없다.
- group CV에서 같은 `substation_id`가 train/test에 동시에 들어가지 않았다.
- `fold_selected_compact13`의 feature selection은 `train_fold_only`로 기록했고, `used_test_fold_in_selection=False`로 검증했다.
- misclassification audit에는 threshold 0.6 기준 FP/FN 이벤트를 기록했다.

## 한계와 주의점

- 샘플 수가 여전히 작기 때문에 이번 결과도 운영 모델 확정 근거가 아니라 다음 학습 기준 후보를 고르는 근거다.
- `fold_selected_compact13`은 test fold 누수는 막았지만, feature 선택 규칙 자체는 아직 logistic coefficient에 의존한다.
- 모델 파일 저장이나 운영 배포는 하지 않았다.

## 다음 단계

- 이번 기준이 통과하면 `compact13 + threshold 0.6`으로 모델 해석과 오분류 이벤트 리뷰를 진행한다.
- 기준이 통과하지 못하면 compact 확정은 보류하고 expanded154 유지 또는 normal negative 재설계를 먼저 검토한다.
