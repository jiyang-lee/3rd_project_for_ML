# Validation And Ablation

## 검증 목적

이 패키지의 검증은 모델 성능만 보는 것이 아니라 전달 계약이 실제로 재현 가능한지 확인하는 데 목적이 있다.

## 수행 검증

```text
row reconciliation
threshold sweep
active policy ablation
priority weight sensitivity
hard normal audit
pipeline run metadata
```

## Row Reconciliation

window key가 단계별로 누락되지 않는지 확인한다.

```text
canonical_windows -> priority_scores
canonical_windows -> agent_card
priority_scores -> merged_scores
priority_scores -> agent_card
agent_card -> canonical_windows
```

## Threshold Sweep

다음 score에 대해 threshold별 precision, recall, false positive rate를 계산한다.

```text
anomaly_ensemble_score
risk_score
priority_score
```

## Active Policy Ablation

다음 운영 신호 조합을 비교한다.

```text
official_anomaly_evidence_event
risk_high_or_critical
m1_specialist_high_or_urgent
priority_high_or_urgent
anomaly_or_risk_high
```

## Priority Sensitivity

priority score의 risk/leadtime/context 가중치를 바꿨을 때 top10 설비가 얼마나 안정적인지 확인한다.

## Hard Normal Audit

label은 normal인데 risk 또는 anomaly가 높게 나온 case를 따로 뽑아 pseudo-clean false alarm 검토 대상으로 본다.
