# HeatGrid Best Models Only Handoff - No Deep Learning

이 폴더는 `best` 파이프라인에서 비교에 필요한 모델 파일만 최소 구성으로 묶은 handoff 패키지다.

`contracts`, `evaluation`, `source_reference`, bulk score CSV, raw data는 포함하지 않는다. 딥러닝 raw point AutoEncoder 학습 파일도 제외했다.

## Structure

```text
heatgrid_best_models_only_no_dl_2026-07-01/
├─ anomaly/
│  ├─ standard_scaler.joblib
│  ├─ isolation_forest.joblib
│  ├─ mahalanobis_ledoitwolf.joblib
│  ├─ multi_window_raw_1h.joblib
│  ├─ multi_window_raw_3h.joblib
│  ├─ multi_window_raw_12h.joblib
│  ├─ baseline_model_metadata.json
│  ├─ anomaly_ensemble_metadata.json
│  ├─ multi_window_anomaly_metadata.json
│  └─ anomaly_baseline_thresholds.csv
├─ risk/
│  ├─ risk_model_best.joblib
│  └─ risk_model_best_metadata.json
├─ leadtime/
│  ├─ leadtime_model_best.joblib
│  └─ leadtime_model_best_metadata.json
├─ priority/
│  └─ priority_engine_best_metadata.json
└─ MANIFEST.json
```

## Included

```text
IsolationForest anomaly model
LedoitWolf Mahalanobis anomaly model
1h/3h/12h multi-window anomaly models
LightGBM risk model
LightGBM leadtime model
Rule-based priority engine metadata
```

## Excluded

```text
best/models/raw_point_ae/
*.pt
raw point AutoEncoder scaler/covariance/history
contracts/
evaluation/
source_reference/
bulk score CSVs
raw data
```

## Notes

이 패키지는 상대방이 이미 동일하거나 유사한 전처리/feature table을 갖고 있고, 모델 파일 중심으로 비교할 때 쓰는 최소 전달본이다.

입력 feature 목록, threshold, score 구성, priority weight 등은 각 metadata JSON 안에 들어 있다.
