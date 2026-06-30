# PreDist 데이터셋 한눈에 보기

## 1. 데이터셋 정체

- 데이터명: `PreDist`
- 출처: [Zenodo - PreDist Dataset](https://zenodo.org/records/17522255)
- 주제: `지역난방 기계실(substation)` 운영 시계열 + 고장/정비 라벨
- 용도: 이상탐지, 고장 조기탐지, 리드타임 추정, 정비 우선순위화

## 2. 폴더 구조

실제 확인 경로:

- `C:\Users\Admin\AppData\Local\Temp\predist_inspect`

구조:

```text
predist_inspect/
├─ manufacturer 1/
│  ├─ disturbances.csv
│  ├─ faults.csv
│  ├─ feature_descriptions.csv
│  ├─ normal_events.csv
│  └─ operational_data/
├─ manufacturer 2/
│  ├─ disturbances.csv
│  ├─ faults.csv
│  ├─ feature_descriptions.csv
│  ├─ normal_events.csv
│  └─ operational_data/
├─ README.md
└─ predist_dataset.zip
```

## 3. 파일 개수 요약

| 구분 | 개수 |
|---|---:|
| 전체 CSV 파일 수 | 101 |
| manufacturer 1 운영 CSV | 35 |
| manufacturer 2 운영 CSV | 58 |
| 전체 기계실 수 | 93 |

## 4. 각 파일이 의미하는 것

| 파일 | 의미 |
|---|---|
| `operational_data/substation_<id>.csv` | 기계실별 운영 시계열 |
| `faults.csv` | 고객 신고 기반 고장 이벤트 라벨 |
| `disturbances.csv` | 정비/활동/고장 발생 이력 |
| `normal_events.csv` | 정상 구간 평가용 이벤트 |
| `feature_descriptions.csv` | 센서 컬럼 설명과 단위 |

## 5. 메타 파일 컬럼

### `faults.csv`

| 컬럼 | 의미 |
|---|---|
| `Event ID` | 이벤트 ID |
| `substation ID` | 기계실 ID |
| `Report date` | 고객 신고 시점 |
| `Problem EN` | 문제 유형 |
| `Event description EN` | 문제 설명 |
| `Possible anomaly start` | 이상 징후 시작 가능 시점 |
| `Possible anomaly end` | 이상 징후 종료 가능 시점 |
| `Training start` / `Training end` | 추천 학습 구간 |
| `efd_possible` | 조기탐지 가능 여부 |
| `Fault label` | 고장 라벨 |
| `Monitoring potential` | 센서만으로 탐지 가능한 정도 |

### `disturbances.csv`

| 컬럼 | 의미 |
|---|---|
| `substation ID` | 기계실 ID |
| `Event start` | 이벤트 시작 시점 |
| `type` | `fault`, `task`, `activity` |

### `normal_events.csv`

| 컬럼 | 의미 |
|---|---|
| `Event ID` | 이벤트 ID |
| `substation ID` | 기계실 ID |
| `Event start` / `Event end` | 정상 구간 |
| `Training start` / `Training end` | 추천 학습 구간 |

### `feature_descriptions.csv`

| 제조사 | 컬럼 |
|---|---|
| manufacturer 1 | `column`, `description`, `unit` |
| manufacturer 2 | `column`, `unit` |

## 6. 메타 레코드 수

| 제조사 | faults | disturbances | normal_events |
|---|---:|---:|---:|
| manufacturer 1 | 33 | 165 | 35 |
| manufacturer 2 | 40 | 163 | 30 |

## 7. 운영 데이터 컬럼 성격

운영 CSV는 `;` 구분자이며 첫 컬럼은 `timestamp`다.

주요 컬럼 그룹:

| 그룹 | 예시 컬럼 |
|---|---|
| 외기온 | `outdoor_temperature` |
| 공급/환수 온도 | `s_hc1_supply_temperature`, `p_hc1_return_temperature`, `p_net_supply_temperature`, `p_net_return_temperature` |
| 급탕 저장조 온도 | `s_dhw_upper_storage_temperature`, `s_dhw_lower_storage_temperature` |
| 열량/유량/에너지 | `p_net_meter_heat_power`, `p_net_meter_flow`, `p_net_meter_energy`, `p_net_meter_volume` |
| 설정값 | `*_setpoint` |
| 제어 상태 | `*_control_unit_mode`, `*_control_valve_position`, `*_heating_pump_status*` |

## 8. 제조사별 운영 컬럼 차이

### manufacturer 1 대표 컬럼

```text
outdoor_temperature
s_hc1_supply_temperature
s_hc1_supply_temperature_setpoint
s_dhw_supply_temperature
s_dhw_supply_temperature_setpoint
p_hc1_return_temperature
s_dhw_upper_storage_temperature
s_dhw_lower_storage_temperature
p_net_meter_energy
p_net_meter_volume
p_net_meter_heat_power
p_net_meter_flow
p_net_supply_temperature
p_net_return_temperature
... 일부 기계실은 hc1.1, hc1.2 회로 컬럼 포함
```

특징:

- 온도/계량 중심 컬럼이 많다
- 일부 기계실은 복수 난방 회로(`hc1.1`, `hc1.2`)가 있다

### manufacturer 2 대표 컬럼

```text
outdoor_temperature
p_dhw_control_valve_position
p_dhw_return_temperature
p_hc1_control_valve_position_setpoint
p_hc1_return_temperature
p_hc1_return_temperature_setpoint
p_net_meter_energy
p_net_meter_flow
p_net_meter_heat_power
p_net_meter_volume
p_net_return_temperature
p_net_supply_temperature
s_dhw_control_unit_mode
s_hc1_control_unit_mode
s_hc1_heating_pump_status_setpoint
s_hc1_supply_temperature
s_hc1_supply_temperature_setpoint
... 일부 기계실은 hc1.1, hc1.2, hc1.3 회로 컬럼 포함
```

특징:

- 제어밸브 위치, 펌프 상태, 제어모드 컬럼이 더 많다
- 복수 회로(`hc1.1`, `hc1.2`, `hc1.3`)가 더 자주 보인다

## 9. 실제 샘플 파일 확인 결과

| 샘플 파일 | 행 수 | 컬럼 수 | 시작 시각 | 종료 시각 |
|---|---:|---:|---|---|
| `manufacturer 1/operational_data/substation_1.csv` | 112,164 | 15 | 2018-06-10 00:40:00 | 2020-07-28 23:50:00 |
| `manufacturer 2/operational_data/substation_1.csv` | 5,094 | 23 | 2020-02-26 15:10:00 | 2020-04-02 00:00:00 |

샘플 첫 행 예시:

```text
manufacturer 1
timestamp;outdoor_temperature;s_hc1_supply_temperature;...;p_net_supply_temperature;p_net_return_temperature
2018-06-10 00:40:00;14.3;32.3;26.0;53.9;64.0;38.1;57.0;57.2;;;;;;

manufacturer 2
timestamp;s_dhw_supply_temperature_setpoint;outdoor_temperature;...;p_net_meter_volume;p_net_supply_temperature
2020-02-26 15:10:00;13.3;2.0;Tag;Tag;23.0;20.0;8.0;63.9;12.1;11.4;30.0;10.0;EIN;10.0;;13.8;;;;;;
```

## 10. 한 줄 결론

PreDist는 `기계실별 운영 시계열`만 있는 데이터가 아니라, `고장 라벨`, `정비 이력`, `정상 구간`까지 함께 있어서 HeatGrid 같은 `다중 기계실 이상탐지 + 우선순위화` 주제에 바로 연결하기 좋은 데이터셋이다.

## 11. 해석 시 주의점

- 기계실마다 컬럼 구성이 완전히 같지 않다
- 제조사별 센서 단위가 일부 다르다
- 일부 기계실은 데이터 기간이 짧다
- 모델링 전에는 `공통 컬럼 교집합`, `단위 정규화`, `결측/공백 처리`를 먼저 잡는 게 안전하다
