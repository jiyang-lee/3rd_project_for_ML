# Front gate 공통 평가셋 기준

- source: `07_데이터산출물/m1_fault_gate_lock_predictions.csv`
- filter: `dataset == fault_no_overlap`, `feature_set == compact13`
- evaluation rows: M1 normal vs fault 90 rows
- target: `y`
- label meaning: `normal=0`, `fault=1`
- purpose: front gate 모델을 같은 입력 row와 같은 metric으로 평가한다.
- conservative rule: 원본 PreDist 7일 window에서 required feature를 재생성할 수 있는 모델만 포함한다.
