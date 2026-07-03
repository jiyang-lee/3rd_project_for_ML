# Final Results

## 최종 사용 산출물

```text
output/agent_priority_card.csv
output/agent/m1_agent_priority_card.csv
output/m1_specialist_gate_scores.csv
output/m1_specialist_scores.csv
output/reports/final_validation_report.md
output/reports/m1_specialist_report.md
output/reports/m1_specialist_vs_current_best_comparison.csv
```

## 최종 priority 의미

최종 `priority_score`는 M1 hybrid priority다.

```text
priority_score
= 0.65 * current_best_priority_score
+ 0.35 * m1_specialist_priority_score
```

해석:

- 기존 best 모델이 만든 risk/leadtime/priority 판단을 기본으로 둔다.
- M1 specialist gate가 fault/task/activity/pre-event 관점에서 보조 근거를 제공한다.
- 둘이 모두 높으면 점검 우선순위를 강하게 올린다.
- 둘이 불일치하면 `review_required`와 `review_reasons`로 사람이 확인할 사유를 남긴다.

## 결과 파일별 의미

`output/anomaly_scores.csv`:

- M1 정상 train 분포 대비 벗어난 정도를 score ratio로 저장한다.
- criticality counter가 포함된다.

`output/risk_scores.csv`:

- 기존 best risk 결과를 M1 범위로 필터링한 파일이다.

`output/leadtime_scores.csv`:

- leadtime bucket과 urgency score를 담는다.
- leadtime은 우선순위 참고 신호다.

`output/priority_scores.csv`:

- 기존 best priority 결과를 M1 범위로 필터링한 파일이다.

`output/agent_priority_card.csv`:

- 최종 에이전트 입력 계약이다.
- priority, anomaly, risk, leadtime, M1 specialist, review/action 설명 컬럼을 포함한다.

## 권장 해석

이 결과는 “어느 설비부터 봐야 하는가”를 정렬하는 용도다. 고장 시각을 단정하거나 자동 정비 지시를 내리는 용도가 아니다.
