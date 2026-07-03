# M1 Specialist HeatGrid Pipeline

M1 설비에 대해 신고/정비 이벤트 전 위험 신호를 조기 탐지하고, 설비별 점검 우선순위를 산정하는 패키지다.

## 전체 흐름

```text
1. raw inventory/schema 확인
2. canonical trainable window를 M1만 필터링
3. 정상 train 분포 기준 anomaly baseline 학습
4. 기존 best risk/leadtime/priority score를 M1만 bridge
5. anomaly score를 priority score와 merge
6. operational agent card 생성
7. M1 specialist gate score 생성
8. current-best priority와 M1 specialist priority를 hybrid priority로 결합
9. validation, ablation, row reconciliation 수행
10. agent 전달용 CSV와 설명 문서 저장
```

## 모델 구성

### Anomaly

- StandardScaler
- IsolationForest
- LedoitWolf covariance 기반 Mahalanobis distance
- train-normal q99 threshold ratio
- criticality counter

### Risk / Leadtime / Priority

기존 best 파이프라인에서 생성된 M1 score를 가져와 사용한다. 이 값은 active downstream body이며, 패키지 내부에서는 M1 범위로 필터링하고 agent contract에 맞게 정리한다.

### M1 Specialist

- fault gate RandomForest
- task gate RandomForest
- activity gate RandomForest
- pre-event LogisticRegression
- fault group weight
- review flag

최종 priority는 다음처럼 계산한다.

```text
priority_score
= 0.65 * current_best_priority_score
+ 0.35 * m1_specialist_priority_score
```

## 주요 실행 명령

```powershell
cd C:\Project3\m1_specialist_package
& C:\Project3\3rd_model\.venv\Scripts\python.exe run_3rd_model_pipeline.py --steps all
```

단계별 실행:

```powershell
& C:\Project3\3rd_model\.venv\Scripts\python.exe run_3rd_model_pipeline.py --steps raw windows anomaly best_scores merge agent_card m1_specialist_gates m1_specialist validation
```

테스트:

```powershell
& C:\Project3\3rd_model\.venv\Scripts\python.exe -m unittest discover -s tests
```

## 핵심 산출물

```text
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
output/reports/final_validation_report.md
output/reports/m1_specialist_report.md
```

## 해석 제한

- 이 패키지는 M1 전용이다.
- leadtime은 우선순위 참고 신호이지 고장 발생 시각 단정값이 아니다.
- priority는 점검 순위를 돕는 값이며 자동 정비 명령이 아니다.
