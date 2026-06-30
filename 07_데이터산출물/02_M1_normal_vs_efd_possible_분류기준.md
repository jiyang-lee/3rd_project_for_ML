# M1 normal vs efd_possible 분류 기준

## 목표

M1 운영 시계열만 사용해 `normal`과 `efd_possible`을 구분하기 위한 첫 전처리 데이터셋을 만든다.

## 라벨 정의

| label | 원천 | 포함 기준 | 건수 |
|---|---|---|---:|
| `normal` | `normal_events.csv` | 모든 정상 이벤트 | 35 |
| `efd_possible` | `faults.csv` | `efd_possible=True`이고 anomaly/training 기준 시간이 모두 있는 fault | 15 |

제외 기준은 다음과 같다.

- strict 조건을 만족하지 않는 fault
- 이벤트 타입만 있고 고장 분류 기준이 아닌 disturbance 목록
- 다른 제조사 그룹 데이터

## 윈도우 기준

| label | window start | window end | 길이 |
|---|---|---|---:|
| `normal` | `Event start` | `Event end` | 7일 |
| `efd_possible` | `Report date - 7 days` | `Report date` | 7일 |

positive의 `Possible anomaly start/end`는 라벨 품질 필터로만 사용한다. feature window는 normal과 길이를 맞추기 위해 신고 직전 7일로 통일한다.

## 센서 컬럼 기준

M1 내부에서도 기계실별 설비 구성이 달라 센서 후보는 26개지만, 첫 기준선에서는 모든 M1 기계실에 존재하는 10개 컬럼만 사용한다.

| 컬럼 | 설명 |
|---|---|
| `outdoor_temperature` | Outdoor temperature |
| `s_hc1_supply_temperature` | Heat circuit 1 flow temperature (secondary) |
| `s_hc1_supply_temperature_setpoint` | Heat circuit 1 reference flow temperature (secondary) |
| `p_hc1_return_temperature` | Heat circuit 1 return temperature (primary side) |
| `p_net_meter_energy` | Energy |
| `p_net_meter_volume` | Volume |
| `p_net_meter_heat_power` | Power |
| `p_net_meter_flow` | Flow |
| `p_net_supply_temperature` | Primary flow temperature |
| `p_net_return_temperature` | Primary return temperature |

이 기준은 모델이 설비 구성 차이를 먼저 학습하는 위험을 줄이고, normal/efd_possible 차이에 집중시키기 위한 것이다.

## feature 기준

각 이벤트 row마다 7일 구간을 잘라 다음 feature를 만든다.

- 각 센서별 `mean`, `std`, `min`, `max`, `median`, `last_minus_first`, `missing_rate`
- 이벤트 단위 `sample_count`, `expected_sample_count`, `coverage_rate`

## 검증 기준

- event index 총 50행
- label 분포: `normal=35`, `efd_possible=15`
- 모든 row의 `manufacturer`는 `manufacturer_1`
- 모든 window 길이는 7일
- 모든 feature row의 `sample_count > 0`
