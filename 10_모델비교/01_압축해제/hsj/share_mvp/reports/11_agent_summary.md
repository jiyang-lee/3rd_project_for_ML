# 11 LLM Agent Summary

- 생성 시간: 2026-07-01 14:28:26
- 최종 운영 MVP 모델: LightGBM
- Agent 역할: ML 모델 결과 조회·해석·요약·권고
- 실제 OpenAI API 호출 여부: 아니오
- agent output sample 개수: 30
- agent output 파일: `data\processed\agent_outputs_sample.json`

## Risk Level 분포

| risk_level | count |
| --- | --- |
| HIGH | 799 |
| LOW | 443 |
| MEDIUM | 324 |

## Risk Level 정책

- HIGH: `risk_probability >= 0.8` 또는 `pred_risk = 1` 이면서 `is_anomaly = 1`
- MEDIUM: `risk_probability >= 0.5` 또는 `pred_risk = 1`
- LOW: 그 외

## Top Feature 후보

| feature | importance |
| --- | --- |
| p_net_meter_volume__mean | 1407.140015 |
| s_dhw_lower_storage_temperature__min | 638.890991 |
| s_hc1.2_return_temperature_setpoint__mean | 489.403015 |
| s_hc1.2_supply_temperature__min | 409.954010 |
| s_dhw_upper_storage_temperature__max | 264.088989 |
| s_hc1_supply_temperature_setpoint__std | 180.881098 |
| p_net_supply_temperature__delta | 148.192993 |
| p_dhw_return_temperature__max | 141.608002 |
| p_net_meter_energy__mean | 135.197102 |
| s_hc1_supply_temperature_setpoint__mean | 81.338203 |
| s_dhw_upper_storage_temperature__first | 77.117401 |
| p_hc1_return_temperature__std | 68.033501 |
| s_hc1_supply_temperature__mean | 43.989899 |
| p_net_supply_temperature__last | 31.225800 |
| outdoor_temperature__slope | 30.039469 |
| s_dhw_lower_storage_temperature__first | 22.761499 |
| s_hc1.2_supply_temperature__std | 16.033899 |
| s_hc1_supply_temperature_setpoint__first | 13.131900 |
| s_dhw_upper_storage_temperature__std | 11.696400 |
| s_hc1_supply_temperature_setpoint__slope | 0.528731 |

## HIGH 위험 샘플 agent_input 예시

```json
{
  "window_id": "window_00007575",
  "source_label_id": "event:15.0",
  "matched_event_id": 15.0,
  "manufacturer": "manufacturer 2",
  "substation_id": 50,
  "window_start": "2019-11-30T07:10:00",
  "window_end": "2019-11-30T08:10:00",
  "model_name": "LightGBM",
  "risk_probability": 0.5149401903320364,
  "selected_threshold": 0.5,
  "pred_risk": 1,
  "anomaly_score": 0.0706161149693653,
  "is_anomaly": 1,
  "risk_level": "HIGH",
  "top_features": [
    {
      "feature": "p_net_meter_volume__mean",
      "value": 342836666.6666667,
      "importance": 1407.1400146484375
    },
    {
      "feature": "s_dhw_lower_storage_temperature__min",
      "value": 41.1,
      "importance": 638.8909912109375
    },
    {
      "feature": "s_hc1.2_return_temperature_setpoint__mean",
      "value": null,
      "importance": 489.40301513671875
    },
    {
      "feature": "s_hc1.2_supply_temperature__min",
      "value": null,
      "importance": 409.9540100097656
    },
    {
      "feature": "s_dhw_upper_storage_temperature__max",
      "value": 45.4,
      "importance": 264.0889892578125
    }
  ],
  "label_context": "pre_fault"
}
```

## agent_message 예시

설비 50에서 HIGH 수준의 고장 위험 신호가 감지되었습니다. LightGBM 위험 확률은 0.515이며, Isolation Forest 기준 정상 패턴 이탈 여부는 1입니다. 주요 영향 변수 후보는 p_net_meter_volume__mean, s_dhw_lower_storage_temperature__min, s_hc1.2_return_temperature_setpoint__mean, s_hc1.2_supply_temperature__min, s_dhw_upper_storage_temperature__max입니다. 현장 점검, 센서 이상 여부 확인, 열교환/유량/온도 계통 상태 확인을 우선 권장합니다.

## Prompt Template

```text
당신은 지역난방 운영 보조 AIoT Agent입니다.
당신은 고장 여부를 직접 예측하지 않습니다.
아래 ML 모델 결과 JSON을 바탕으로 운영자가 이해할 수 있게 요약하고, 점검 우선순위를 제안하세요.

규칙:
1. risk_probability, pred_risk, is_anomaly를 모델 결과로만 해석합니다.
2. 새로운 고장 확률을 생성하지 않습니다.
3. 주요 feature는 원인 확정이 아니라 점검 후보로 표현합니다.
4. 운영자가 바로 확인할 수 있는 조치 중심으로 답변합니다.

입력 JSON:
{agent_input_json}
```

## 실제 OpenAI 연동 시 필요한 추가 항목

- 설비별 운영 기준값과 정상 운전 범위
- 최근 24시간 또는 7일 센서 추이 요약
- 운영자 조치 이력과 알람 확인 상태
- 설비 위치, 담당자, 점검 가능 시간 등 운영 metadata
- 안전 문구와 권한 제한 정책

## Risk Level 해석 시 주의사항

- HIGH는 LightGBM의 위험 확률(risk_probability)만으로 결정되지 않습니다.
- LightGBM의 위험 예측(pred_risk)과 Isolation Forest의 이상 탐지 결과(is_anomaly)를 함께 고려하여 운영 우선순위를 결정합니다.
- 따라서 risk_probability가 상대적으로 낮더라도 두 모델이 동시에 위험 신호를 나타내는 경우 HIGH로 분류될 수 있습니다.

## Agent 역할 원칙

- Agent는 새로운 고장 확률을 생성하지 않습니다.
- Agent는 머신러닝 모델(LightGBM, Isolation Forest)의 결과를 조회하고 해석하여 운영자에게 이해하기 쉬운 형태로 설명합니다.
- 최종 점검 여부와 유지보수 의사결정은 운영자가 수행합니다.

## 최종 프로젝트 마무리 권장 사항

- Agent 결과를 SQLite 또는 Parquet 기반 테이블로 저장해 11단계 이후 DB 설계와 연결합니다.
- 운영 화면에서는 HIGH/MEDIUM을 우선 노출하고 LOW는 추세 모니터링으로 분리합니다.
- LLM 응답에는 모델 결과와 운영자 조치를 구분해 표시해야 합니다.
- MVP 발표에서는 “예측 모델”과 “설명 Agent”의 역할을 명확히 분리해 설명합니다.