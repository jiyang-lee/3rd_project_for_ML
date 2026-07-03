# Handoff Runbook

## Purpose

이 폴더는 실행용 전체 프로젝트가 아니라 현재 M1 모델 전달 묶음이다. 재실행이나 코드 수정은 `C:\Project3\m1_specialist_package`에서 수행하고, 이 handoff 폴더는 전달/검토용으로 사용한다.

## First Checks

```text
agent_contract/agent_priority_card.csv
agent_contract/agent_card_column_dictionary_ko.csv
agent_contract/agent_card_value_mapping_ko.md
models/anomaly/
models/m1_specialist/
docs/
reports/
```

## Required Model Files

```text
models/anomaly/standard_scaler.joblib
models/anomaly/isolation_forest.joblib
models/anomaly/mahalanobis_ledoitwolf.joblib
models/m1_specialist/m1_fault_gate_rf_depth3.joblib
models/m1_specialist/m1_task_gate_rf_depth3.joblib
models/m1_specialist/m1_activity_gate_rf_depth3.joblib
models/m1_specialist/m1_fault_pre_event_logistic.joblib
```

## If Rebuild Is Needed

```powershell
cd C:\Project3\m1_specialist_package
& C:\Project3\3rd_model\.venv\Scripts\python.exe run_3rd_model_pipeline.py --steps all
```

재생성 후 `m1_specialist_handoff`는 package의 현재 산출물에서 다시 복사해야 한다.
