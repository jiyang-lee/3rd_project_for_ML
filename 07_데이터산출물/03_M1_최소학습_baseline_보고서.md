# M1 최소학습 baseline 보고서

## 개요

M1 전용 전처리 데이터셋 50행으로 `normal`과 `efd_possible`을 구분하는 최소 baseline을 실행했다. 이번 단계의 목적은 운영 모델 확정이 아니라, 현재 feature에 분류 신호가 있는지와 검증 방식이 안전한지 확인하는 것이다.

## 데이터

| 항목 | 값 |
|---|---:|
| 전체 샘플 | 50 |
| normal | 35 |
| efd_possible | 15 |
| 학습 feature | 70 |
| 고유 substation | 29 |

## 학습/평가 방식

- metadata, 날짜, 이벤트 ID, `substation_id`, `coverage_rate`는 모델 입력에서 제외했다.
- 센서 통계 feature 70개만 사용했다.
- 같은 기계실이 train/test에 동시에 들어가지 않도록 `substation_id` 기준 group CV를 사용했다.
- 비교 기준은 `DummyClassifier(strategy="most_frequent")`와 `StandardScaler + LogisticRegression(class_weight="balanced")`다.

## Fold 구성

| fold | test_rows | test_groups | test_normal | test_efd_possible |
| --- | --- | --- | --- | --- |
| 1 | 9 | 5 | 6 | 3 |
| 2 | 9 | 5 | 6 | 3 |
| 3 | 11 | 6 | 8 | 3 |
| 4 | 11 | 7 | 8 | 3 |
| 5 | 10 | 6 | 7 | 3 |

## CV 결과

| model | accuracy_mean | accuracy_std | balanced_accuracy_mean | balanced_accuracy_std | precision_mean | recall_mean | f1_mean | roc_auc_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dummy_most_frequent | 0.6976 | 0.0303 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.5 |
| logistic_balanced | 0.5927 | 0.1042 | 0.5946 | 0.1095 | 0.39 | 0.6 | 0.4714 | 0.6071 |

## Logistic positive 방향 상위 feature

| feature | coefficient |
| --- | --- |
| outdoor_temperature__last_minus_first | 0.6540147800582354 |
| p_net_supply_temperature__max | 0.6535809516485364 |
| p_hc1_return_temperature__mean | 0.6118408248882915 |
| p_hc1_return_temperature__median | 0.5583335429409717 |
| p_net_meter_heat_power__max | 0.5009401673701184 |
| outdoor_temperature__max | 0.4821818714097047 |
| p_hc1_return_temperature__std | 0.3961153926254388 |
| s_hc1_supply_temperature_setpoint__min | 0.36339737050505017 |
| outdoor_temperature__std | 0.33701554553514035 |
| p_net_meter_heat_power__mean | 0.3176169293476882 |

## Logistic negative 방향 상위 feature

| feature | coefficient |
| --- | --- |
| s_hc1_supply_temperature__min | -0.6020843716217549 |
| p_net_meter_flow__max | -0.5618548323777794 |
| p_net_supply_temperature__min | -0.5168210903710109 |
| p_hc1_return_temperature__min | -0.5166621829071449 |
| s_hc1_supply_temperature__last_minus_first | -0.4959042238672981 |
| p_net_meter_flow__min | -0.48962436157469824 |
| p_net_return_temperature__min | -0.45642083582723947 |
| p_net_return_temperature__last_minus_first | -0.4477150107898867 |
| p_hc1_return_temperature__last_minus_first | -0.4237974587226927 |
| s_hc1_supply_temperature_setpoint__median | -0.38081826229340726 |

## Logistic 오분류 샘플

| fold | sample_id | label | predicted_label | substation_id | source_event_id | coverage_rate | positive_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | efd_possible_0003 | efd_possible | normal | 12 | 3 | 1.0000 | 0.0020 |
| 1 | normal_0027 | normal | efd_possible | 12 | 27 | 1.0000 | 0.5547 |
| 1 | normal_0042 | normal | efd_possible | 22 | 42 | 1.0000 | 0.7860 |
| 1 | normal_0054 | normal | efd_possible | 22 | 54 | 1.0000 | 0.9041 |
| 2 | efd_possible_0052 | efd_possible | normal | 21 | 52 | 1.0000 | 0.0009 |
| 2 | efd_possible_0049 | efd_possible | normal | 18 | 49 | 0.9970 | 0.2126 |
| 2 | normal_0017 | normal | efd_possible | 2 | 17 | 1.0000 | 0.6335 |
| 2 | normal_0056 | normal | efd_possible | 2 | 56 | 1.0000 | 0.6008 |
| 2 | normal_0008 | normal | efd_possible | 6 | 8 | 1.0000 | 0.7958 |
| 3 | efd_possible_0044 | efd_possible | normal | 8 | 44 | 1.0000 | 0.2312 |
| 3 | normal_0050 | normal | efd_possible | 17 | 50 | 1.0000 | 0.9565 |
| 3 | normal_0016 | normal | efd_possible | 17 | 16 | 1.0000 | 0.9793 |
| 3 | normal_0021 | normal | efd_possible | 1 | 21 | 1.0000 | 0.6665 |
| 4 | efd_possible_0067 | efd_possible | normal | 7 | 67 | 1.0000 | 0.0176 |
| 4 | normal_0055 | normal | efd_possible | 23 | 55 | 1.0000 | 0.8821 |
| 4 | normal_0043 | normal | efd_possible | 25 | 43 | 1.0000 | 0.5353 |
| 5 | efd_possible_0053 | efd_possible | normal | 13 | 53 | 1.0000 | 0.0734 |
| 5 | normal_0061 | normal | efd_possible | 14 | 61 | 1.0000 | 0.9999 |
| 5 | normal_0014 | normal | efd_possible | 26 | 14 | 1.0000 | 0.8666 |
| 5 | normal_0068 | normal | efd_possible | 13 | 68 | 1.0000 | 0.9977 |

## 해석

- 이 결과는 50행짜리 최소 baseline이므로 성능 일반화 근거로 사용하면 안 된다.
- Dummy는 다수 클래스인 `normal`만 예측해 accuracy는 0.6976이지만, `efd_possible` recall과 f1은 0이다.
- Logistic은 accuracy는 0.5927로 낮지만, balanced accuracy 0.5946, recall 0.6000, f1 0.4714로 positive를 일부 잡는다.
- 따라서 현재 feature에는 약한 분류 신호가 있을 수 있지만, 아직 모델 성능을 주장할 단계는 아니다.
- positive가 15건뿐이라 fold별 recall과 f1 변동이 클 수 있다.
- Event ID 20은 coverage가 0.7242라 품질 주의가 필요하지만, positive 샘플 수가 적어 이번 baseline에서는 유지했다.

## 다음 단계

- fold별 오분류를 보고 feature window 또는 label 기준을 조정할지 판단한다.
- 성능 주장을 하기 전에 샘플 수 확장 또는 label 정책 확장 실험을 분리해서 진행한다.
