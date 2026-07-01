# MVP 모델 사용 안내

이 문서는 `outputs/share_mvp/`에 포함된 모델 파일과 결과 샘플을 팀원이 이해하고 재사용할 수 있도록 정리한 안내서입니다.

## 1. 최종 운영 MVP 모델

최종 운영 MVP 모델은 **LightGBM**입니다.

10단계 Model Evaluation 결과, LightGBM은 RandomForest보다 False Positive를 줄이면서도 Isolation Forest보다 높은 위험 탐지 성능을 보였습니다. 따라서 MVP 운영 모델로는 LightGBM을 우선 사용합니다.

## 2. 포함된 모델 파일 역할

| 파일 | 역할 |
|---|---|
| `models/09_lightgbm_model.joblib` | 최종 운영 MVP 위험 예측 모델입니다. `risk_probability`를 생성하고 threshold 기준으로 위험 여부를 판단합니다. |
| `models/08_isolation_forest.joblib` | 정상 패턴 기반 보조 이상탐지 모델입니다. LightGBM 결과를 보조하는 `anomaly_score`, `is_anomaly` 신호로 사용합니다. |
| `models/07_random_forest_baseline.joblib` | Baseline 비교 모델입니다. 최종 운영 모델은 아니지만 성능 비교 기준으로 사용합니다. |

## 3. 모델 입력 데이터 형식

모델 입력은 원본 시계열 데이터가 아닙니다.

실제 추론 시에는 반드시 다음 순서를 거쳐야 합니다.

```text
원본 운영 데이터
  ↓
전처리
  ↓
timestamp 정렬
  ↓
window 생성
  ↓
window 단위 feature 생성
  ↓
학습 당시와 동일한 354개 feature 컬럼 구성
  ↓
모델 입력
```

즉, joblib 파일만으로는 바로 예측할 수 없습니다. 학습 당시와 동일한 feature 생성 파이프라인이 필요합니다.

## 4. Feature 컬럼 주의사항

LightGBM, RandomForest, Isolation Forest는 모두 학습 당시 저장된 **354개 feature 컬럼**을 기준으로 동작합니다.

주의사항:

- feature 컬럼 이름이 학습 당시와 동일해야 합니다.
- feature 컬럼 순서가 학습 당시와 동일해야 합니다.
- 누락된 feature가 있으면 예측 결과를 신뢰할 수 없습니다.
- 추가 feature가 있어도 모델 입력에는 학습 당시 feature만 사용해야 합니다.
- `window_id`, `manufacturer`, `substation_id`, `window_start`, `window_end` 같은 metadata는 모델 feature가 아닙니다.
- `window_label`, `matched_event_id`, `matched_fault_type`, `overlap_count`, `source_label_id` 같은 label metadata는 feature에서 제외해야 합니다.

## 5. Label Metadata 제외 정책

다음 컬럼은 모델 입력 feature로 사용하면 안 됩니다.

```text
window_id
manufacturer
substation_id
window_start
window_end
first_timestamp
last_timestamp
window_label
matched_interval_type
matched_event_id
matched_fault_type
overlap_count
source_label_id
recommended_for_training
exclude_reason
split
target
```

특히 `overlap_count`는 라벨 구간과의 겹침 정보에서 생성된 값이므로 feature로 사용하면 데이터 누수 위험이 있습니다.

## 6. LightGBM 사용 방식

LightGBM 모델은 위험 class 확률을 반환합니다.

```text
risk_probability = model.predict_proba(X)[:, 1]
pred_risk = risk_probability >= selected_threshold
```

현재 MVP에서 권장하는 threshold는 `0.5`입니다.

09단계 결과 CSV에는 threshold별 예측 컬럼이 저장되어 있습니다.

```text
pred_risk_threshold_0_30
pred_risk_threshold_0_40
pred_risk_threshold_0_50
pred_risk_threshold_0_60
```

10단계 리드타임 평가에서는 이 저장 결과를 사용하여 재학습 없이 threshold별 성능을 비교할 수 있습니다.

## 7. Isolation Forest 사용 방식

Isolation Forest는 정상 패턴 기반 보조 이상탐지 모델입니다.

```text
anomaly_score = -decision_function(X)
is_anomaly = model.predict(X) == -1
```

`anomaly_score`는 값이 클수록 정상 패턴에서 더 벗어난 것으로 해석합니다.

Isolation Forest는 최종 운영 모델이 아니라 LightGBM 결과를 보조하는 이상 신호로 사용하는 것을 권장합니다.

## 8. LLM Agent 역할

LLM Agent는 예측 모델이 아닙니다.

LLM Agent는 다음 역할만 수행합니다.

- LightGBM의 `risk_probability` 해석
- Isolation Forest의 `is_anomaly`, `anomaly_score` 보조 해석
- `risk_level` 기반 운영자 메시지 생성
- 주요 feature 후보 요약
- 현장 점검 또는 센서 확인 권고

LLM Agent는 새로운 고장 확률을 생성하거나, ML 모델 결과와 다른 예측을 만들어서는 안 됩니다.

## 9. 포함된 결과 파일

| 파일 | 설명 |
|---|---|
| `reports/10_model_evaluation_summary.md` | 모델 성능 비교, threshold 분석, lead time 평가, 최종 모델 선정 결과입니다. |
| `reports/11_agent_summary.md` | LLM Agent 입력/출력 구조와 sample message 설명입니다. |
| `data/agent_outputs_sample.json` | 운영자용 Agent 결과 JSON 샘플입니다. |
| `README.md` | 프로젝트 전체 소개 문서입니다. |

## 10. 팀원 재사용 시 체크리스트

- 원본 `data/raw`는 이 공유 패키지에 포함되어 있지 않습니다.
- 대용량 중간 산출물 전체도 포함되어 있지 않습니다.
- 모델을 새 데이터에 적용하려면 전처리, window 생성, feature engineering 파이프라인이 필요합니다.
- 학습 당시와 동일한 354개 feature 컬럼을 만들어야 합니다.
- label metadata는 절대 feature에 포함하지 않습니다.
- LightGBM 결과는 Agent가 설명할 수 있지만, Agent가 새 예측을 만드는 것은 아닙니다.

## 11. 권장 사용 흐름

```text
1. README.md로 프로젝트 전체 구조 이해
2. reports/10_model_evaluation_summary.md로 최종 모델 선정 근거 확인
3. reports/11_agent_summary.md로 Agent 구조 확인
4. data/agent_outputs_sample.json으로 운영자 메시지 예시 확인
5. 필요 시 models/*.joblib을 동일 feature pipeline과 함께 로딩하여 추론
```
