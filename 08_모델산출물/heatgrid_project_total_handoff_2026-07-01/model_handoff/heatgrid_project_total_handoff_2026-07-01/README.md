# HeatGrid Project Total Handoff

이 패키지는 현재 프로젝트의 상태카드 runtime 후보를 한 번에 전달하기 위한 총 zip이다.

## 핵심 결론

- 최종 출력은 단일 라벨이 아니라 `primary_state + secondary_tags + pre_event_detected + fault_group + leadtime + priority` 형태의 상태카드다.
- 앞단 gate는 M1 full gate runtime policy의 RandomForest 모델 3개를 포함한다.
- 뒷단 pre_event는 기존 M1-only logistic이 아니라 **M1+M2를 함께 사용한 system-stratified pre_event 후보**를 포함한다.
- pre_event 후보는 급탕/환수 시스템 그룹을 threshold policy에 반영한다.

## 폴더 구조

```text
heatgrid_project_total_handoff_2026-07-01/
├─ front_gates/
│  ├─ m1_fault_gate_rf_depth3.joblib
│  ├─ m1_task_gate_rf_depth3.joblib
│  └─ m1_activity_gate_rf_depth3.joblib
├─ pre_event_gate_m1_m2_system/
│  ├─ m1_m2_system_stratified_pre_event_candidate.joblib
│  └─ m1_m2_system_stratified_pre_event_candidate_metadata.json
├─ runtime_policy/
│  ├─ total_runtime_metadata.json
│  ├─ state_card_output_schema.csv
│  ├─ state_card_rule_table.csv
│  ├─ state_card_external_validation_decision_matrix.csv
│  └─ m1_m2_system_pre_event_decision_matrix.csv
├─ MANIFEST.json
└─ README.md
```

## Runtime 흐름

```text
sensor window
→ fault/task/activity front gates
→ conflict resolver
→ primary_state = fault 인 경우만 M1+M2 system pre_event gate 실행
→ system_capability_group별 threshold 적용
→ state card 출력
```

## 포함 모델

### Front gates

- fault gate: RandomForest depth3, threshold 0.5
- task gate: RandomForest depth3, threshold 0.5
- activity gate: RandomForest depth3, threshold 0.5

### Pre-event gate

- model: `lightgbm_depth3`
- feature set: `common13`
- manufacturer scope: `M1+M2`
- fallback threshold: `0.4`
- system thresholds:

```json
{
  "dhw_return": 0.4,
  "dhw_storage": 0.6,
  "dhw_storage_return": 0.7,
  "dhw_supply": 0.4,
  "heating_common_only": 0.6
}
```

## 주의

이 pre_event 후보는 M1+M2와 시스템 그룹을 반영하지만, metadata status는 `global_not_locked_aux_candidates_available`이다.
즉 전체 운영 확정 모델이라기보다는 system-aware 후보 패키지다.

기존 M1-only `m1_fault_pre_event_logistic.joblib`은 이 total zip의 pre_event 모델로 포함하지 않았다.

## 검증 출처

- front gate: `07_데이터산출물/m1_full_gate_decision_matrix.csv`
- state card: `09_실험라인/state_card_external_validation/outputs/`
- M1+M2 system pre_event: `09_실험라인/m1_m2_system_stratified_pre_event/outputs/`

## 로딩 예시

```python
from pathlib import Path
import json
import joblib

ROOT = Path("heatgrid_project_total_handoff_2026-07-01")
metadata = json.loads((ROOT / "runtime_policy" / "total_runtime_metadata.json").read_text(encoding="utf-8"))
fault_gate = joblib.load(ROOT / "front_gates" / "m1_fault_gate_rf_depth3.joblib")
pre_event = joblib.load(ROOT / "pre_event_gate_m1_m2_system" / "m1_m2_system_stratified_pre_event_candidate.joblib")
```

## 무결성 확인

`MANIFEST.json`에 포함 파일의 byte size와 SHA256 hash를 기록했다.
