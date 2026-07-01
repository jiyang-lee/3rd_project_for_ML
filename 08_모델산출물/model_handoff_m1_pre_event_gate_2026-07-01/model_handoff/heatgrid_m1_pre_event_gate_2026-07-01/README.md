# HeatGrid M1 Pre-Event Gate Joblib Handoff

이 패키지는 M1 full gate runtime policy 중 **fault 내부 pre_event gate** 모델만 분리한 전달 패키지다.

## 폴더 구조

```text
heatgrid_m1_pre_event_gate_2026-07-01/
├─ pre_event_gate/
│  ├─ m1_fault_pre_event_logistic.joblib
│  └─ m1_fault_pre_event_metadata.json
├─ MANIFEST.json
└─ README.md
```

## 포함 모델

- component: `fault_pre_event_gate`
- role: `fault_internal_pre_event_gate`
- model: `LogisticRegression(class_weight="balanced")`
- feature set: `compact13_overlap`
- threshold: `0.6`
- training dataset: `expanded_compact13_full_pool`

## 실행 위치

이 모델은 앞단 gate가 `fault`로 판단된 경우에만 실행한다.

```text
sensor window
→ fault/task/activity front gate
→ primary_state = fault
→ pre_event_gate 실행
→ risk_probability >= 0.6 이면 pre_event_detected = true
```

`normal`, `task`, `activity` 상태에서는 이 모델을 실행하지 않는다.

## 로딩 예시

```python
from pathlib import Path
import json
import joblib

ROOT = Path("heatgrid_m1_pre_event_gate_2026-07-01")
model = joblib.load(ROOT / "pre_event_gate" / "m1_fault_pre_event_logistic.joblib")
metadata = json.loads((ROOT / "pre_event_gate" / "m1_fault_pre_event_metadata.json").read_text(encoding="utf-8"))
features = metadata["input_features"]
threshold = metadata["selected_model"]["threshold"]

# X는 features 순서와 이름이 맞는 1행 이상 DataFrame
risk_probability = model.predict_proba(X[features])[:, 1]
pre_event_detected = risk_probability >= threshold
```

## 검증 요약

- 운영 잠금 지표 source: `07_데이터산출물/m1_full_gate_decision_matrix.csv`
  - balanced accuracy: `0.8500`
  - recall: `0.7857`
  - normal FPR: `0.0857`
- joblib reload 검증 source: `07_데이터산출물/m1_joblib_reload_validation.csv`
  - rows: `49`
  - correct: `47/49`
  - reload prediction identical: `True`

## 제외 항목

아래는 이 zip에 포함하지 않았다.

- `fault_gate`
- `task_gate`
- `activity_gate`
- `leadtime_policy`
- `priority_policy`
- bulk score CSV outputs

## 무결성 확인

`MANIFEST.json`에 포함 파일의 byte size와 SHA256 hash를 기록했다.
