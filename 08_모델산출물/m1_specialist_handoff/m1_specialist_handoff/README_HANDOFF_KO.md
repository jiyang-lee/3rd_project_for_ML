# M1 Specialist Handoff

이 폴더는 현재 M1 모델을 다른 사람에게 전달하기 위한 경량 handoff 묶음이다. 실행용 전체 프로젝트가 아니라, 모델 파일, 데이터/agent 계약, score 산출물, 현재 모델 설명 문서만 포함한다.

## 먼저 볼 파일

```text
README.md
MODEL_INVENTORY_KO.md
AGENT_HANDOFF_KO.md
docs/02_AGENT_OUTPUT_CONTRACT.md
docs/03_MODEL_DESIGN.md
docs/06_FINAL_RESULTS.md
```

## 모델 파일

```text
models/anomaly/standard_scaler.joblib
models/anomaly/isolation_forest.joblib
models/anomaly/mahalanobis_ledoitwolf.joblib
models/m1_specialist/m1_fault_gate_rf_depth3.joblib
models/m1_specialist/m1_task_gate_rf_depth3.joblib
models/m1_specialist/m1_activity_gate_rf_depth3.joblib
models/m1_specialist/m1_fault_pre_event_logistic.joblib
```

## Agent 전달 계약

```text
agent_contract/agent_priority_card.csv
agent_contract/m1_agent_priority_card.csv
agent_contract/agent_state_card_schema.json
agent_contract/agent_card_column_dictionary_ko.csv
agent_contract/agent_card_value_mapping_ko.md
```

`agent_card_column_dictionary_ko.csv`와 `agent_card_value_mapping_ko.md`가 agent로 넘기는 컬럼의 한글 설명 문서다.

## 데이터 계약

```text
data_contract/trainable_windows.csv
data_contract/feature_columns.csv
data_contract/imputation_values.csv
data_contract/window_import_metadata.json
```

## 점수와 검증 결과

```text
scores/
reports/
```

`scores`에는 anomaly, risk, leadtime, priority, M1 specialist score가 들어 있다. `reports`에는 전달 판단에 필요한 최소 검증 요약만 남겼다.

```text
reports/final_validation_report.md
reports/m1_specialist_report.md
reports/m1_specialist_vs_current_best_comparison.csv
reports/row_reconciliation.csv
```

프로젝트 흐름은 `docs/01_PIPELINE_STEPS.md`와 `docs/03_MODEL_DESIGN.md`에서 확인하면 된다.
