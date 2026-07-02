# 11_운영서비스 — HeatGrid 엔드투엔드 운영형 서비스

PreDist 리플레이 시뮬레이션 → TimescaleDB 수집 → compact13 피처 → gate 모델 추론 → 상태카드 →
LangGraph 에이전트(출동지시서) → React 대시보드까지의 전체 파이프라인 데모.

기존 연구 산출물(`08_모델산출물` joblib 4개, runtime policy, priority 정책 CSV)을 재학습 없이 그대로 서빙한다.

## 아키텍처

```
replay/publisher.py ──POST /api/ingest/readings──▶ FastAPI ──▶ TimescaleDB (sensor_readings 하이퍼테이블)
    (가상시계 가속 재생)                              │
                                                    ▼ scheduler.py (asyncio, 가상 6시간 stride)
                                       7일 window → compact13 피처 → fault/task/activity gate 병렬
                                          → conflict resolver → pre-event(0.6) → priority 정책
                                                    │
                                                    ▼ state_cards 테이블 + WebSocket 브로드캐스트
                                       pre-event/review 카드 발생 시 LangGraph 에이전트 트리거
                                       observe → analyze → prioritize → dispatch → record
                                                    │
                                                    ▼ dispatch_orders (한국어 작업지시서 초안)
frontend (Vite+React+TS) ◀──REST + /ws────── FastAPI
```

## 실행 방법 (Windows)

전제: Docker Desktop 실행 중, Node 20+, uv 설치됨.

```powershell
# 0. 의존성 (repo 루트에서)
cd C:\3rd_Project\HeatGridAgent
uv sync --group service

# 1. DB
cd 11_운영서비스
docker compose up -d
# 확인: docker exec heatgrid-tsdb psql -U heatgrid -d heatgrid -c "\dt"

# 2. 환경설정 + 데이터 추출 (1회)
copy .env.example .env          # OPENAI_API_KEY는 선택 (없으면 템플릿 폴백)
cd ..
.venv\Scripts\python.exe -m heatgrid_service.replay.extract --app-dir 지정 불필요 — 아래처럼 실행:
$env:PYTHONPATH="11_운영서비스\backend"; .venv\Scripts\python.exe -m heatgrid_service.replay.extract
# 시나리오 참고: ... -m heatgrid_service.replay.extract --list-scenarios

# 3. 백엔드 (터미널 A)
.venv\Scripts\python.exe -m uvicorn heatgrid_service.api.app:app --app-dir 11_운영서비스/backend --port 8000

# 4. 리플레이 publisher (터미널 B)
$env:PYTHONPATH="11_운영서비스\backend"; .venv\Scripts\python.exe -m heatgrid_service.replay.publisher

# 5. 프론트엔드 (터미널 C)
cd 11_운영서비스\frontend
npm install
npm run dev                     # http://localhost:5173
```

## 구성 요소

| 경로 | 역할 |
|---|---|
| `db/init/01_schema.sql` | substations, sensor_readings(하이퍼테이블), state_cards, dispatch_orders, agent_runs, replay_state |
| `backend/heatgrid_service/features.py` | run_36 compact13 피처 함수 verbatim 포팅 (골든 테스트로 패리티 보증) |
| `backend/heatgrid_service/models_registry.py` | joblib 4개 로드, `m1_full_gate_runtime_policy_metadata.json`이 피처 순서/threshold의 source of truth |
| `backend/heatgrid_service/pipeline/` | conflict resolver(run_33), priority 정책(run_28), 상태카드 빌더(run_39 스키마) |
| `backend/heatgrid_service/scheduler.py` | 가상시계 기준 추론 루프 |
| `backend/heatgrid_service/agent/` | LangGraph observe→analyze→prioritize→dispatch→record (OpenAI, 키 없으면 템플릿 폴백) |
| `backend/heatgrid_service/replay/` | zip 추출 CLI + 가속 리플레이 publisher |
| `frontend/` | 기계실 그리드, 상태카드 상세, risk 차트, 우선순위 보드, 출동지시 피드, 에이전트 trace |

## 정직성 원칙 (연구 저장소의 검증 규율 유지)

- **fault_group은 모델 예측이 아니다** — 리플레이 시나리오의 faults.csv 메타데이터 조인이며 UI에 명시된다.
- 모든 상태카드의 `validation_level`은 `replay_simulation`이다. 이 서비스는 데모/아키텍처 검증용이며,
  README 루트의 "현재 한계"(M2 pre-event 외부검증 실패, 33건 소표본)는 그대로 유효하다.
- priority score는 ML이 아니라 정책 점수(`100*(0.55r+0.30u+0.15g)`)다.

## 테스트

```powershell
.venv\Scripts\python.exe -m pytest 11_운영서비스/tests -q
```

- `test_feature_parity.py` — 골든 패리티: 기존 standard_feature_pool.csv 대비 compact13 재계산 일치
- `test_conflict_resolver.py` — run_33 resolve() 케이스 테이블
- `test_priority_policy.py` — 기존 m1_fault_dispatch_priority_v1.csv 행 재계산 일치
