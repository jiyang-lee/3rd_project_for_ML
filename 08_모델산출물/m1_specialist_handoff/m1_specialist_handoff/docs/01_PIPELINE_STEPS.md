# Pipeline Steps

## 1. Raw Inventory

raw folder의 파일 목록과 schema 요약을 만든다. 이 단계는 데이터 출처 확인용이며 모델 학습을 직접 수행하지 않는다.

```text
data/interim/raw_inventory.csv
data/interim/raw_schema_summary.csv
```

## 2. Window Import

기존 best 파이프라인의 canonical `trainable_windows.csv`를 읽고 M1 row만 남긴다.

```text
data/processed/trainable_windows.csv
data/processed/feature_columns.csv
data/processed/imputation_values.csv
```

## 3. Anomaly Baseline

M1 train-normal window를 정상 기준으로 사용한다.

```text
StandardScaler
IsolationForest
LedoitWolf Mahalanobis
q99 threshold ratio
criticality counter
```

산출물:

```text
output/anomaly_scores.csv
output/anomaly_metrics.csv
models/anomaly/
```

## 4. Best Score Bridge

기존 best의 risk, leadtime, priority score를 M1만 필터링해서 가져온다. agent 계약에 필요한 score와 설명 근거를 같은 key 기준으로 정리한다.

산출물:

```text
output/risk_scores.csv
output/leadtime_scores.csv
output/priority_scores.csv
```

## 5. Merge

priority score와 anomaly score를 key 기준으로 결합한다.

```text
output/merged_model_scores.csv
```

## 6. Agent Card

에이전트가 읽을 operational column을 만든다.

```text
output/agent_priority_card.csv
output/agent_state_card_schema.json
```

## 7. M1 Specialist

M1 specialist gate score를 계산하고 current-best priority와 결합한다.

```text
output/m1_specialist_gate_scores.csv
output/m1_specialist_scores.csv
output/agent/m1_agent_priority_card.csv
```

## 8. Validation

row reconciliation, threshold sweep, ablation, sensitivity, hard-normal audit을 수행한다.

```text
output/reports/final_validation_report.md
output/reports/ablation_summary.csv
output/reports/threshold_sweep.csv
output/reports/priority_weight_sensitivity.csv
```
