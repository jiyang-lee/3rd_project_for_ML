# M1 Joblib 외부 M2 성능 검증 보고서

## 결론
M1에서 학습·잠금한 joblib 모델을 M2에 그대로 적용한 외부 성능 검증 결과입니다.

- 통과 gate 수: `3`개
- 실패 gate 수: `1`개
- M2는 학습에 사용하지 않았고, `joblib.load → feature 계산 → predict_proba`만 수행했습니다.
- 따라서 이 보고서의 수치가 현재 가장 직접적인 외부 성능입니다.

## 외부 성능 요약
| dataset_id | gate | rows | positive_rows | normal_or_negative_rows | balanced_accuracy | precision | recall | f1 | normal_fpr | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m2_activity_pre_1d_external | activity_gate | 57 | 27 | 30 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 30 | 0 | 0 | 27 |
| m2_fault_internal_efd_possible_sensitivity | fault_pre_event_gate | 39 | 25 | 14 | 0.6057 | 0.7273 | 0.6400 | 0.6809 | 0.4286 | 8 | 6 | 9 | 16 |
| m2_fault_no_overlap_external | fault_gate | 75 | 45 | 30 | 0.8667 | 0.9474 | 0.8000 | 0.8675 | 0.0667 | 28 | 2 | 9 | 36 |
| m2_normal_vs_efd_possible_external | fault_pre_event_gate | 55 | 25 | 30 | 0.5200 | 0.4706 | 0.6400 | 0.5424 | 0.6000 | 12 | 18 | 9 | 16 |
| m2_task_post_1d_external | task_gate | 72 | 42 | 30 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 30 | 0 | 0 | 42 |

## 의사결정
| dataset_id | gate | balanced_accuracy | recall | normal_fpr | decision |
| --- | --- | --- | --- | --- | --- |
| m2_activity_pre_1d_external | activity_gate | 1.0000 | 1.0000 | 0.0000 | external_gate_pass |
| m2_fault_internal_efd_possible_sensitivity | fault_pre_event_gate | 0.6057 | 0.6400 | 0.4286 | sensitivity_only_not_training_equivalent |
| m2_fault_no_overlap_external | fault_gate | 0.8667 | 0.8000 | 0.0667 | external_gate_pass |
| m2_normal_vs_efd_possible_external | fault_pre_event_gate | 0.5200 | 0.6400 | 0.6000 | external_gate_fail |
| m2_task_post_1d_external | task_gate | 1.0000 | 1.0000 | 0.0000 | external_gate_pass |

## 데이터셋 구성
| dataset_id | gate | rows_coverage_eligible | positive_rows | negative_or_normal_rows | coverage_median | substation_count | threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| m2_fault_no_overlap_external | fault_gate | 75 | 45 | 30 | 1.0000 | 34 | 0.5000 |
| m2_task_post_1d_external | task_gate | 72 | 42 | 30 | 1.0000 | 34 | 0.5000 |
| m2_activity_pre_1d_external | activity_gate | 57 | 27 | 30 | 1.0000 | 23 | 0.5000 |
| m2_normal_vs_efd_possible_external | fault_pre_event_gate | 55 | 25 | 30 | 1.0000 | 28 | 0.6000 |
| m2_fault_internal_efd_possible_sensitivity | fault_pre_event_gate | 39 | 25 | 14 | 1.0000 | 23 | 0.6000 |

## Class별 지표
| dataset_id | gate | class | precision | recall | f1 | support |
| --- | --- | --- | --- | --- | --- | --- |
| m2_activity_pre_1d_external | activity_gate | negative_or_normal | 1.0000 | 1.0000 | 1.0000 | 30 |
| m2_activity_pre_1d_external | activity_gate | target | 1.0000 | 1.0000 | 1.0000 | 27 |
| m2_fault_internal_efd_possible_sensitivity | fault_pre_event_gate | negative_or_normal | 0.4706 | 0.5714 | 0.5161 | 14 |
| m2_fault_internal_efd_possible_sensitivity | fault_pre_event_gate | target | 0.7273 | 0.6400 | 0.6809 | 25 |
| m2_fault_no_overlap_external | fault_gate | negative_or_normal | 0.7568 | 0.9333 | 0.8358 | 30 |
| m2_fault_no_overlap_external | fault_gate | target | 0.9474 | 0.8000 | 0.8675 | 45 |
| m2_normal_vs_efd_possible_external | fault_pre_event_gate | negative_or_normal | 0.5714 | 0.4000 | 0.4706 | 30 |
| m2_normal_vs_efd_possible_external | fault_pre_event_gate | target | 0.4706 | 0.6400 | 0.5424 | 25 |
| m2_task_post_1d_external | task_gate | negative_or_normal | 1.0000 | 1.0000 | 1.0000 | 30 |
| m2_task_post_1d_external | task_gate | target | 1.0000 | 1.0000 | 1.0000 | 42 |

## Confusion Matrix
| dataset_id | gate | actual | predicted | count |
| --- | --- | --- | --- | --- |
| m2_activity_pre_1d_external | activity_gate | 0 | 0 | 30 |
| m2_activity_pre_1d_external | activity_gate | 0 | 1 | 0 |
| m2_activity_pre_1d_external | activity_gate | 1 | 0 | 0 |
| m2_activity_pre_1d_external | activity_gate | 1 | 1 | 27 |
| m2_fault_internal_efd_possible_sensitivity | fault_pre_event_gate | 0 | 0 | 8 |
| m2_fault_internal_efd_possible_sensitivity | fault_pre_event_gate | 0 | 1 | 6 |
| m2_fault_internal_efd_possible_sensitivity | fault_pre_event_gate | 1 | 0 | 9 |
| m2_fault_internal_efd_possible_sensitivity | fault_pre_event_gate | 1 | 1 | 16 |
| m2_fault_no_overlap_external | fault_gate | 0 | 0 | 28 |
| m2_fault_no_overlap_external | fault_gate | 0 | 1 | 2 |
| m2_fault_no_overlap_external | fault_gate | 1 | 0 | 9 |
| m2_fault_no_overlap_external | fault_gate | 1 | 1 | 36 |
| m2_normal_vs_efd_possible_external | fault_pre_event_gate | 0 | 0 | 12 |
| m2_normal_vs_efd_possible_external | fault_pre_event_gate | 0 | 1 | 18 |
| m2_normal_vs_efd_possible_external | fault_pre_event_gate | 1 | 0 | 9 |
| m2_normal_vs_efd_possible_external | fault_pre_event_gate | 1 | 1 | 16 |
| m2_task_post_1d_external | task_gate | 0 | 0 | 30 |
| m2_task_post_1d_external | task_gate | 0 | 1 | 0 |
| m2_task_post_1d_external | task_gate | 1 | 0 | 0 |
| m2_task_post_1d_external | task_gate | 1 | 1 | 42 |

## 해석
- `fault_gate`, `task_gate`, `activity_gate`는 M1 front gate joblib을 그대로 적용했습니다.
- `fault_pre_event_gate`는 M1 fault 내부 조기탐지 LogisticRegression을 그대로 적용했습니다.
- `m2_normal_vs_efd_possible_external`은 M2 normal과 M2 `efd_possible=True` fault report를 비교한 외부 pre-event 검증입니다.
- `m2_fault_internal_efd_possible_sensitivity`는 fault report 내부에서 `efd_possible=True/False`를 구분할 수 있는지 본 참고 지표입니다. 학습 구조와 완전히 같지 않으므로 최종 pass/fail에는 직접 쓰지 않습니다.

## 한계
- M2는 같은 PreDist 계열의 다른 manufacturer입니다. 완전히 독립적인 기관/운영사 데이터는 아닙니다.
- M2 normal은 30건으로 M1 normal 35건보다 작습니다.
- task/activity는 event window 정의가 성능에 크게 영향을 줄 수 있어, 외부 성능이 낮으면 모델보다 window 정책 문제일 수 있습니다.
- 이번 작업은 재학습이 아니라 외부 inference 검증입니다.

## 다음 작업
1. 통과한 gate는 M1+M2 통합 검증 후보로 올립니다.
2. 실패한 gate는 feature를 바꾸기 전에 window/label 정책을 먼저 재검토합니다.
3. M2에서 안정적인 gate만 runtime wrapper에 포함합니다.
4. 완전히 다른 라벨 포함 SCADA 데이터가 생기면 그때 진짜 외부 기관 검증을 추가합니다.

## 품질 검증
- source commit: `173b4859ff79be30b245a2def36da60173269784`
- M1 joblib 재학습 없음
- M2 metadata/operational data만 외부 테스트로 사용
- PreDist 원본 수정 없음
