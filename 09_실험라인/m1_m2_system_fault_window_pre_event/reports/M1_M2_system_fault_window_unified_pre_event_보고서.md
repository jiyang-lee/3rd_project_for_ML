# M1+M2 System/Fault/Window 통합 Pre-Event 실험 보고서

## 결론
최종 판단: **window_model_candidates_found**

요청대로 system group, fault group, window 후보, 모델 후보를 한 번에 만들고 비교했다.
전체 공통 모델 하나를 억지로 잠그는 대신, 어떤 조합에서 pre_event 신호가 살아나는지를 표로 잠갔다.
단, `report_pre_1d`는 report 직전 상태 감지에 가까워 조기탐지 후보와 분리해서 해석해야 한다.

## 핵심 요약
- window 후보: `report_pre_7d`, `report_pre_5d`, `report_pre_3d`, `report_pre_1d`
- feature: `common13`
- 모델: Dummy, Logistic, RandomForest, HistGradientBoosting, LightGBM, XGBoost
- 기준: balanced accuracy >= 0.70, recall >= 0.70, normal FPR <= 0.25
- 통과 후보 수: `228`
- `report_pre_1d` 통과 후보 수: `110`
- `report_pre_3d/5d/7d` 통과 후보 수: `118`

## 상위 Decision
| dataset_id | model | threshold | scope | fault_scope | window_policy | balanced_accuracy | recall | normal_fpr | candidate_pass | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_systems__all_faults__report_pre_1d | hist_gradient_boosting | 0.4000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__all_faults__report_pre_1d | hist_gradient_boosting | 0.5000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__all_faults__report_pre_1d | hist_gradient_boosting | 0.6000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__all_faults__report_pre_1d | lightgbm_depth3 | 0.4000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__all_faults__report_pre_1d | lightgbm_depth3 | 0.5000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__all_faults__report_pre_1d | lightgbm_depth3 | 0.6000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__all_faults__report_pre_1d | random_forest_depth3 | 0.4000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__all_faults__report_pre_1d | random_forest_depth3 | 0.5000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__all_faults__report_pre_1d | random_forest_depth3 | 0.6000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__all_faults__report_pre_1d | xgboost_depth3 | 0.4000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__all_faults__report_pre_1d | xgboost_depth3 | 0.5000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__all_faults__report_pre_1d | xgboost_depth3 | 0.6000 | all_systems | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__fault_control_controller__report_pre_1d | random_forest_depth3 | 0.5000 | all_systems | fault_control_controller | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__fault_leakage_water_loss__report_pre_1d | random_forest_depth3 | 0.4000 | all_systems | fault_leakage_water_loss | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__fault_leakage_water_loss__report_pre_1d | random_forest_depth3 | 0.5000 | all_systems | fault_leakage_water_loss | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__fault_pressure_regulator__report_pre_1d | random_forest_depth3 | 0.4000 | all_systems | fault_pressure_regulator | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__fault_pressure_regulator__report_pre_1d | random_forest_depth3 | 0.5000 | all_systems | fault_pressure_regulator | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__fault_pump_failure__report_pre_1d | random_forest_depth3 | 0.4000 | all_systems | fault_pump_failure | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__fault_pump_failure__report_pre_1d | random_forest_depth3 | 0.5000 | all_systems | fault_pump_failure | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| system_dhw_storage__all_faults__report_pre_1d | random_forest_depth3 | 0.5000 | system_dhw_storage | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| system_dhw_storage__all_faults__report_pre_1d | random_forest_depth3 | 0.6000 | system_dhw_storage | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| system_heating_common_only__all_faults__report_pre_1d | random_forest_depth3 | 0.4000 | system_heating_common_only | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| system_heating_common_only__all_faults__report_pre_1d | random_forest_depth3 | 0.5000 | system_heating_common_only | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| system_heating_common_only__all_faults__report_pre_1d | random_forest_depth3 | 0.6000 | system_heating_common_only | all_faults | report_pre_1d | 1.0000 | 1.0000 | 0.0000 | True | window_model_candidate |
| all_systems__fault_control_controller__report_pre_1d | random_forest_depth3 | 0.4000 | all_systems | fault_control_controller | report_pre_1d | 0.9923 | 1.0000 | 0.0154 | True | window_model_candidate |
| all_systems__fault_valve_actuator__report_pre_1d | random_forest_depth3 | 0.4000 | all_systems | fault_valve_actuator | report_pre_1d | 0.9923 | 1.0000 | 0.0154 | True | window_model_candidate |
| system_dhw_storage_return__all_faults__report_pre_1d | random_forest_depth3 | 0.5000 | system_dhw_storage_return | all_faults | report_pre_1d | 0.9583 | 1.0000 | 0.0833 | True | window_model_candidate |
| system_dhw_storage__all_faults__report_pre_1d | random_forest_depth3 | 0.4000 | system_dhw_storage | all_faults | report_pre_1d | 0.9559 | 1.0000 | 0.0882 | True | window_model_candidate |
| system_dhw_storage__all_faults__report_pre_1d | xgboost_depth3 | 0.5000 | system_dhw_storage | all_faults | report_pre_1d | 0.9521 | 0.9630 | 0.0588 | True | window_model_candidate |
| all_systems__fault_control_controller__report_pre_1d | hist_gradient_boosting | 0.4000 | all_systems | fault_control_controller | report_pre_1d | 0.9500 | 0.9000 | 0.0000 | True | window_model_candidate |

## Dataset Summary
| dataset_id | rows | normal_rows | pre_event_rows | manufacturer_count | substation_count | system_groups | fault_groups | can_evaluate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_systems__all_faults__report_pre_7d | 112 | 65 | 47 | 2 | 59 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | control_controller\|flow_air_strainer\|leakage_water_loss\|other_review\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_dhw_storage__all_faults__report_pre_7d | 61 | 34 | 27 | 2 | 31 | dhw_storage | control_controller\|flow_air_strainer\|leakage_water_loss\|other_review\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_dhw_storage_return__all_faults__report_pre_7d | 22 | 12 | 10 | 2 | 11 | dhw_storage_return | control_controller\|leakage_water_loss\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_heating_common_only__all_faults__report_pre_7d | 26 | 16 | 10 | 2 | 15 | heating_common_only | flow_air_strainer\|leakage_water_loss\|pressure_regulator\|pump_failure\|valve_actuator | True |
| all_systems__fault_control_controller__report_pre_7d | 75 | 65 | 10 | 2 | 46 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | control_controller | True |
| all_systems__fault_flow_air_strainer__report_pre_7d | 68 | 65 | 3 | 2 | 43 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | flow_air_strainer | False |
| all_systems__fault_leakage_water_loss__report_pre_7d | 74 | 65 | 9 | 2 | 47 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | leakage_water_loss | True |
| all_systems__fault_pressure_regulator__report_pre_7d | 72 | 65 | 7 | 2 | 43 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | pressure_regulator | True |
| all_systems__fault_pump_failure__report_pre_7d | 75 | 65 | 10 | 2 | 47 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | pump_failure | True |
| all_systems__fault_valve_actuator__report_pre_7d | 72 | 65 | 7 | 2 | 45 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | valve_actuator | True |
| all_systems__all_faults__report_pre_5d | 113 | 65 | 48 | 2 | 59 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | control_controller\|flow_air_strainer\|leakage_water_loss\|other_review\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_dhw_storage__all_faults__report_pre_5d | 61 | 34 | 27 | 2 | 31 | dhw_storage | control_controller\|flow_air_strainer\|leakage_water_loss\|other_review\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_dhw_storage_return__all_faults__report_pre_5d | 22 | 12 | 10 | 2 | 11 | dhw_storage_return | control_controller\|leakage_water_loss\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_heating_common_only__all_faults__report_pre_5d | 27 | 16 | 11 | 2 | 15 | heating_common_only | flow_air_strainer\|leakage_water_loss\|pressure_regulator\|pump_failure\|valve_actuator | True |
| all_systems__fault_control_controller__report_pre_5d | 75 | 65 | 10 | 2 | 46 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | control_controller | True |
| all_systems__fault_flow_air_strainer__report_pre_5d | 68 | 65 | 3 | 2 | 43 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | flow_air_strainer | False |
| all_systems__fault_leakage_water_loss__report_pre_5d | 74 | 65 | 9 | 2 | 47 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | leakage_water_loss | True |
| all_systems__fault_pressure_regulator__report_pre_5d | 73 | 65 | 8 | 2 | 43 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | pressure_regulator | True |
| all_systems__fault_pump_failure__report_pre_5d | 75 | 65 | 10 | 2 | 47 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | pump_failure | True |
| all_systems__fault_valve_actuator__report_pre_5d | 72 | 65 | 7 | 2 | 45 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | valve_actuator | True |
| all_systems__all_faults__report_pre_3d | 113 | 65 | 48 | 2 | 59 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | control_controller\|flow_air_strainer\|leakage_water_loss\|other_review\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_dhw_storage__all_faults__report_pre_3d | 61 | 34 | 27 | 2 | 31 | dhw_storage | control_controller\|flow_air_strainer\|leakage_water_loss\|other_review\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_dhw_storage_return__all_faults__report_pre_3d | 22 | 12 | 10 | 2 | 11 | dhw_storage_return | control_controller\|leakage_water_loss\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_heating_common_only__all_faults__report_pre_3d | 27 | 16 | 11 | 2 | 15 | heating_common_only | flow_air_strainer\|leakage_water_loss\|pressure_regulator\|pump_failure\|valve_actuator | True |
| all_systems__fault_control_controller__report_pre_3d | 75 | 65 | 10 | 2 | 46 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | control_controller | True |
| all_systems__fault_flow_air_strainer__report_pre_3d | 68 | 65 | 3 | 2 | 43 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | flow_air_strainer | False |
| all_systems__fault_leakage_water_loss__report_pre_3d | 74 | 65 | 9 | 2 | 47 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | leakage_water_loss | True |
| all_systems__fault_pressure_regulator__report_pre_3d | 73 | 65 | 8 | 2 | 43 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | pressure_regulator | True |
| all_systems__fault_pump_failure__report_pre_3d | 75 | 65 | 10 | 2 | 47 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | pump_failure | True |
| all_systems__fault_valve_actuator__report_pre_3d | 72 | 65 | 7 | 2 | 45 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | valve_actuator | True |
| all_systems__all_faults__report_pre_1d | 113 | 65 | 48 | 2 | 59 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | control_controller\|flow_air_strainer\|leakage_water_loss\|other_review\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_dhw_storage__all_faults__report_pre_1d | 61 | 34 | 27 | 2 | 31 | dhw_storage | control_controller\|flow_air_strainer\|leakage_water_loss\|other_review\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_dhw_storage_return__all_faults__report_pre_1d | 22 | 12 | 10 | 2 | 11 | dhw_storage_return | control_controller\|leakage_water_loss\|pressure_regulator\|pump_failure\|valve_actuator | True |
| system_heating_common_only__all_faults__report_pre_1d | 27 | 16 | 11 | 2 | 15 | heating_common_only | flow_air_strainer\|leakage_water_loss\|pressure_regulator\|pump_failure\|valve_actuator | True |
| all_systems__fault_control_controller__report_pre_1d | 75 | 65 | 10 | 2 | 46 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | control_controller | True |
| all_systems__fault_flow_air_strainer__report_pre_1d | 68 | 65 | 3 | 2 | 43 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | flow_air_strainer | False |
| all_systems__fault_leakage_water_loss__report_pre_1d | 74 | 65 | 9 | 2 | 47 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | leakage_water_loss | True |
| all_systems__fault_pressure_regulator__report_pre_1d | 73 | 65 | 8 | 2 | 43 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | pressure_regulator | True |
| all_systems__fault_pump_failure__report_pre_1d | 75 | 65 | 10 | 2 | 47 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | pump_failure | True |
| all_systems__fault_valve_actuator__report_pre_1d | 72 | 65 | 7 | 2 | 45 | dhw_return\|dhw_storage\|dhw_storage_return\|dhw_supply\|heating_common_only | valve_actuator | True |

## Metric 상위
| dataset_id | model | threshold | rows | normal_rows | pre_event_rows | balanced_accuracy | precision | recall | f1 | normal_fpr | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_systems__all_faults__report_pre_1d | hist_gradient_boosting | 0.4000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__all_faults__report_pre_1d | hist_gradient_boosting | 0.5000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__all_faults__report_pre_1d | hist_gradient_boosting | 0.6000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__all_faults__report_pre_1d | lightgbm_depth3 | 0.4000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__all_faults__report_pre_1d | lightgbm_depth3 | 0.5000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__all_faults__report_pre_1d | lightgbm_depth3 | 0.6000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__all_faults__report_pre_1d | random_forest_depth3 | 0.4000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__all_faults__report_pre_1d | random_forest_depth3 | 0.5000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__all_faults__report_pre_1d | random_forest_depth3 | 0.6000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__all_faults__report_pre_1d | xgboost_depth3 | 0.4000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__all_faults__report_pre_1d | xgboost_depth3 | 0.5000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__all_faults__report_pre_1d | xgboost_depth3 | 0.6000 | 113 | 65 | 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 48 |
| all_systems__fault_control_controller__report_pre_1d | random_forest_depth3 | 0.5000 | 75 | 65 | 10 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 10 |
| all_systems__fault_leakage_water_loss__report_pre_1d | random_forest_depth3 | 0.4000 | 74 | 65 | 9 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 9 |
| all_systems__fault_leakage_water_loss__report_pre_1d | random_forest_depth3 | 0.5000 | 74 | 65 | 9 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 9 |
| all_systems__fault_pressure_regulator__report_pre_1d | random_forest_depth3 | 0.4000 | 73 | 65 | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 8 |
| all_systems__fault_pressure_regulator__report_pre_1d | random_forest_depth3 | 0.5000 | 73 | 65 | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 8 |
| all_systems__fault_pump_failure__report_pre_1d | random_forest_depth3 | 0.4000 | 75 | 65 | 10 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 10 |
| all_systems__fault_pump_failure__report_pre_1d | random_forest_depth3 | 0.5000 | 75 | 65 | 10 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 65 | 0 | 0 | 10 |
| system_dhw_storage__all_faults__report_pre_1d | random_forest_depth3 | 0.5000 | 61 | 34 | 27 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 34 | 0 | 0 | 27 |
| system_dhw_storage__all_faults__report_pre_1d | random_forest_depth3 | 0.6000 | 61 | 34 | 27 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 34 | 0 | 0 | 27 |
| system_heating_common_only__all_faults__report_pre_1d | random_forest_depth3 | 0.4000 | 27 | 16 | 11 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 16 | 0 | 0 | 11 |
| system_heating_common_only__all_faults__report_pre_1d | random_forest_depth3 | 0.5000 | 27 | 16 | 11 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 16 | 0 | 0 | 11 |
| system_heating_common_only__all_faults__report_pre_1d | random_forest_depth3 | 0.6000 | 27 | 16 | 11 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 16 | 0 | 0 | 11 |
| all_systems__fault_control_controller__report_pre_1d | random_forest_depth3 | 0.4000 | 75 | 65 | 10 | 0.9923 | 0.9091 | 1.0000 | 0.9524 | 0.0154 | 64 | 1 | 0 | 10 |
| all_systems__fault_valve_actuator__report_pre_1d | random_forest_depth3 | 0.4000 | 72 | 65 | 7 | 0.9923 | 0.8750 | 1.0000 | 0.9333 | 0.0154 | 64 | 1 | 0 | 7 |
| system_dhw_storage_return__all_faults__report_pre_1d | random_forest_depth3 | 0.5000 | 22 | 12 | 10 | 0.9583 | 0.9091 | 1.0000 | 0.9524 | 0.0833 | 11 | 1 | 0 | 10 |
| system_dhw_storage__all_faults__report_pre_1d | random_forest_depth3 | 0.4000 | 61 | 34 | 27 | 0.9559 | 0.9000 | 1.0000 | 0.9474 | 0.0882 | 31 | 3 | 0 | 27 |
| system_dhw_storage__all_faults__report_pre_1d | xgboost_depth3 | 0.5000 | 61 | 34 | 27 | 0.9521 | 0.9286 | 0.9630 | 0.9455 | 0.0588 | 32 | 2 | 1 | 26 |
| all_systems__fault_control_controller__report_pre_1d | hist_gradient_boosting | 0.4000 | 75 | 65 | 10 | 0.9500 | 1.0000 | 0.9000 | 0.9474 | 0.0000 | 65 | 0 | 1 | 9 |
| all_systems__fault_control_controller__report_pre_1d | hist_gradient_boosting | 0.5000 | 75 | 65 | 10 | 0.9500 | 1.0000 | 0.9000 | 0.9474 | 0.0000 | 65 | 0 | 1 | 9 |
| all_systems__fault_control_controller__report_pre_1d | hist_gradient_boosting | 0.6000 | 75 | 65 | 10 | 0.9500 | 1.0000 | 0.9000 | 0.9474 | 0.0000 | 65 | 0 | 1 | 9 |
| all_systems__fault_control_controller__report_pre_1d | random_forest_depth3 | 0.6000 | 75 | 65 | 10 | 0.9500 | 1.0000 | 0.9000 | 0.9474 | 0.0000 | 65 | 0 | 1 | 9 |
| all_systems__fault_pump_failure__report_pre_1d | hist_gradient_boosting | 0.4000 | 75 | 65 | 10 | 0.9500 | 1.0000 | 0.9000 | 0.9474 | 0.0000 | 65 | 0 | 1 | 9 |
| all_systems__fault_pump_failure__report_pre_1d | random_forest_depth3 | 0.6000 | 75 | 65 | 10 | 0.9500 | 1.0000 | 0.9000 | 0.9474 | 0.0000 | 65 | 0 | 1 | 9 |
| system_dhw_storage_return__all_faults__report_pre_1d | random_forest_depth3 | 0.6000 | 22 | 12 | 10 | 0.9500 | 1.0000 | 0.9000 | 0.9474 | 0.0000 | 12 | 0 | 1 | 9 |
| system_dhw_storage_return__all_faults__report_pre_5d | xgboost_depth3 | 0.6000 | 22 | 12 | 10 | 0.9500 | 1.0000 | 0.9000 | 0.9474 | 0.0000 | 12 | 0 | 1 | 9 |
| all_systems__fault_control_controller__report_pre_1d | logistic_balanced | 0.5000 | 75 | 65 | 10 | 0.9462 | 0.5882 | 1.0000 | 0.7407 | 0.1077 | 58 | 7 | 0 | 10 |
| all_systems__fault_control_controller__report_pre_5d | logistic_balanced | 0.5000 | 75 | 65 | 10 | 0.9462 | 0.5882 | 1.0000 | 0.7407 | 0.1077 | 58 | 7 | 0 | 10 |
| all_systems__fault_leakage_water_loss__report_pre_1d | hist_gradient_boosting | 0.5000 | 74 | 65 | 9 | 0.9444 | 1.0000 | 0.8889 | 0.9412 | 0.0000 | 65 | 0 | 1 | 8 |

## 해석
- 통과 후보가 특정 system group 또는 fault group에 몰리면, pre_event는 전체 공통 문제가 아니라 `system/fault/window`별 문제로 다뤄야 한다.
- `report_pre_1d/3d`가 상위에 오르면 7일 전조보다 단기 징후 중심으로 재정의해야 한다.
- fault group별 후보가 강하면 출동 우선순위와 고장군 taxonomy를 pre_event 모델 앞단에 연결해야 한다.
- `report_pre_1d` 완전 분리처럼 보이는 결과는 운영상 “하루 전 상태 감지”로 두고, “며칠 전 조기탐지”는 3일/5일/7일 후보에서 별도 판단한다.

## 한계
- M1/M2는 같은 PreDist 계열이므로 완전 독립 외부 검증은 아니다.
- 세분화할수록 샘플 수가 작아져 과적합 위험이 커진다.
- 이 결과는 운영 확정이 아니라 다음 label/window 잠금 후보를 찾는 통합 실험이다.

## 품질 검증
| dataset_id | model | fold | quality_check | passed | detail |
| --- | --- | --- | --- | --- | --- |
| all_systems__all_faults__report_pre_7d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_7d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_7d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_7d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_7d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_7d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_flow_air_strainer__report_pre_7d |  |  | skipped_insufficient_data_audit_only | True | rows=68, label_counts={0: 65, 1: 3} |
| all_systems__fault_leakage_water_loss__report_pre_7d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_7d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_7d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_7d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_7d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_5d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_5d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_5d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_5d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_5d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_flow_air_strainer__report_pre_5d |  |  | skipped_insufficient_data_audit_only | True | rows=68, label_counts={0: 65, 1: 3} |
| all_systems__fault_leakage_water_loss__report_pre_5d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_5d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_5d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_5d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_5d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_3d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_3d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_3d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_3d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_3d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_flow_air_strainer__report_pre_3d |  |  | skipped_insufficient_data_audit_only | True | rows=68, label_counts={0: 65, 1: 3} |
| all_systems__fault_leakage_water_loss__report_pre_3d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_3d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_3d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_3d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_3d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__all_faults__report_pre_1d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage__all_faults__report_pre_1d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_dhw_storage_return__all_faults__report_pre_1d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| system_heating_common_only__all_faults__report_pre_1d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_control_controller__report_pre_1d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_flow_air_strainer__report_pre_1d |  |  | skipped_insufficient_data_audit_only | True | rows=68, label_counts={0: 65, 1: 3} |
| all_systems__fault_leakage_water_loss__report_pre_1d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_leakage_water_loss__report_pre_1d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pressure_regulator__report_pre_1d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_pump_failure__report_pre_1d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | dummy_most_frequent | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | dummy_most_frequent | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | dummy_most_frequent | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | dummy_most_frequent | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | dummy_most_frequent | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | logistic_balanced | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | logistic_balanced | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | logistic_balanced | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | logistic_balanced | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | logistic_balanced | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | random_forest_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | random_forest_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | random_forest_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | random_forest_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | random_forest_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | hist_gradient_boosting | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | hist_gradient_boosting | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | hist_gradient_boosting | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | hist_gradient_boosting | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | hist_gradient_boosting | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | lightgbm_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | lightgbm_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | lightgbm_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | lightgbm_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | lightgbm_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | xgboost_depth3 | 1.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | xgboost_depth3 | 2.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | xgboost_depth3 | 3.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | xgboost_depth3 | 4.0000 | train_test_group_overlap_zero | True |  |
| all_systems__fault_valve_actuator__report_pre_1d | xgboost_depth3 | 5.0000 | train_test_group_overlap_zero | True |  |
|  |  |  | feature_count_common13 | True | 13 |
|  |  |  | raw_zip_exists | True | C:\3rd_Project\HeatGridAgent\05_데이터셋\PreDist\predist_dataset.zip |
|  |  |  | manufacturer_metadata_only | True | manufacturer used for split/audit, not feature |
|  |  |  | candidate_pass_count | True | 228 |

source commit: `09da59e0b4ca66f37bae0e8c2b811bad7789a054`
