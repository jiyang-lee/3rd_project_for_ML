# M1 hard normal false positive 보고서

## 결론

- 최종 판단: 특정 substation/window에 FP가 몰려 추가 검토 필요
- 회사 제공 normal 라벨은 그대로 유지한다.
- 이번 단계에서는 normal을 삭제하거나 재라벨링하지 않았다.
- main 기준 hard normal은 8건이다.
- high severity는 0건, medium severity는 8건이다.
- 판단 근거: hard normal이 일부 substation에 2건 이상 몰려 있어 설비별 정상 패턴 차이를 확인해야 한다.

## 검증 질문

`compact13 + threshold 0.6`에서 정상인데 위험처럼 잡히는 normal 이벤트가 어떤 것인지 확인했다.
분석 기준은 기존 10번 out-of-fold prediction이며, 새 모델 학습은 하지 않았다.

## Hard Normal 정의

- `locked_compact13` 또는 `fold_selected_compact13` 중 하나라도 threshold 0.6에서 FP이면 `hard_normal=True`로 기록했다.
- 두 compact 전략 모두 FP이면 `high`, 하나만 FP이면 `medium`으로 기록했다.
- `expanded154` FP 여부는 참고로만 함께 남겼다.

## Hard Normal 목록

| source_event_id | substation_id | locked_compact13_probability | fold_selected_compact13_probability | expanded154_probability | fp_count_across_strategies | hard_normal_severity | hard_normal_strategy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | 6 | 0.0802 | 0.9553 | 0.9726 | 2 | medium | fold_selected_compact13 |
| 19 | 8 | 0.2752 | 0.8767 | 0.9054 | 2 | medium | fold_selected_compact13 |
| 27 | 12 | 0.6036 | 0.4583 | 0.1941 | 1 | medium | locked_compact13 |
| 33 | 3 | 0.5148 | 0.6351 | 0.8327 | 2 | medium | fold_selected_compact13 |
| 35 | 11 | 0.4407 | 0.9975 | 0.5252 | 1 | medium | fold_selected_compact13 |
| 39 | 15 | 0.0929 | 0.8751 | 0.8941 | 2 | medium | fold_selected_compact13 |
| 48 | 11 | 0.0501 | 0.7753 | 0.7584 | 2 | medium | fold_selected_compact13 |
| 68 | 13 | 0.6884 | 0.4969 | 0.9293 | 2 | medium | locked_compact13 |

## Feature Profile 상위 차이

| feature | all_normal_mean | hard_normal_mean | true_negative_normal_mean | positive_mean | abs_hard_minus_true_negative |
| --- | --- | --- | --- | --- | --- |
| p_net_meter_flow__last_1d_std_minus_prev_6d_std | -22.3849 | -54.1785 | -12.9645 | -131.5715 | 41.2140 |
| s_hc1_supply_temperature_error__last_minus_first | -1.5642 | -6.0712 | -0.2288 | -5.6200 | 5.8425 |
| outdoor_temperature__last_minus_first | -1.9189 | 0.0625 | -2.5060 | 0.1881 | 2.5685 |
| s_hc1_supply_temperature_setpoint__last_1d_mean_minus_prev_6d_mean | 1.8246 | 3.5173 | 1.3231 | -5.3618 | 2.1942 |
| p_return_gap__last_minus_first | 0.4819 | -0.5065 | 0.7748 | 4.7944 | 1.2813 |
| outdoor_temperature__last_12h_mean_minus_prev_12h_mean | 1.3698 | 0.5813 | 1.6035 | -1.0089 | 1.0223 |
| s_hc1_supply_temperature__last_1d_mean_minus_prev_6d_mean | 1.1664 | 0.4884 | 1.3673 | -4.3171 | 0.8790 |
| outdoor_temperature__last_6h_mean_minus_prev_6h_mean | -1.7629 | -1.1473 | -1.9452 | 1.2157 | 0.7980 |

## Substation 분포

| substation_id | normal_event_count | hard_normal_count | high_severity_count | medium_severity_count | hard_normal_event_ids |
| --- | --- | --- | --- | --- | --- |
| 11 | 2 | 2 | 0 | 2 | 35\|48 |
| 6 | 1 | 1 | 0 | 1 | 8 |
| 8 | 1 | 1 | 0 | 1 | 19 |
| 15 | 2 | 1 | 0 | 1 | 39 |
| 13 | 1 | 1 | 0 | 1 | 68 |
| 3 | 2 | 1 | 0 | 1 | 33 |
| 12 | 1 | 1 | 0 | 1 | 27 |

## Decision Notes

| note_key | value | interpretation |
| --- | --- | --- |
| final_decision | 특정 substation/window에 FP가 몰려 추가 검토 필요 | hard normal이 일부 substation에 2건 이상 몰려 있어 설비별 정상 패턴 차이를 확인해야 한다. |
| normal_label_policy | keep | 회사 제공 normal 라벨은 삭제하거나 재라벨링하지 않는다. |
| normal_rows | 35 | normal 35건이 audit에 모두 포함됐다. |
| hard_normal_count | 8 | main compact13 계열에서 하나 이상 FP가 난 normal 수다. |
| high_severity_count | 0 | locked와 fold-selected compact13 둘 다 FP인 normal 수다. |
| medium_severity_count | 8 | 둘 중 하나만 FP인 normal 수다. |
| expanded154_fp_count | 7 | expanded154에서도 FP였던 normal 수다. |
| locked_compact13_fp_count | 2 | locked compact13 FP normal 수다. |
| fold_selected_compact13_fp_count | 6 | fold-selected compact13 FP normal 수다. |
| max_substation_hard_count | 2 | 한 substation 안에서 발견된 hard normal 최대 건수다. |
| concentrated_substations | 11 | hard normal이 2건 이상 나온 substation 목록이다. |
| hard_to_positive_z_distance | 0.788847130817187 | compact13 z-score 평균 기준 hard normal과 positive의 거리다. |
| hard_to_true_negative_z_distance | 0.32965848710408757 | compact13 z-score 평균 기준 hard normal과 true negative normal의 거리다. |

## 생성 이미지

- `07_데이터산출물/m1_hard_normal_probability_ranking.png`
- `07_데이터산출물/m1_hard_normal_feature_profile.png`
- `07_데이터산출물/m1_hard_normal_substation_distribution.png`

## 검증 결과

- normal 35건이 audit에 모두 포함됐다.
- normal disturbance count는 0으로 재확인했다.
- Event 20/34/69는 학습/판단 dataset에 없다.
- threshold 0.6 기준 FP/TN 구분은 10번 prediction과 일치한다.
- `hard_normal_flag`와 severity는 정의된 규칙으로 생성됐다.

## 한계와 주의점

- 샘플 수가 작아서 hard normal은 제거 대상이 아니라 해석/audit 태그로만 사용해야 한다.
- 이번 분석은 normal 라벨 품질을 부정하는 것이 아니라 모델이 헷갈리는 정상 패턴을 분리한 것이다.
- 모델 파일 저장이나 운영 배포는 하지 않았다.

## 다음에 볼 것

- hard normal 이벤트의 센서 시계열을 직접 확인한다.
- 특정 substation에 hard normal이 반복되면 설비별 정상 패턴 보정이 필요한지 확인한다.
- 이후 학습에서는 normal 라벨은 유지하되 hard normal 태그를 평가/해석용 metadata로 둔다.
