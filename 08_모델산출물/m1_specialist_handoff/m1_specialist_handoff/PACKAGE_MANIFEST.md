# Package Manifest

## Active Code

```text
src/third_model/config.py
src/third_model/data_io.py
src/third_model/anomaly.py
src/third_model/best_bridge.py
src/third_model/m1_specialist_gates.py
src/third_model/m1_specialist.py
src/third_model/operational.py
src/third_model/validation.py
src/third_model/pipeline.py
src/third_model/deploy.py
```

## Main Outputs

```text
data/processed/trainable_windows.csv
data/processed/feature_columns.csv
data/processed/imputation_values.csv
output/agent_priority_card.csv
output/agent_state_card_schema.json
output/anomaly_scores.csv
output/risk_scores.csv
output/leadtime_scores.csv
output/priority_scores.csv
output/merged_model_scores.csv
output/m1_specialist_gate_scores.csv
output/m1_specialist_scores.csv
output/agent/m1_agent_priority_card.csv
output/agent/m1_specialist_parallel_agent_card.csv
output/reports/m1_scope_audit.md
output/reports/m1_specialist_report.md
output/reports/m1_specialist_vs_current_best_comparison.csv
```

## Active Models

```text
models/anomaly/standard_scaler.joblib
models/anomaly/isolation_forest.joblib
models/anomaly/mahalanobis_ledoitwolf.joblib
models/m1_specialist/m1_fault_gate_rf_depth3.joblib
models/m1_specialist/m1_task_gate_rf_depth3.joblib
models/m1_specialist/m1_activity_gate_rf_depth3.joblib
models/m1_specialist/m1_fault_pre_event_logistic.joblib
```

## Excluded From Scope

```text
manufacturer 2 rows
M2 threshold calibration
M2 validation claims
global M1/M2 priority replacement claim
```
