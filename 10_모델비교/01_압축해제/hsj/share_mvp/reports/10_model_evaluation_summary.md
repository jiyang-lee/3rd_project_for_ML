# 10 Model Evaluation Summary

- 생성 시간: 2026-07-01 14:11:32
- 사용 split: Event-aware split
- 신규 모델 학습 여부: 아니오
- 최종 권장 모델: LightGBM

## 최종 모델 비교표

| Model | Precision | Recall | F1 | pre_fault Recall | False Positive | PR-AUC | ROC-AUC | Avg Lead Time | Median Lead Time | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RandomForest Baseline | 0.875974 | 0.971698 | 0.921357 | 0.988290 | 175 | 0.953559 | 0.832611 | 1416.666667 | 1440.000000 | pre_fault Recall은 가장 높지만 False Positive가 많아 오탐 부담이 큽니다. |
| Isolation Forest | 0.928652 | 0.644654 | 0.761021 | 0.803279 | 63 | 0.933842 | 0.729279 | 1440.000000 | 1440.000000 | False Positive는 가장 낮지만 위험 Recall과 pre_fault Recall이 낮아 단독 운영 모델로는 보수적입니다. |
| LightGBM | 0.916296 | 0.808962 | 0.859290 | 0.875878 | 94 | 0.940239 | 0.802193 | 1440.000000 | 1440.000000 | False Positive를 줄이면서 pre_fault Recall을 일정 수준 유지해 MVP 운영 모델 후보로 권장합니다. |

## 모델별 성능 비교(Test)

| Model | Precision | Recall | F1 | pre_fault Recall | False Positive | PR-AUC | ROC-AUC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RandomForest Baseline | 0.875974 | 0.971698 | 0.921357 | 0.988290 | 175 | 0.953559 | 0.832611 |
| Isolation Forest | 0.928652 | 0.644654 | 0.761021 | 0.803279 | 63 | 0.933842 | 0.729279 |
| LightGBM | 0.916296 | 0.808962 | 0.859290 | 0.875878 | 94 | 0.940239 | 0.802193 |

## LightGBM Threshold별 성능 비교

| split | threshold | Precision | Recall | F1 | pre_fault Recall | False Positive | PR-AUC | ROC-AUC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | 0.300000 | 0.821494 | 1.000000 | 0.902000 | 1.000000 | 294 | 0.948425 | 0.819739 |
| validation | 0.400000 | 0.821494 | 1.000000 | 0.902000 | 1.000000 | 294 | 0.948425 | 0.819739 |
| validation | 0.500000 | 0.902318 | 0.805617 | 0.851230 | 0.862129 | 118 | 0.948425 | 0.819739 |
| validation | 0.600000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | 0.948425 | 0.819739 |
| test | 0.300000 | 0.812261 | 1.000000 | 0.896406 | 1.000000 | 294 | 0.940239 | 0.802193 |
| test | 0.400000 | 0.812261 | 1.000000 | 0.896406 | 1.000000 | 294 | 0.940239 | 0.802193 |
| test | 0.500000 | 0.916296 | 0.808962 | 0.859290 | 0.875878 | 94 | 0.940239 | 0.802193 |
| test | 0.600000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | 0.940239 | 0.802193 |

## Lead Time 요약

| Model | Event Count | Detected Event Count | Missed Event Count | Detection Rate | Avg Lead Time | Median Lead Time | Min Lead Time | Max Lead Time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Isolation Forest | 11 | 7 | 4 | 0.636364 | 1440.000000 | 1440.000000 | 1440.000000 | 1440.000000 |
| LightGBM | 11 | 8 | 3 | 0.727273 | 1440.000000 | 1440.000000 | 1440.000000 | 1440.000000 |
| RandomForest Baseline | 11 | 9 | 2 | 0.818182 | 1416.666667 | 1440.000000 | 1230.000000 | 1440.000000 |

## Lead Time 상세 상위 50행

| Model | source_label_id | fault_time | first_detection_time | lead_time_minutes | detected_before_fault | pre_fault_window_count | detected_pre_fault_window_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RandomForest Baseline | event:0.0 | 2020-03-23 14:20:00 | 2020-03-22 14:20:00 | 1440.000000 | True | 42 | 42 |
| RandomForest Baseline | event:10.0 | 2020-01-21 10:00:00 | 2020-01-20 10:00:00 | 1440.000000 | True | 42 | 42 |
| RandomForest Baseline | event:14.0 | 2019-12-06 12:00:00 | 2019-12-05 12:00:00 | 1440.000000 | True | 42 | 42 |
| RandomForest Baseline | event:15.0 | 2019-12-01 07:10:00 | 2019-11-30 07:10:00 | 1440.000000 | True | 42 | 42 |
| RandomForest Baseline | event:45.0 | 2020-01-13 14:50:00 | 2020-01-12 14:50:00 | 1440.000000 | True | 42 | 42 |
| RandomForest Baseline | event:47.0 | 2020-01-08 22:10:00 |  |  | False | 0 | 0 |
| RandomForest Baseline | event:53.0 | 2020-05-25 02:10:00 |  |  | False | 0 | 0 |
| RandomForest Baseline | event:57.0 | 2020-02-24 16:50:00 | 2020-02-23 20:20:00 | 1230.000000 | True | 42 | 37 |
| RandomForest Baseline | event:69.0 | 2020-03-10 14:50:00 | 2020-03-09 14:50:00 | 1440.000000 | True | 42 | 42 |
| RandomForest Baseline | event:7.0 | 2020-02-04 07:40:00 | 2020-02-03 07:40:00 | 1440.000000 | True | 57 | 57 |
| RandomForest Baseline | event:8.0 | 2020-01-24 13:50:00 | 2020-01-23 13:50:00 | 1440.000000 | True | 42 | 42 |
| Isolation Forest | event:0.0 | 2020-03-23 14:20:00 | 2020-03-22 14:20:00 | 1440.000000 | True | 42 | 42 |
| Isolation Forest | event:10.0 | 2020-01-21 10:00:00 | 2020-01-20 10:00:00 | 1440.000000 | True | 42 | 42 |
| Isolation Forest | event:14.0 | 2019-12-06 12:00:00 | 2019-12-05 12:00:00 | 1440.000000 | True | 42 | 42 |
| Isolation Forest | event:15.0 | 2019-12-01 07:10:00 | 2019-11-30 07:10:00 | 1440.000000 | True | 42 | 42 |
| Isolation Forest | event:45.0 | 2020-01-13 14:50:00 |  |  | False | 42 | 0 |
| Isolation Forest | event:47.0 | 2020-01-08 22:10:00 |  |  | False | 0 | 0 |
| Isolation Forest | event:53.0 | 2020-05-25 02:10:00 |  |  | False | 0 | 0 |
| Isolation Forest | event:57.0 | 2020-02-24 16:50:00 |  |  | False | 42 | 0 |
| Isolation Forest | event:69.0 | 2020-03-10 14:50:00 | 2020-03-09 14:50:00 | 1440.000000 | True | 42 | 42 |
| Isolation Forest | event:7.0 | 2020-02-04 07:40:00 | 2020-02-03 07:40:00 | 1440.000000 | True | 57 | 57 |
| Isolation Forest | event:8.0 | 2020-01-24 13:50:00 | 2020-01-23 13:50:00 | 1440.000000 | True | 42 | 42 |
| LightGBM | event:0.0 | 2020-03-23 14:20:00 | 2020-03-22 14:20:00 | 1440.000000 | True | 42 | 42 |
| LightGBM | event:10.0 | 2020-01-21 10:00:00 | 2020-01-20 10:00:00 | 1440.000000 | True | 42 | 42 |
| LightGBM | event:14.0 | 2019-12-06 12:00:00 | 2019-12-05 12:00:00 | 1440.000000 | True | 42 | 42 |
| LightGBM | event:15.0 | 2019-12-01 07:10:00 | 2019-11-30 07:10:00 | 1440.000000 | True | 42 | 42 |
| LightGBM | event:45.0 | 2020-01-13 14:50:00 | 2020-01-12 14:50:00 | 1440.000000 | True | 42 | 42 |
| LightGBM | event:47.0 | 2020-01-08 22:10:00 |  |  | False | 0 | 0 |
| LightGBM | event:53.0 | 2020-05-25 02:10:00 |  |  | False | 0 | 0 |
| LightGBM | event:57.0 | 2020-02-24 16:50:00 |  |  | False | 42 | 0 |
| LightGBM | event:69.0 | 2020-03-10 14:50:00 | 2020-03-09 14:50:00 | 1440.000000 | True | 42 | 37 |
| LightGBM | event:7.0 | 2020-02-04 07:40:00 | 2020-02-03 07:40:00 | 1440.000000 | True | 57 | 57 |
| LightGBM | event:8.0 | 2020-01-24 13:50:00 | 2020-01-23 13:50:00 | 1440.000000 | True | 42 | 42 |

## Confusion Matrix 비교

| Model | actual | pred_normal_candidate | pred_risk |
| --- | --- | --- | --- |
| RandomForest Baseline | actual_normal_candidate | 119 | 175 |
| RandomForest Baseline | actual_risk | 36 | 1236 |
| Isolation Forest | actual_normal_candidate | 231 | 63 |
| Isolation Forest | actual_risk | 452 | 820 |
| LightGBM | actual_normal_candidate | 200 | 94 |
| LightGBM | actual_risk | 243 | 1029 |

## Classification Report 비교

| Model | class | precision | recall | f1-score | support |
| --- | --- | --- | --- | --- | --- |
| RandomForest Baseline | normal_candidate | 0.767742 | 0.404762 | 0.530067 | 294.000000 |
| RandomForest Baseline | risk | 0.875974 | 0.971698 | 0.921357 | 1272.000000 |
| RandomForest Baseline | accuracy | 0.865262 | 0.865262 | 0.865262 | 0.865262 |
| RandomForest Baseline | macro avg | 0.821858 | 0.688230 | 0.725712 | 1566.000000 |
| RandomForest Baseline | weighted avg | 0.855655 | 0.865262 | 0.847896 | 1566.000000 |
| Isolation Forest | normal_candidate | 0.338214 | 0.785714 | 0.472876 | 294.000000 |
| Isolation Forest | risk | 0.928652 | 0.644654 | 0.761021 | 1272.000000 |
| Isolation Forest | accuracy | 0.671137 | 0.671137 | 0.671137 | 0.671137 |
| Isolation Forest | macro avg | 0.633433 | 0.715184 | 0.616949 | 1566.000000 |
| Isolation Forest | weighted avg | 0.817804 | 0.671137 | 0.706925 | 1566.000000 |
| LightGBM | normal_candidate | 0.451467 | 0.680272 | 0.542741 | 294.000000 |
| LightGBM | risk | 0.916296 | 0.808962 | 0.859290 | 1272.000000 |
| LightGBM | accuracy | 0.784802 | 0.784802 | 0.784802 | 0.784802 |
| LightGBM | macro avg | 0.683881 | 0.744617 | 0.701016 | 1566.000000 |
| LightGBM | weighted avg | 0.829029 | 0.784802 | 0.799861 | 1566.000000 |

## Feature Importance Top 20 비교

| model | feature | importance |
| --- | --- | --- |
| RandomForest Baseline | p_net_meter_volume__mean | 0.037693 |
| RandomForest Baseline | p_net_meter_volume__first | 0.031179 |
| RandomForest Baseline | p_net_meter_volume__min | 0.031049 |
| RandomForest Baseline | p_net_meter_volume__std | 0.027262 |
| RandomForest Baseline | p_net_meter_volume__max | 0.026516 |
| RandomForest Baseline | p_net_meter_volume__last | 0.025005 |
| RandomForest Baseline | p_net_meter_volume__slope | 0.024374 |
| RandomForest Baseline | p_net_meter_heat_power__max | 0.021661 |
| RandomForest Baseline | p_net_meter_energy__slope | 0.021588 |
| RandomForest Baseline | p_net_meter_energy__first | 0.020303 |
| RandomForest Baseline | s_dhw_lower_storage_temperature__min | 0.020268 |
| RandomForest Baseline | p_net_meter_flow__mean | 0.019842 |
| RandomForest Baseline | p_net_meter_heat_power__mean | 0.019671 |
| RandomForest Baseline | p_net_meter_energy__delta | 0.018900 |
| RandomForest Baseline | p_net_meter_heat_power__first | 0.018641 |
| RandomForest Baseline | p_net_meter_volume__delta | 0.017557 |
| RandomForest Baseline | p_hc1_control_valve_position_setpoint__missing_rate | 0.016330 |
| RandomForest Baseline | p_net_meter_heat_power__last | 0.015979 |
| RandomForest Baseline | p_net_meter_energy__max | 0.015878 |
| RandomForest Baseline | p_net_meter_energy__mean | 0.015201 |
| LightGBM | p_net_meter_volume__mean | 1407.140015 |
| LightGBM | s_dhw_lower_storage_temperature__min | 638.890991 |
| LightGBM | s_hc1.2_return_temperature_setpoint__mean | 489.403015 |
| LightGBM | s_hc1.2_supply_temperature__min | 409.954010 |
| LightGBM | s_dhw_upper_storage_temperature__max | 264.088989 |
| LightGBM | s_hc1_supply_temperature_setpoint__std | 180.881098 |
| LightGBM | p_net_supply_temperature__delta | 148.192993 |
| LightGBM | p_dhw_return_temperature__max | 141.608002 |
| LightGBM | p_net_meter_energy__mean | 135.197102 |
| LightGBM | s_hc1_supply_temperature_setpoint__mean | 81.338203 |
| LightGBM | s_dhw_upper_storage_temperature__first | 77.117401 |
| LightGBM | p_hc1_return_temperature__std | 68.033501 |
| LightGBM | s_hc1_supply_temperature__mean | 43.989899 |
| LightGBM | p_net_supply_temperature__last | 31.225800 |
| LightGBM | outdoor_temperature__slope | 30.039469 |
| LightGBM | s_dhw_lower_storage_temperature__first | 22.761499 |
| LightGBM | s_hc1.2_supply_temperature__std | 16.033899 |
| LightGBM | s_hc1_supply_temperature_setpoint__first | 13.131900 |
| LightGBM | s_dhw_upper_storage_temperature__std | 11.696400 |
| LightGBM | s_hc1_supply_temperature_setpoint__slope | 0.528731 |

## 모델별 장단점

- RandomForest Baseline: pre_fault Recall이 가장 높지만 False Positive가 많아 운영 알람 피로도가 커질 수 있습니다.
- Isolation Forest: 정상 패턴 기반 이상 탐지로 False Positive는 낮지만 위험 Recall이 낮아 고장 전 탐지 보조 지표로 사용하는 편이 안전합니다.
- LightGBM: RandomForest보다 오탐을 줄이면서 Isolation Forest보다 위험 Recall이 높아 MVP 운영 모델로 가장 균형이 좋습니다.

## 11 LLM Agent 입력 데이터 구조 제안

- `event_id`: source_label_id 또는 matched_event_id
- `window_id`, `substation_id`, `manufacturer`, `window_start`, `window_end`
- `model_name`, `risk_probability`, `threshold`, `pred_risk`
- `top_features`: 해당 윈도우의 주요 기여 feature 목록 또는 모델 중요 feature와 실제 feature 값
- `lead_time_minutes`: fault 이벤트가 확인된 경우 최초 탐지 lead time
- `label_context`: normal_candidate/pre_fault/fault/disturbance_marker 등 평가용 라벨 정보
- `agent_message`: 운영자가 이해할 수 있는 위험 요약 문장

## 한계점

- 본 Lead Time 평가는 현재 pre_fault 구간 정의와 label_interval 생성 정책을 기반으로 계산되었습니다.
- 따라서 평균 Lead Time은 데이터셋의 라벨 정의(예: pre_fault 시작 시점)의 영향을 받을 수 있으며, 실제 운영 환경에서는 실제 고장 이력과 운영 로그를 이용한 추가 검증이 필요합니다.
