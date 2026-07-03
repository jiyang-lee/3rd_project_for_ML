# M1 Scope

이 패키지는 `manufacturer 1`만 대상으로 한다.

## 범위

```text
manufacturer == manufacturer 1
```

M2 row는 데이터 import 단계에서 제외한다. 따라서 anomaly 학습, best score bridge, specialist gate 계산, priority 산정, validation report는 모두 M1 기준이다.

## 남긴 단계

```text
raw inventory
canonical window import
M1 anomaly baseline
current-best risk/leadtime/priority bridge
operational agent card
M1 specialist gate scoring
M1 hybrid priority promotion
validation and ablation
```

## 해석 제한

- 이 결과는 M1에 특화된 운영 우선순위 산정 결과다.
- M2 또는 전체 제조사 공통 모델 성능을 주장하지 않는다.
- leadtime은 고장 시점을 직접 맞히는 모델이 아니라 priority 참고 신호다.
- priority는 현장 조치 순서를 돕는 ranking 신호이며, 자동 정비 지시가 아니다.
