# M1 라벨/window 검증 보고서

## 개요

M1 `normal` vs `efd_possible` 최소학습 이후, 라벨 품질과 window 기준을 검증했다. 목표는 모델을 더 복잡하게 만드는 것이 아니라, 현재 라벨/window가 학습 기준으로 타당한지 판단하는 것이다.

## 핵심 결론

현재 50행만으로는 최종 window를 확정하지 않고, Event 20/67 민감도를 반영한 보수 기준과 샘플 확장을 먼저 진행한다. 가장 안정적인 후보는 `report_pre_7d` / `no_low_coverage20`로 관찰됐지만, 이 결론은 탐색 결과로만 둔다.

- normal 35개 이벤트의 7일 구간 안에는 M1 disturbance가 없었다: `True`
- Event ID 20의 `report_pre_7d` coverage는 `0.7242`로 낮다.
- Event ID 67은 anomaly start가 report date보다 `217.5`일 앞선 장기 anomaly다.
- 성능 숫자 하나만으로 window를 고르지 않고, coverage, disturbance overlap, outlier 민감도, group CV 결과를 함께 봐야 한다.

## 라벨/window audit 요약

| label | policy | rows | coverage_min | coverage_median | coverage_max | disturbance_sum |
| --- | --- | --- | --- | --- | --- | --- |
| efd_possible | anomaly_original | 15 | 0.4630 | 1.0003 | 1.0022 | 25 |
| efd_possible | anomaly_start_plus_7d | 15 | 0.7242 | 1.0000 | 1.0000 | 23 |
| efd_possible | anomaly_start_pre_7d | 15 | 0.9950 | 1.0000 | 1.0000 | 3 |
| efd_possible | report_pre_1d | 15 | 0.0972 | 1.0000 | 1.0000 | 2 |
| efd_possible | report_pre_3d | 15 | 0.3565 | 1.0000 | 1.0000 | 4 |
| efd_possible | report_pre_7d | 15 | 0.7242 | 1.0000 | 1.0000 | 5 |
| normal | normal_1d | 35 | 1.0000 | 1.0000 | 1.0000 | 0 |
| normal | normal_3d | 35 | 1.0000 | 1.0000 | 1.0000 | 0 |
| normal | normal_7d | 35 | 1.0000 | 1.0000 | 1.0000 | 0 |

## 시나리오별 최고 후보

| candidate_id | scenario | positive_rows | coverage_min | positive_disturbance_sum | balanced_accuracy_mean | recall_mean | f1_mean | fp_sum | fn_sum | review_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anomaly_start_plus_7d | all | 15 | 0.7242 | 23 | 0.6381 | 0.6000 | 0.5048 | 11 | 6 | coverage<0.95; post/anomaly window disturbance risk |
| anomaly_start_plus_7d | no_event67 | 14 | 0.7242 | 23 | 0.6732 | 0.6667 | 0.5457 | 11 | 5 | coverage<0.95; post/anomaly window disturbance risk |
| report_pre_7d | no_event67_no_event20 | 13 | 0.9950 | 5 | 0.5988 | 0.3667 | 0.3933 | 6 | 8 | reviewable |
| report_pre_7d | no_low_coverage20 | 14 | 0.9950 | 5 | 0.6048 | 0.5000 | 0.4133 | 10 | 7 | reviewable |

## 검토 가능한 상위 후보

| candidate_id | scenario | positive_rows | coverage_min | positive_disturbance_sum | balanced_accuracy_mean | recall_mean | f1_mean | fp_sum | fn_sum | review_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| report_pre_7d | no_low_coverage20 | 14 | 0.9950 | 5 | 0.6048 | 0.5000 | 0.4133 | 10 | 7 | reviewable |
| report_pre_7d | no_event67_no_event20 | 13 | 0.9950 | 5 | 0.5988 | 0.3667 | 0.3933 | 6 | 8 | reviewable |
| report_pre_1d | no_low_coverage20 | 14 | 0.9792 | 2 | 0.5774 | 0.4333 | 0.4086 | 10 | 8 | reviewable |
| report_pre_1d | no_event67_no_event20 | 13 | 0.9792 | 2 | 0.5518 | 0.3333 | 0.3133 | 8 | 9 | reviewable |
| report_pre_3d | no_event67_no_event20 | 13 | 0.9931 | 4 | 0.5161 | 0.2333 | 0.2467 | 7 | 10 | reviewable |
| anomaly_start_plus_7d | no_event67_no_event20 | 13 | 0.9970 | 21 | 0.5042 | 0.3333 | 0.2810 | 11 | 9 | post/anomaly window disturbance risk |
| anomaly_start_plus_7d | no_low_coverage20 | 14 | 0.9970 | 21 | 0.5024 | 0.3667 | 0.3159 | 12 | 9 | post/anomaly window disturbance risk |

## 기존 report_pre_7d 민감도

| candidate_id | scenario | positive_rows | coverage_min | positive_disturbance_sum | balanced_accuracy_mean | recall_mean | f1_mean | fp_sum | fn_sum | review_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| report_pre_7d | all | 15 | 0.7242 | 5 | 0.5946 | 0.6000 | 0.4714 | 14 | 6 | coverage<0.95; high false positives |
| report_pre_7d | no_event67 | 14 | 0.7242 | 5 | 0.6673 | 0.6667 | 0.5310 | 12 | 5 | coverage<0.95 |
| report_pre_7d | no_event67_no_event20 | 13 | 0.9950 | 5 | 0.5988 | 0.3667 | 0.3933 | 6 | 8 | reviewable |
| report_pre_7d | no_low_coverage20 | 14 | 0.9950 | 5 | 0.6048 | 0.5000 | 0.4133 | 10 | 7 | reviewable |

## 판단

- `report_pre_7d`는 기존 기준과 맞지만 Event 20 low coverage 영향을 받는다.
- `anomaly_start_plus_7d`와 `anomaly_original` 계열은 disturbance overlap과 사후 정보 혼입 위험이 있어 모델 성능 비교 기준으로 신중해야 한다.
- Event 67은 이상 시작이 너무 오래 이어진 케이스라 일반적인 조기탐지 window 판단을 왜곡할 수 있다.
- 따라서 다음 학습 기준은 한 번에 확정하지 말고, `no_event67_no_event20` 같은 보수 버전을 함께 유지해 비교하는 것이 안전하다.

## 생성 파일

- `07_데이터산출물/m1_label_window_audit.csv`
- `07_데이터산출물/m1_window_candidate_summary.csv`
- `07_데이터산출물/m1_window_candidate_cv_metrics.csv`
- `07_데이터산출물/m1_window_candidate_cv_predictions.csv`
- `07_데이터산출물/m1_window_decision_matrix.csv`

## 한계와 주의점

- 전체 샘플이 50행 수준이라 window 결정의 통계적 안정성이 낮다.
- group CV는 누수를 줄이지만 fold별 positive 수가 적다.
- 이 결과는 다음 학습 기준을 좁히기 위한 진단 결과이며, 운영 모델 성능 근거가 아니다.
