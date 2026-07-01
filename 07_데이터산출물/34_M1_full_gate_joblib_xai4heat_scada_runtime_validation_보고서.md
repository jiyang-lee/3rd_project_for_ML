# M1 Full Gate Joblib 및 XAI4HEAT SCADA Runtime 검증 보고서

## 결론
결론은 `joblib_ready_but_scada_schema_blocked`입니다.

- M1 full gate runtime policy는 `joblib` 파일 4개로 저장됐고, 저장 후 reload 예측은 모두 동일했습니다.
- XAI4HEAT SCADA CSV 5개는 내려받았거나 이미 존재합니다.
- XAI4HEAT는 fault/task/activity 라벨 성능 평가용이 아닙니다. 이번에는 외부 SCADA에서 feature 계산과 inference 호출이 가능한지만 확인했습니다.
- 현재 XAI4HEAT feature coverage는 `0.7692`입니다. 실행된 gate row는 `0`개, 누락 feature 때문에 차단된 row는 `20`개입니다.

## 근거
### Joblib 모델 registry
| component | model_type | training_dataset_id | feature_set | feature_count | threshold | training_rows | positive_rows | normal_rows | model_path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fault_gate | RandomForestClassifier_depth3 | fault_no_overlap | compact13 | 13 | 0.5000 | 90 | 55 | 35 | 08_모델산출물\m1_fault_gate_rf_depth3.joblib |
| task_gate | RandomForestClassifier_depth3 | task_post_1d | compact13 | 13 | 0.5000 | 77 | 42 | 35 | 08_모델산출물\m1_task_gate_rf_depth3.joblib |
| activity_gate | RandomForestClassifier_depth3 | activity_pre_1d | compact13 | 13 | 0.5000 | 82 | 47 | 35 | 08_모델산출물\m1_activity_gate_rf_depth3.joblib |
| fault_pre_event_gate | LogisticRegression_balanced | expanded_compact13_full_pool | compact13_overlap | 13 | 0.6000 | 131 | 26 | 105 | 08_모델산출물\m1_fault_pre_event_logistic.joblib |

### 저장 전후 reload 검증
아래 수치는 저장용 full-data 모델을 reload한 뒤 같은 입력에 다시 예측시킨 결과입니다. 33번 OOF 검증 수치는 다음 절에서 별도로 재현했습니다.

| component | training_dataset_id | rows | balanced_accuracy | recall | normal_fpr | reload_max_probability_abs_diff | reload_prediction_identical |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fault_gate | fault_no_overlap | 90 | 0.9532 | 0.9636 | 0.0571 | 0.0000 | True |
| task_gate | task_post_1d | 77 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | True |
| activity_gate | activity_pre_1d | 82 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | True |
| fault_pre_event_gate | strict_no_event20_fixed_eval | 49 | 0.9714 | 1.0000 | 0.0571 | 0.0000 | True |

### 33번 Full Gate OOF metric 재현
| component | rows | balanced_accuracy | precision | recall | f1 | normal_fpr | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recomputed_33_fault_gate | 90 | 0.8455 | 0.8750 | 0.8909 | 0.8829 | 0.2000 | 28 | 7 | 6 | 49 |
| recomputed_33_task_gate | 77 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 35 | 0 | 0 | 42 |
| recomputed_33_activity_gate | 82 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 35 | 0 | 0 | 47 |

### XAI4HEAT 다운로드 manifest
| filename | status | exists | size_bytes | doi |
| --- | --- | --- | --- | --- |
| L4_combined_data.csv | exists | True | 2838776 | 10.17632/2mwc6x6kwb.1 |
| L8_combined_data.csv | exists | True | 1836321 | 10.17632/2mwc6x6kwb.1 |
| L12_combined_data.csv | exists | True | 1835886 | 10.17632/2mwc6x6kwb.1 |
| L17_combined_data.csv | exists | True | 2749896 | 10.17632/2mwc6x6kwb.1 |
| L22_combined_data.csv | exists | True | 1861382 | 10.17632/2mwc6x6kwb.1 |

### SCADA schema mapping 요약
| match_status | count |
| --- | --- |
| missing | 10 |
| semantic_match | 30 |

### Runtime prediction 상태
| runtime_status | count |
| --- | --- |
| blocked_by_missing_features | 20 |

### Distribution shift
| feature | m1_mean | xai4heat_mean | mean_shift_zscore | shift_status |
| --- | --- | --- | --- | --- |
| outdoor_temperature__last_12h_mean_minus_prev_12h_mean | 0.6708 | -0.7583 | -0.5066 | computed |
| outdoor_temperature__last_6h_mean_minus_prev_6h_mean | -0.3448 | 0.4500 | 0.2936 | computed |
| outdoor_temperature__last_minus_first | -0.6916 | -4.8200 | -0.8744 | computed |
| p_hc1_return_temperature__last_12h_mean_minus_prev_12h_mean | -0.0184 | 7.2417 | 1.9250 | computed |
| p_hc1_return_temperature__last_1d_mean_minus_prev_6d_mean | -0.3580 | 4.3095 | 1.0875 | computed |
| p_net_meter_flow__last_1d_std_minus_prev_6d_std | -27.1464 |  |  | blocked_or_missing |
| p_net_return_temperature__last_1d_mean_minus_prev_6d_mean | -0.3201 | 2.7680 | 0.7225 | computed |
| p_return_gap__last_1d_mean_minus_prev_6d_mean | 0.1265 | 1.5415 | 0.5964 | computed |
| p_return_gap__last_minus_first | 0.2260 | -0.2600 | -0.0665 | computed |
| s_hc1_supply_temperature__last_1d_mean_minus_prev_6d_mean | 0.1307 | 5.8048 | 1.0046 | computed |
| s_hc1_supply_temperature__last_1d_std_minus_prev_6d_std | -0.9163 | -0.8394 | 0.0266 | computed |
| s_hc1_supply_temperature_error__last_minus_first | -1.3440 |  |  | blocked_or_missing |

## 한계
- XAI4HEAT는 1시간 해상도이고, M1 PreDist는 10분 해상도입니다. 같은 feature 이름을 만들 수 있어도 분포는 다를 수 있습니다.
- XAI4HEAT에는 이번 runtime 검증에서 사용할 fault/task/activity 정답 라벨이 없으므로 성능 지표를 계산하지 않았습니다.
- 누락 feature가 있는 gate는 실행하지 않고 `blocked_by_missing_features`로 차단했습니다. 억지 매핑은 하지 않았습니다.
- Event 20, 34, 69, 67은 fault metadata audit 대상으로 유지합니다. Event 19, 68, 35, 48은 hard normal metadata로 유지합니다.
- priority score는 ML 모델이 아니라 policy layer입니다.

## 다음 작업 순서
1. XAI4HEAT에서 누락된 M1 compact13 signal을 대체할 수 있는 안전한 semantic mapping 후보를 검토합니다.
2. 외부 라벨이 있는 SCADA 데이터를 확보하면 성능 검증을 별도로 수행합니다.
3. runtime 입력 schema를 확정한 뒤 `joblib` inference wrapper를 만듭니다.
4. 현재 joblib package는 M1 내부 기준 재현용 운영 후보로만 사용합니다.

## 품질 검증
| check | pass | evidence |
| --- | --- | --- |
| M1 internal joblib artifacts created | True | 08_모델산출물\m1_fault_gate_rf_depth3.joblib\|08_모델산출물\m1_task_gate_rf_depth3.joblib\|08_모델산출물\m1_activity_gate_rf_depth3.joblib\|08_모델산출물\m1_fault_pre_event_logistic.joblib |
| 33 full gate metric reproduced | True | threshold 0.5 balanced accuracy matched m1_full_gate_lock_metrics.csv |
| joblib reload prediction identical | True | max diff=4.4408920985e-16 |
| XAI4HEAT raw CSV available | True | 5/5 |
| XAI4HEAT raw CSV ignored by git | True | clean_or_ignored |
| schema mapping audit created | True | 07_데이터산출물\xai4heat_scada_schema_mapping_audit.csv |
| feature coverage audit created | True | 07_데이터산출물\xai4heat_scada_feature_coverage_audit.csv |
| missing-feature gates blocked | True | {'blocked_by_missing_features': 20} |
| external label metrics not computed | True | XAI4HEAT label metrics are intentionally not computed |
| PreDist ZIP/metadata unmodified | True | clean |
| non-target manufacturer strings absent in generated outputs | True | not_found |
| Event 20/34/69/67 metadata retained | True | special event notes are written to report |
| Event 19/68/35/48 hard normal metadata retained | True | hard normal notes are written to report |

## 참조
- XAI4HEAT GitHub: https://github.com/xai4heat/xai4heat
- XAI4HEAT Mendeley: https://data.mendeley.com/datasets/2mwc6x6kwb/1
- DOI: 10.17632/2mwc6x6kwb.1
