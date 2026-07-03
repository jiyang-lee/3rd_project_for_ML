# HeatGrid 신운영서비스

`HeatGridAgent_LLM_Agent_Architecture_Report.html`의 운영 에이전트 비전을 실행 가능한 서비스로 옮긴 신규 구현이다. 데이터와 모델 입력은 `05_데이터셋`, `12_최종모델`, `13_서브데이터셋`만 사용하며, 부트스트랩 이후 런타임은 이 폴더의 `artifacts/`와 `data/replay/`만 읽는다.

## 빠른 실행

```bash
cd 11_신운영서비스/backend
uv sync
uv run python ../setup/bootstrap.py
docker compose -f ../docker-compose.yml up -d db
uv run uvicorn heatgrid_ops.api.app:app --host 0.0.0.0 --port 8000
```

프론트엔드:

```bash
cd 11_신운영서비스/frontend
npm install
npm run build
npm run dev
```

## 핵심 계약

- 공식 우선순위는 handoff ZIP의 `priority_score`를 그대로 사용한다. 원본 계약은 `0.65 * current_best + 0.35 * m1_specialist`이다.
- OpenAI 키가 없거나 일일 토큰 예산을 초과하면 템플릿으로 응답한다.
- RAG 문서는 `13_서브데이터셋`의 HTML/PDF에서만 수집한다.
- `11_운영서비스`, `07_데이터산출물`, `08_모델산출물`을 신규 런타임 경로로 참조하지 않는다.

## 검증

```bash
cd 11_신운영서비스/backend
uv run pytest ../tests -q
uv run python ../setup/bootstrap.py
uv run python -m compileall -q heatgrid_ops ../setup
uv run python -m heatgrid_ops.rag.ingest --dry-run
```

프론트엔드:

```bash
cd 11_신운영서비스/frontend
npm run build
npm audit --audit-level=moderate
```

컨테이너:

```bash
cd 11_신운영서비스
docker compose config --quiet
docker compose up -d db
docker compose exec -T db psql -U heatgrid -d heatgrid -c "select count(*) from information_schema.tables where table_schema='public' and table_type='BASE TABLE';"
docker compose down
```
