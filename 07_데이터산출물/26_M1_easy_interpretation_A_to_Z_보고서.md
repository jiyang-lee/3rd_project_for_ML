# M1 쉬운 해석 A to Z 보고서

## Executive Summary

- **최종 결론은 "4분류 모델"이 아니라 "계층형 운영 판단 정책"이다.** 처음에는 `normal / fault / task / activity`를 한 번에 맞히는 모델을 생각할 수 있지만, 검증 결과 라벨마다 시간적 의미가 달랐다. 그래서 M1은 먼저 장애 위험을 잡고, 그다음 작업/활동 맥락을 붙이는 구조가 맞다.

- **실제로 예측 모델로 쓸 수 있는 핵심은 `fault`다.** `fault_no_overlap + compact13 + random_forest_balanced_depth3 + threshold 0.5`가 현재 운영 기준선이다. 장애 recall은 `0.8909`, 정상 오탐률은 `0.2000`이다. 쉽게 말하면 장애 55건 중 49건을 잡고, 정상 35건 중 7건은 잘못 위험으로 울린다.

- **`task`는 예측 대상이 아니라 사후 맥락 라벨이다.** `task_post_1d`는 잘 맞지만, 사전 예측으로 볼 수 있는 근거는 약하다. 따라서 "정비/작업이 일어난 뒤 어떤 운영 맥락이었는지 설명하는 라벨"로 써야 한다.

- **`activity`는 좋아 보였지만 아직 예측 성공이라고 말하면 안 된다.** `activity_pre_1d`는 완벽하게 보였지만, missingness-only 모델도 완벽했다. 즉 센서값의 실제 패턴보다 "데이터가 비어 있는 방식"을 배웠을 가능성이 크다. 그래서 activity는 보조 신호로만 둔다.

- **25번에서 모든 모델 탐색을 했지만 기존 fault gate를 유지하는 것이 최종 선택이다.** 새 후보는 fault recall을 `0.9455`까지 올렸지만 정상 오탐률이 `0.2857`까지 올라갔다. M1의 운영 조건은 정상 오탐률 `0.20` 우선, 최대 `0.25` 허용이므로 새 후보는 탈락이다.

## A. 이 프로젝트가 풀려는 문제

이 프로젝트의 핵심 질문은 단순히 "정확도가 높은 모델을 만들 수 있나?"가 아니다.

진짜 질문은 다음이다.

> 기계실 데이터만 보고, 운영자가 미리 봐야 할 위험 신호와 이미 발생한 운영 맥락을 구분할 수 있는가?

그래서 모델은 세 가지 일을 구분해야 한다.

1. **미리 위험을 알려주는 일**
2. **사건이 발생한 뒤 맥락을 설명하는 일**
3. **아직 믿기 어려운 신호를 검토 대상으로 남기는 일**

이 구분이 중요한 이유는 `fault`, `task`, `activity`가 모두 같은 종류의 라벨이 아니었기 때문이다.

## B. 처음 아이디어: 4분류 모델

처음에는 모든 이벤트를 바로 네 가지 중 하나로 분류하는 구조를 생각할 수 있다.

```text
normal / fault / task / activity
```

겉보기에는 이 구조가 가장 깔끔하다. 하지만 실제 운영에서는 문제가 있다.

- `fault`는 "미리 잡고 싶은 위험"이다.
- `task`는 "작업이나 정비가 있었던 운영 맥락"에 가깝다.
- `activity`는 예측 후보처럼 보였지만, 데이터 결측 패턴에 크게 의존했다.
- `normal`은 비교 기준이지, 나머지 세 라벨과 같은 성격의 이벤트가 아니다.

즉 네 라벨을 같은 레벨에서 한 번에 맞히는 방식은 모델 성능 숫자는 만들 수 있어도 운영적으로 해석하기 어렵다.

## C. 그래서 바꾼 방향: 계층형 판단

최종 방향은 아래처럼 바뀌었다.

```text
1. fault predictive gate
2. activity candidate/context check
3. task context check
4. final operational decision
```

쉬운 말로 풀면 이렇다.

1. **먼저 장애 위험인지 본다.**
2. **장애가 아니면 activity 보조 신호를 본다.**
3. **작업/정비 맥락이 있으면 task context를 붙인다.**
4. **아무 신호도 없으면 normal_or_monitor로 둔다.**

여기서 중요한 규칙은 `fault` 우선이다. 장애 위험이 잡히면, task나 activity 신호가 같이 있어도 최종 라벨은 `predictive_fault_risk`가 된다. task/activity는 보조 태그로 남긴다.

## D. 라벨별 쉬운 정의

| 라벨 | 쉬운 의미 | 최종 역할 |
| --- | --- | --- |
| `normal` | 비교 기준이 되는 정상 구간 | 기준 집단 |
| `fault` | 미리 잡고 싶은 장애 위험 | predictive gate |
| `task` | 작업/정비가 있었던 맥락 | post-event context classifier |
| `activity` | 활동 신호처럼 보이지만 검토가 필요한 신호 | overlap/missingness-sensitive candidate |

## E. 성능 지표를 쉽게 읽는 법

이 보고서에서 중요한 지표는 세 개다.

| 지표 | 쉬운 뜻 | 왜 중요한가 |
| --- | --- | --- |
| recall | 실제 장애 중 모델이 잡은 비율 | 장애를 놓치지 않기 위해 중요 |
| normal FPR | 정상인데 위험이라고 잘못 울린 비율 | 알람 피로도를 줄이기 위해 중요 |
| balanced accuracy | 정상/장애 양쪽을 균형 있게 본 정확도 | 데이터 수가 작고 불균형할 때 유용 |

M1에서는 **fault recall을 높이는 것**이 1순위지만, 정상 오탐률이 너무 높아지면 운영에서 쓰기 어렵다. 그래서 25번에서는 다음 기준을 썼다.

- 우선 목표: fault recall 최대화
- 1차 제약: normal FPR `<= 0.20`
- 최대 허용: normal FPR `<= 0.25`
- 검증 방식: `substation_id` 기준 Nested Group CV

## F. Fault는 왜 predictive gate인가

`fault`는 사전 위험 탐지 후보로 가장 설득력이 있다.

21번 기준 모델은 다음 결과를 냈다.

| 항목 | 값 |
| --- | ---: |
| 데이터셋 | `fault_no_overlap` |
| 모델 | `compact13 + random_forest_balanced_depth3` |
| threshold | `0.5` |
| rows | 90 |
| normal rows | 35 |
| fault rows | 55 |
| balanced accuracy | 0.8455 |
| fault recall | 0.8909 |
| normal FPR | 0.2000 |
| TP / FN | 49 / 6 |
| TN / FP | 28 / 7 |

쉬운 해석은 이렇다.

> 장애 55건 중 49건은 잡았다. 장애 6건은 놓쳤다. 정상 35건 중 28건은 정상으로 봤고, 7건은 위험으로 잘못 울렸다.

완벽하지는 않지만, 운영에서 "위험을 먼저 잡는 gate"로 쓸 수 있는 수준이다.

## G. 그런데 fault도 완전 lock은 아니다

21번 결론은 `fault_gate_lock_pending_threshold_review`였다.

이 말은 "fault를 쓸 수 없다"가 아니다. 의미는 더 섬세하다.

- threshold `0.5`에서는 기준을 통과한다.
- threshold를 조금 바꾸면 성능 균형이 흔들린다.
- 그래서 M1에서는 primary predictive gate로 쓰되, threshold 검토 여지는 남긴다.

즉 `fault`는 M1에서 가장 강한 예측 축이지만, 서비스화 전에는 알람 임계값을 운영자 관점에서 다시 조정해야 한다.

## H. Task는 왜 예측 대상이 아닌가

22번 검증에서 `task_post_1d`는 성능이 좋았다.

하지만 중요한 것은 "언제의 데이터로 맞혔는가"다.

| 후보 | 결과 |
| --- | --- |
| `task_pre_1d` | 겉보기 성능은 좋지만 overlap rate가 `0.4000` |
| `task_post_1d` | 통과 |
| `task_no_overlap` | balanced accuracy `0.6521`, recall `0.6757`, normal FPR `0.3714` |

쉬운 해석은 이렇다.

> task는 사건 전에 미리 맞히는 신호라기보다, 작업/정비가 발생한 뒤 그 맥락을 설명하는 라벨에 가깝다.

그래서 최종 역할은 다음으로 고정했다.

```text
task = post_event_context_classifier
```

보고서나 발표에서 `task 예측 성공`이라고 말하면 안 된다. 대신 `정비/작업 발생 후 맥락 분류`라고 말해야 한다.

## I. Activity는 왜 헷갈렸나

`activity`는 처음에는 꽤 좋아 보였다.

22번에서 `activity_pre_1d`와 `activity_post_1d`가 모두 거의 완벽하게 통과했다.

| 후보 | balanced accuracy | recall | normal FPR |
| --- | ---: | ---: | ---: |
| `activity_pre_1d` | 1.0000 | 1.0000 | 0.0000 |
| `activity_post_1d` | 1.0000 | 1.0000 | 0.0000 |
| `activity_no_overlap` | 0.7370 | 0.6739 | 0.2000 |

표면적으로 보면 "activity도 예측 가능하다"고 말하고 싶어진다.

하지만 `activity_no_overlap`에서 성능이 무너졌다. 즉 overlap이나 window 정의에 의존했을 가능성이 생겼다.

## J. Activity를 끝까지 의심한 이유

23번은 activity를 더 깊게 검증했다.

핵심 결과는 이렇다.

| 검증 | 결과 |
| --- | --- |
| `activity_pre_1d` | BA 1.0000, recall 1.0000, FPR 0.0000 |
| `activity_pre_1d_strict_no_overlap` | BA 1.0000, recall 1.0000, FPR 0.0000 |
| `missingness_only` | BA 1.0000 |
| high-missing feature 제거 | BA 0.7413, recall 0.7111, FPR 0.2286 |

여기서 제일 중요한 줄은 `missingness_only = 1.0000`이다.

쉬운 말로 하면:

> 센서값 자체가 아니라 "어디가 비어 있는지"만 봐도 activity를 완벽하게 맞힌다.

이건 모델이 진짜 물리적 활동 패턴을 배운 것이 아닐 수 있다는 강한 경고다.

## K. 그래서 Activity 결론은 보류

23번 최종 결론은 다음이다.

```text
activity_predictive_gate_pending_overlap_review
```

운영 역할은 다음으로 둔다.

```text
activity = overlap_sensitive_predictive_candidate
```

쉽게 말하면:

> activity는 예측 후보처럼 보이지만, 결측/overlap 영향이 너무 강해서 "예측 성공"이라고 잠그면 안 된다. 지금은 보조 신호로만 쓴다.

## L. 최종 정책은 어떻게 라우팅하나

24번에서 만든 최종 정책은 한 줄로 말하면 이렇다.

> fault risk를 먼저 잡고, task/activity 맥락으로 운영 판단을 보강한다.

실제 라우팅 결과는 다음과 같다.

| 최종 운영 라벨 | row 수 | 쉬운 뜻 |
| --- | ---: | --- |
| `predictive_fault_risk` | 56 | 장애 위험으로 먼저 볼 이벤트 |
| `maintenance_context_event` | 42 | 작업/정비 맥락 이벤트 |
| `activity_context_or_candidate_signal` | 47 | activity 보조 신호 이벤트 |
| `normal_or_monitor` | 34 | 특별 신호가 없거나 모니터링 대상 |
| `review_required` | 57 | 경계/충돌/보류 조건 때문에 사람이 봐야 할 이벤트 |

이 구조는 "무조건 한 라벨로 확정"하는 구조가 아니다. 운영자가 볼 수 있도록 위험, 맥락, 검토 필요 여부를 함께 남긴다.

## M. 25번에서 다시 최고의 모델을 찾은 이유

24번까지의 결론은 구조 설계였다. 그런데 남은 질문이 있었다.

> fault gate를 더 좋은 모델로 바꿀 수 있나?

그래서 25번에서는 모델 탐색을 다시 했다. 단, 단순히 점수가 높은 모델을 찾은 것이 아니다.

기준은 다음이었다.

1. fault recall을 최대화한다.
2. normal FPR은 `0.20` 이하를 우선한다.
3. 최대 허용도 `0.25`까지만 본다.
4. `substation_id` 기준 Nested Group CV로 검증한다.
5. task/activity 역할은 바꾸지 않는다.

## N. 25번 결과: 새 모델은 recall은 좋지만 오탐이 많다

25번에서 선택된 nested 후보는 fault recall을 올렸다.

| 항목 | 기존 21번 baseline | 25번 nested selected |
| --- | ---: | ---: |
| fault recall | 0.8909 | 0.9455 |
| normal FPR | 0.2000 | 0.2857 |
| balanced accuracy | 0.8455 | 0.8299 |
| macro F1 | 0.8472 | 0.8413 |
| fold BA std | 0.0855 | 0.0878 |

쉬운 해석은 이렇다.

> 새 모델은 장애를 더 많이 잡는다. 하지만 정상도 훨씬 더 많이 위험이라고 울린다.

구체적으로는:

- 기존 baseline: 정상 35건 중 FP 7건
- 새 nested 후보: 정상 35건 중 FP 10건
- 기존 baseline: 장애 55건 중 FN 6건
- 새 nested 후보: 장애 55건 중 FN 3건

즉 장애 미탐 3건을 줄이는 대신 정상 오탐 3건을 추가로 만든 셈이다.

M1 운영 제약에서는 이 trade-off를 채택하지 않는다.

## O. 왜 "최고 점수"가 아니라 "최적 운영 모델"인가

일반 ML 프로젝트에서는 recall이 더 높으면 좋아 보일 수 있다.

하지만 이 프로젝트에서는 알람이 실제 운영 판단으로 이어진다. 정상인데 계속 위험이라고 울리면 운영자는 알람을 신뢰하지 않게 된다.

그래서 25번 최종 결론은 다음이다.

```text
keep_existing_fault_gate
```

이 결론은 모델 탐색 실패가 아니다. 오히려 운영 조건을 지킨 결과다.

> "장애를 더 잡는 모델"보다 "장애를 충분히 잡으면서 정상 오탐을 제어하는 모델"이 M1에서는 더 낫다.

## P. 최종 M1 구조

최종 구조는 다음과 같다.

```text
Input event/window
  |
  |-- fault gate positive?
  |      -> predictive_fault_risk
  |
  |-- task post-event context positive?
  |      -> maintenance_context_event
  |
  |-- activity candidate signal positive?
  |      -> activity_context_or_candidate_signal
  |
  |-- none
         -> normal_or_monitor
```

우선순위는 다음이다.

```text
fault > task context > activity candidate > normal/monitor
```

단, fault와 context가 동시에 켜지면 최종 라벨은 fault로 두고, context는 보조 태그로 남긴다.

## Q. 발표할 때 쓰면 좋은 한 문장

이 프로젝트를 가장 쉽게 설명하면 다음이다.

> M1은 4분류 모델이 아니라, 장애 위험을 먼저 잡고 작업/활동 맥락을 덧붙이는 계층형 운영 판단 정책이다.

조금 더 길게 말하면:

> fault는 사전 위험 탐지 gate로 사용하고, task는 정비/작업 발생 후 맥락 분류로 사용하며, activity는 결측/overlap 민감성이 확인되어 보조 신호로만 사용한다.

## R. 절대 쓰면 안 되는 표현

아래 표현은 피해야 한다.

- `task를 사전에 예측했다`
- `activity 예측에 성공했다`
- `4분류 모델을 최종 완성했다`
- `최고 성능 모델로 fault gate를 교체했다`

대신 이렇게 말해야 한다.

- `task는 post-event context classifier로 정리했다`
- `activity는 overlap/missingness-sensitive candidate로 보류했다`
- `M1은 hierarchical operational decision policy로 정리했다`
- `fault gate는 기존 21번 기준 모델을 유지한다`

## S. 서비스 관점에서 어떻게 보이나

서비스 화면이나 Agent 입력으로 바꾸면 이벤트마다 아래 정보가 붙는 구조가 좋다.

| 필드 | 의미 |
| --- | --- |
| `fault_probability` | 장애 위험 점수 |
| `fault_pred` | 장애 gate 통과 여부 |
| `task_context_probability` | 작업/정비 맥락 점수 |
| `activity_candidate_probability` | activity 보조 신호 점수 |
| `final_operational_label` | 최종 운영 라벨 |
| `supporting_context_tags` | 보조 맥락 태그 |
| `review_required` | 사람이 확인해야 하는지 |

이렇게 하면 모델이 단순히 "정답 하나"를 내는 것이 아니라, 운영자가 판단할 수 있는 구조화된 입력을 제공한다.

## T. Review Required가 중요한 이유

24번 정책에서 `review_required`는 57건이었다.

검토가 필요한 경우는 다음이다.

- fault probability가 threshold 근처인 경우
- fault/task/activity 신호가 충돌하는 경우
- activity가 positive지만 missingness-sensitive인 경우

이 필드는 약점이 아니라 장점이다. 모델이 확신하기 어려운 케이스를 숨기지 않고 운영자에게 넘기는 장치다.

## U. 현재 모델의 장점

현재 M1 구조의 장점은 세 가지다.

1. **해석 가능하다.** 왜 fault인지, 왜 context인지, 왜 review인지 분리해서 설명할 수 있다.
2. **운영 기준이 있다.** recall만 보지 않고 normal FPR 제약을 둔다.
3. **라벨 의미를 존중한다.** task/activity를 억지로 예측 대상으로 만들지 않는다.

## V. 현재 모델의 한계

한계도 명확하다.

1. **샘플 수가 작다.** fault 기준 90건, normal 35건, fault 55건이다.
2. **activity는 결측 패턴 의존성이 크다.**
3. **threshold 안정성은 더 봐야 한다.**
4. **정상 오탐 20%도 실제 운영에서는 부담일 수 있다.**
5. **기계실/기간이 늘어나면 결과가 바뀔 수 있다.**

## W. 다음에 해야 할 일

다음 단계는 모델을 무작정 더 복잡하게 만드는 것이 아니다.

추천 순서는 다음이다.

1. **fault gate threshold 운영 검토**
   - `0.45 / 0.50 / 0.55 / 0.60`에서 알람 수와 미탐 수를 운영 관점으로 비교한다.

2. **activity relabeling 또는 missingness audit**
   - activity가 진짜 물리적 활동인지, 데이터 수집 상태인지 분리해야 한다.

3. **task는 context 전용 feature/story로 정리**
   - 예측 모델 성능 개선 대상이 아니라 운영 설명 레이어로 유지한다.

4. **Agent 입력 schema 설계**
   - `fault_probability`, `context_tags`, `review_required`, `policy_reason`을 Agent가 읽기 좋은 형태로 정리한다.

5. **운영자 피드백 루프 추가**
   - FP 7건, FN 6건을 사람이 보면 threshold와 feature 해석을 더 현실적으로 조정할 수 있다.

## X. 최종 의사결정표

| 항목 | 최종 결정 | 이유 |
| --- | --- | --- |
| fault | 기존 predictive gate 유지 | recall 0.8909, FPR 0.2000으로 운영 제약 충족 |
| task | post-event context classifier | post window는 통과하지만 사전 예측 근거 약함 |
| activity | 보조 신호 | missingness-only가 1.0000이라 예측 lock 불가 |
| 4분류 모델 | 보류 | 라벨 의미가 서로 달라 단일 분류가 부적절 |
| hierarchical policy | 채택 | 위험 판단과 맥락 설명을 분리할 수 있음 |
| 25번 best model 교체 | 하지 않음 | recall은 올랐지만 FPR 0.2857로 운영 기준 초과 |

## Y. 한 페이지 요약

M1의 핵심은 `fault`를 먼저 잡는 것이다. 현재 기준 모델은 장애 55건 중 49건을 잡고, 정상 35건 중 7건을 잘못 울린다. 이 정도는 M1에서 운영 후보로 쓸 수 있다.

`task`와 `activity`는 같은 방식으로 보면 안 된다. `task`는 사후 정비/작업 맥락이고, `activity`는 예측 후보처럼 보였지만 결측 패턴 의존성이 너무 강하다. 그래서 둘은 fault처럼 predictive target으로 잠그지 않는다.

25번에서 더 많은 모델을 돌려봤지만, 새 후보는 장애를 더 잡는 대신 정상 오탐을 너무 많이 늘렸다. 따라서 최종적으로는 기존 fault gate를 유지하고, 24번에서 설계한 계층형 정책을 M1의 설명 구조로 채택한다.

## Z. 최종 결론

최종 결론은 다음 한 줄이다.

```text
M1 = fault predictive gate + task context classifier + activity candidate signal 기반의 hierarchical operational decision policy
```

그리고 현재 확정 운영 문장은 다음이다.

```text
fault gate는 기존 21번 모델을 유지한다.
task는 사후 맥락 분류로 사용한다.
activity는 예측 성공으로 말하지 않고 보조 신호로만 사용한다.
최종 서비스/Agent 설명은 4분류 모델이 아니라 계층형 운영 판단 정책으로 정리한다.
```

