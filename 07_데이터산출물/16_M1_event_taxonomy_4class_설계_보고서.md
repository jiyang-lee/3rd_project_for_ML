# M1 4분류 Label Taxonomy 설계 보고서

## 개요

이번 단계는 모델 성능 개선이 아니라, M1 기준 `normal / fault / task / activity` 4분류 학습이 가능한 label/window 구조를 확정하는 작업이다.

최종 결론: **M1_4class_possible**

## 핵심 정리

- `efd_possible`은 최상위 class label이 아니라 fault 내부 metadata로만 사용한다.
- `faults.csv`에 없는 fault disturbance는 `efd_possible=False`가 아니라 `efd_possible_unknown`으로 기록했다.
- M1 `disturbances.csv`에는 task label이 실제로 존재한다.
- normal 35건은 회사 제공 label을 그대로 유지했다.
- Event 20/34/69/67은 삭제하지 않고 fault metadata flag로 audit에 남겼다.

## Class 후보와 Window 요약

| class | source_rows | baseline_included | substations | overlap_rows |
| --- | --- | --- | --- | --- |
| normal | 35 | 35 | 22 | 0 |
| fault | 67 | 62 | 28 | 9 |
| task | 43 | 37 | 23 | 29 |
| activity | 55 | 47 | 20 | 5 |

## Fault 내부 Metadata

| item | count |
| --- | --- |
| fault disturbance | 67 |
| faults.csv matched | 33 |
| fault detail missing | 34 |
| fault label known | 31 |
| fault label unknown | 2 |
| efd_possible True | 29 |
| efd_possible False | 4 |

## Window Policy Audit

| final_class | window_policy | rows | coverage_eligible | overlap_rows | median_coverage |
| --- | --- | --- | --- | --- | --- |
| activity | activity_post_7d | 55 | 46 | 7 | 1.0000 |
| activity | activity_pre_7d | 55 | 47 | 5 | 1.0000 |
| fault | fault_pre_7d | 67 | 62 | 9 | 1.0000 |
| normal | normal_event_7d | 35 | 35 | 0 | 1.0000 |
| task | task_post_7d | 43 | 41 | 4 | 1.0000 |
| task | task_pre_7d | 43 | 37 | 29 | 1.0000 |

## 최소 Baseline Sanity Check

| feature_set | model | balanced_accuracy | macro_f1 | accuracy |
| --- | --- | --- | --- | --- |
| compact13 | dummy_most_frequent | 0.2500 | 0.1276 | 0.3436 |
| compact13 | logistic_balanced | 0.4466 | 0.4356 | 0.4631 |
| expanded154 | dummy_most_frequent | 0.2500 | 0.1276 | 0.3436 |
| expanded154 | logistic_balanced | 0.4992 | 0.4711 | 0.5073 |

## 산출물

| 항목 | 파일 |
| --- | --- |
| taxonomy audit | `m1_event_taxonomy_audit.csv` |
| label candidate index | `m1_4class_label_candidate_index.csv` |
| window policy audit | `m1_4class_window_policy_audit.csv` |
| feasibility summary | `m1_4class_dataset_feasibility_summary.csv` |
| baseline metrics | `m1_4class_baseline_metrics.csv` |
| baseline predictions | `m1_4class_baseline_predictions.csv` |

## 검증

- normal 35건을 유지했다.
- disturbance 165건을 audit했다.
- fault/task/activity source count를 원본과 대조했다.
- fault 67건 중 faults.csv 매칭 33건, 미매칭 34건을 확인했다.
- 미매칭 fault는 `efd_possible_unknown`으로 기록했다.
- task/activity에는 `efd_possible` label을 부여하지 않았다.
- Event 20/34/69/67이 audit에 남아 있다.
- Event 19/68/35/48 hard normal metadata를 유지했다.
- group CV에서 train/test `substation_id` overlap은 0이다.

## 한계와 다음 단계

- baseline은 label/window 설계 sanity check이며 최종 모델 선택이 아니다.
- selected window에 다른 disturbance가 겹치는 row가 있으므로, 다음 단계에서는 overlap 제거 버전과 유지 버전을 비교해야 한다.
- compact13이 충분하지 않으면 expanded154 또는 class별 feature 확장을 검토한다.
