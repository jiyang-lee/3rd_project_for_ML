# 모델 인벤토리

이 패키지에 남긴 모델은 active 흐름에서 실제로 쓰는 joblib과 metadata만이다.

## 1. 이상탐지 모델

```text
models/anomaly/standard_scaler.joblib
models/anomaly/isolation_forest.joblib
models/anomaly/mahalanobis_ledoitwolf.joblib
models/anomaly/anomaly_metadata.json
```

역할:

- `trainable_windows.csv`의 M1 feature를 표준화한다.
- train split 중 `label == normal`인 구간을 정상 기준으로 잡는다.
- IsolationForest score와 LedoitWolf covariance 기반 Mahalanobis distance를 계산한다.
- train-normal q99 기준으로 score ratio를 만들고, threshold 초과가 지속되면 criticality를 누적한다.

## 2. M1 Specialist Gate 모델

```text
models/m1_specialist/m1_fault_gate_rf_depth3.joblib
models/m1_specialist/m1_task_gate_rf_depth3.joblib
models/m1_specialist/m1_activity_gate_rf_depth3.joblib
models/m1_specialist/m1_fault_pre_event_logistic.joblib
models/m1_specialist/m1_specialist_gate_metadata.json
models/m1_specialist/m1_full_gate_runtime_policy_metadata.json
```

역할:

- raw operational data에서 compact13 성격의 M1 전용 feature를 계산한다.
- fault/task/activity gate 확률과 pre-event 확률을 만든다.
- fault group, group weight, review flag를 생성한다.
- 최종 priority에 35% 비중으로 들어가는 `m1_specialist_priority_score`의 근거가 된다.

## 3. 최종 우선순위 산출

최종 `priority_score`는 별도 joblib 하나가 아니라 다음 두 축을 결합한 운영 로직이다.

```text
priority_score
= 0.65 * current_best_priority_score
+ 0.35 * m1_specialist_priority_score
```

`current_best_priority_score`는 기존 best risk/leadtime/priority 결과를 M1만 필터링해서 가져온 값이다. `m1_specialist_priority_score`는 M1 specialist gate 결과를 우선순위 보조 신호로 변환한 값이다.

## 4. 최종 전달 파일

```text
output/agent_priority_card.csv
output/agent/m1_agent_priority_card.csv
output/agent/agent_card_column_dictionary_ko.csv
output/agent/agent_card_value_mapping_ko.md
```
