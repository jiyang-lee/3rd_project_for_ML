# 공통 평가셋 기준

- source: `09_실험라인/m1_m2_standard_pre_event/outputs/standard_feature_pool.csv`
- evaluation filter: `main_eligible == True`
- target: `y`
- label meaning: `normal=0`, `pre_event=1`
- purpose: handoff 모델을 같은 입력 표와 같은 지표로 평가 가능한지 확인한다.
- conservative rule: 필요한 feature가 정확히 모두 있는 모델만 성능 리더보드에 포함한다.
