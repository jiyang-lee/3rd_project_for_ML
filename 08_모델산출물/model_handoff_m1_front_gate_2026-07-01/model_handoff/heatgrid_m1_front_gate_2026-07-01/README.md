# HeatGrid M1 Front Gate Joblib Handoff

이 패키지는 M1 full gate runtime policy 중 앞단 fault gate 모델만 분리한 전달 패키지다.

## 폴더 구조

```text
heatgrid_m1_front_gate_2026-07-01/
├─ front_gate/
│  ├─ m1_fault_gate_rf_depth3.joblib
│  └─ m1_fault_gate_metadata.json
├─ MANIFEST.json
└─ README.md
```

## 포함 모델

- component: `fault_gate`
- role: `front_gate`
- model: `RandomForestClassifier_depth3`
- feature set: `compact13`
- threshold: `0.5`
- training dataset: `fault_no_overlap`

## 제외 모델

요청 범위에 맞춰 아래 모델은 포함하지 않았다.

- `task_gate`
- `activity_gate`
- `fault_pre_event_gate`
- `priority_policy`

## 로딩 예시

```python
from pathlib import Path
import json
import joblib

ROOT = Path("heatgrid_m1_front_gate_2026-07-01")
model = joblib.load(ROOT / "front_gate" / "m1_fault_gate_rf_depth3.joblib")
metadata = json.loads((ROOT / "front_gate" / "m1_fault_gate_metadata.json").read_text(encoding="utf-8"))
features = metadata["input_features"]
threshold = metadata["selected_model"]["threshold"]
```

## 무결성 확인

`MANIFEST.json`에 포함 파일의 byte size와 SHA256 hash를 기록했다.
