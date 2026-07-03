# Handoff

이 패키지는 M1 전용 active 파이프라인 전달본이다.

## 전달 기준

- 최종 agent 입력은 `output/agent_priority_card.csv`다.
- 모델 파일은 `models/anomaly/`와 `models/m1_specialist/`만 active로 본다.

## 후속 담당자가 볼 순서

```text
1. README.md
2. MODEL_INVENTORY_KO.md
3. AGENT_HANDOFF_KO.md
4. docs/00_SOURCE_TRACE.md
5. docs/01_PIPELINE_STEPS.md
6. docs/02_AGENT_OUTPUT_CONTRACT.md
7. docs/04_VALIDATION_AND_ABLATION.md
8. output/reports/final_validation_report.md
```

## 추가 검증 과제

- hard-normal review 항목을 현장 이벤트 이력과 대조한다.
- high priority top case를 설비 담당자 기준으로 리뷰한다.
- M2 또는 전체 설비군 확장은 별도 실험으로 분리한다.
