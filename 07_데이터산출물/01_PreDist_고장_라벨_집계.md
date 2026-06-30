# PreDist 고장 라벨 집계

## 기준

- 데이터 위치: `05_데이터셋/PreDist/metadata/*/faults.csv`
- 집계 기준: 고객 신고 기반 고장 리포트(`faults.csv`)의 `Fault label`
- 총 고장 리포트 수: 73건
- 고장 종류 수: 20종
- 주의: `disturbances.csv`의 `type=fault`는 이벤트 목록이며 고장 유형명이 없으므로, 고장 종류 집계는 `faults.csv`를 기준으로 한다.

## 고장 종류별 개수

| 한글 고장명 | 원문 라벨 | manufacturer_1 | manufacturer_2 | 합계 |
|---|---|---:|---:|---:|
| 제어장치 파라미터 설정 오류 | Control unit: Incorrect parameterisation | 11 | 2 | 13 |
| 누수 | Leakage | 2 | 8 | 10 |
| 난방 회로 펌프 고장 | Failure of the heating circuit pump | 4 | 4 | 8 |
| 차압 조절기 설정 오류 | Incorrect setting of the differential pressure regulator | 2 | 6 | 8 |
| 미상 | unknown | 2 | 5 | 7 |
| 급탕 저장탱크 충전펌프 고장 | Failure of the domestic hot water storage charging pump | 1 | 5 | 6 |
| 배관 내 공기 혼입 | Air in the piping system | 0 | 3 | 3 |
| 1차측 전동 제어밸브 액추에이터 고장 | Motorised control valve (primary side): Actuator defective | 2 | 1 | 3 |
| 차압 조절기 고장 | Differential pressure regulator defective | 2 | 0 | 2 |
| 안전밸브 폐쇄 불량에 따른 물 손실 | Safety relief valve: Water loss, does not close properly | 2 | 0 | 2 |
| 차단밸브 닫힘 | Shut-off valve closed | 1 | 1 | 2 |
| 차압 조절기 닫힘 고착 | Differential pressure regulator jams when closed | 0 | 1 | 1 |
| 열량계 고장 | Failure of the thermal energy meter | 0 | 1 | 1 |
| 열교환기 외부 누수 | Heat exchanger: Leakage, external | 1 | 0 | 1 |
| 팽창탱크 예압 부족 | Low pre-charge at the expansion vessel | 0 | 1 | 1 |
| 1차측 전동 제어밸브 고장 | Motorised control valve (primary side) defective | 1 | 0 | 1 |
| 1차측 전동 제어밸브 닫힘 고착 | Motorised control valve (primary side): Control valve jams when closed | 1 | 0 | 1 |
| 1차측 전동 제어밸브 액추에이터 동작시간 설정 오류 | Motorised control valve (primary side): Incorrect setting of the actuator travel time | 0 | 1 | 1 |
| 2차측 스트레이너 유량 저하 | Strainer (secondary side): Poor flow rate | 0 | 1 | 1 |
| 온도 감시/제어기 고장 | Temperature monitor/controller defective | 1 | 0 | 1 |

## 요약

- 가장 많은 고장 유형은 `제어장치 파라미터 설정 오류`로 13건이다.
- 상위 4개 유형은 `제어장치 파라미터 설정 오류`, `누수`, `난방 회로 펌프 고장`, `차압 조절기 설정 오류`이다.
- `미상` 라벨이 7건 있어, 모델 학습 시 별도 클래스 유지 또는 제외 여부를 결정해야 한다.
- 1건짜리 희소 라벨이 9종 있어, 다중분류 모델에서는 클래스 불균형 처리가 필요하다.
