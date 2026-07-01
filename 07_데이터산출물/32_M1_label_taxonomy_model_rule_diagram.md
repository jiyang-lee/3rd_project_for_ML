# M1 Label Taxonomy / Model / Rule 다이어그램

## 1. 전체 Label 구조

```mermaid
flowchart TD
    A["M1 전체 기록"] --> B["normal"]
    A --> C["event"]

    B --> B1["source: normal_events.csv"]
    B --> B2["회사 제공 normal 35건 유지"]
    B --> B3["모델 학습에서는 negative 기준"]

    C --> D["fault"]
    C --> E["task"]
    C --> F["activity"]

    D --> D1["source: disturbances.csv type=fault"]
    D --> D2["source: faults.csv 매칭 33건"]
    D --> D3["fault 내부 metadata 보유"]

    E --> E1["source: disturbances.csv type=task"]
    E --> E2["efd_possible 부여 안 함"]
    E --> E3["window/label 재설계 대상"]

    F --> F1["source: disturbances.csv type=activity"]
    F --> F2["efd_possible 부여 안 함"]
    F --> F3["전조보다 상태/활동 감지에 가까울 수 있음"]
```

핵심은 이거다.

| 단계 | 현재 의미 |
| --- | --- |
| `normal` | 회사가 정상이라고 준 35개 window |
| `event` | disturbance 기반 이벤트 전체 |
| `fault/task/activity` | event를 다시 나눈 최종 목표 class |
| `efd_possible` | fault 안에서만 쓰는 metadata, 최상위 class가 아님 |

## 2. Fault 내부 Label 흐름

```mermaid
flowchart TD
    A["fault event"] --> B["faults.csv 매칭됨?"]

    B -->|"yes: 33건"| C["fault detail 있음"]
    B -->|"no: 34건"| B0["efd_possible_unknown<br/>4분류 fault 후보 audit"]

    C --> D["fault label 있음?"]
    D -->|"known: 31건"| D1["fault_label_known"]
    D -->|"unknown: 2건<br/>Event 34, 69"| D2["fault_label_unknown<br/>학습 확정 전 review"]

    C --> E["efd_possible 값"]
    E -->|"True: 29건"| F["pre_event 후보"]
    E -->|"False: 4건"| G["fault event이지만<br/>조기탐지 positive 아님"]

    F --> H["strict 조건 만족?"]
    H -->|"yes"| I["strict_positive"]
    H -->|"no"| J["weak_positive"]

    I --> I1["조건: efd_possible=True"]
    I --> I2["Possible anomaly start/end 있음"]
    I --> I3["Training start/end 있음"]
    I --> I4["Report date 있음"]

    J --> J1["efd_possible=True지만<br/>anomaly start 등 일부 부족"]
    J --> J2["strict보다 라벨 신뢰 낮음"]
    J --> J3["06번에서 확장 실험했지만<br/>최종 잠금 기준 아님"]
```

## 3. Strict / Weak 처리 규칙

| 구분 | 쓰임 | 규칙 | 현재 결론 |
| --- | --- | --- | --- |
| `strict_positive` | 조기탐지 pre-event 핵심 positive | `efd_possible=True`이고 anomaly/training/report metadata가 충분한 fault | 현재 pre-event 기준의 중심 |
| `weak_positive` | positive 확장 후보 | `efd_possible=True`지만 strict 조건 일부 부족 | 실험은 했지만 최종 잠금 기준은 아님 |
| `Event 20` | strict 후보였지만 coverage 낮음 | 7일 window coverage 부족 | 학습/평가 제외, audit 유지 |
| `Event 34` | unknown fault label | label 판단 불명확 | 학습 제외, review |
| `Event 69` | unknown + Training end 없음 | metadata 부족 | 학습 제외, review |
| `Event 67` | long anomaly | 장기 anomaly flag | main에는 포함, sensitivity에서 확인 |

## 4. 모델이 붙는 위치

```mermaid
flowchart TD
    A["M1 10분 센서값"] --> B["최근 7일 window"]
    B --> C["feature 계산"]

    C --> C1["compact13_overlap<br/>현재 pre-event 기준 feature"]
    C --> C2["expanded154<br/>비교/확장 실험용"]

    C1 --> D["Fault pre-event gate"]
    D --> D1["label: normal vs strict pre_event"]
    D --> D2["model: LogisticRegression(class_weight=balanced)"]
    D --> D3["threshold: 0.6"]
    D --> D4["결론: fault_pre_event_gate_v1_locked_for_M1"]

    D4 --> E["lead-time audit"]
    E --> E1["D-7, D-5, D-3, D-1, D-12h, D-0"]
    E --> E2["stable crossing 기준"]
    E --> E3["고장군별 며칠 전부터 잡히는지 표로 해석"]

    E3 --> F["dispatch priority v1"]
    F --> F1["risk_probability 0.55"]
    F --> F2["leadtime_urgency 0.30"]
    F --> F3["group_weight 0.15"]
    F --> F4["priority_score / tier / why_reason"]
```

## 5. 다른 모델들은 어디에 있었나

```mermaid
flowchart TD
    A["모델 실험들"] --> B["pre_event 조기탐지"]
    A --> C["normal vs fault gate"]
    A --> D["task/activity gate"]
    A --> E["normal vs event gate"]

    B --> B1["현재 잠금 후보"]
    B1 --> B2["LogisticRegression + compact13_overlap + threshold 0.6"]

    C --> C1["RandomForest 등 비교"]
    C --> C2["fault event 구분에는 도움"]
    C --> C3["하지만 현재 lead-time/priority 흐름에는 사용 안 함"]

    D --> D1["Logistic / RF / ExtraTrees / boosting 비교"]
    D --> D2["task/activity는 모델보다 window/label 재설계 우선"]

    E --> E1["normal vs event 단일 gate"]
    E --> E2["fault/task/activity를 한 덩어리로 묶어 불안정"]
    E --> E3["중단하고 class별 gate로 분리"]
```

## 6. 한 줄 결론

현재 가장 중요한 운영 흐름은 아래 하나다.

```text
M1 센서값
→ 최근 7일 window
→ compact13_overlap feature
→ LogisticRegression
→ pre_event 위험확률
→ threshold 0.6
→ 고장군별 lead-time audit
→ priority score
```

그리고 `normal / fault / task / activity` 4분류는 아직 최종 모델이 아니라 아래 순서로 가는 중이다.

```text
1. normal vs fault는 먼저 잠금 가능성 있음
2. fault 내부에서는 pre_event 조기탐지 흐름이 가장 많이 정리됨
3. task/activity는 label/window 정책을 더 정리해야 함
4. efd_possible은 fault 내부 속성이지 class label이 아님
```

## 7. 용어 다시 보기

| 용어 | 쉬운 뜻 |
| --- | --- |
| `taxonomy` | label을 어떤 층으로 나눌지 정한 구조 |
| `metadata` | 정답 label은 아니지만 판단에 참고하는 정보 |
| `efd_possible` | 이 fault가 조기탐지 후보인지 나타내는 fault 내부 정보 |
| `strict_positive` | metadata가 충분해서 조기탐지 positive로 믿고 쓰는 fault |
| `weak_positive` | positive 후보지만 strict보다 근거가 약한 fault |
| `compact13_overlap` | 현재 조기탐지 모델이 쓰는 13개 feature |
| `threshold 0.6` | 위험확률이 0.6 이상이면 pre_event로 보는 기준 |
| `lead-time audit` | 며칠 전부터 threshold를 넘는지 확인한 표 |
| `priority score` | 위험확률, 리드타임, 고장군 가중치를 합친 운영 점수 |
