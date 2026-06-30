
# 0. 작업 시작 전 확인 절차
코드 작성 전 반드시 다음 문서를 먼저 확인한다.

1. 최종 3주제 HTML 문서
2. 각 프로젝트 폴더의 docs/guide 내부 md 파일
3. README.md
4. 기존 코드 구조
5. pyproject.toml 의존성
6. .env.example 환경변수 구조

위 문서를 확인하지 않고 임의로 구조를 만들거나 새 기술을 추가하지 않는다.

# 1. Rules

본 프로젝트는 단순한 AIoT Agent 구현이 아니라, 
기존 서비스를 벤치마킹하고 차별점을 반영한 서비스형 프로젝트를 목표로 한다.

프로젝트 규모는 개인 프로젝트처럼 너무 작아 보이지 않도록 설계하되, 
3~4주 단위로 구현 가능한 현실적인 범위를 유지한다.

개발은 다음 단계로 확장한다.

1. Prototype: 핵심 기능 검증
2. Alpha: 주요 기능 통합
3. Beta: 서비스화 수준 개선

## 0. 프로젝트 폴더 구조  Rule

기본 폴더 구조는 다음을 따른다.

project/
├─ README.md
├─ pyproject.toml
├─ .env.example
├─ .gitignore
├─ docs/
│  └─ guide/
│  └─ report/
├─ data/
│  ├─ raw/
│  ├─ processed/
│  └─ external/
├─ notebooks/
├─ src/
│  ├─ api/
│  ├─ agents/
│  ├─ config/
│  ├─ data/
│  ├─ db/
│  ├─ models/
│  ├─ services/
│  └─ utils/
├─ frontend/
├─ tests/
└─ scripts/

	- 새 파일을 만들기 전 기존 폴더 구조를 먼저 확인한다.
	- 기능별 책임에 맞는 폴더에 파일을 생성한다.
	- 임시 파일은 루트 디렉토리에 만들지 않는다.
	- 테스트용 파일은 tests 또는 scripts에 작성한다.

---

## 1. 개발환경
	- python 버전은 3.12를 사용한다.
	- Python 패키지 관리는 uv를 사용한다.
	- 가상환경은 uv 기반으로 생성하고 관리한다.
	- 라이브러리 설치는 pip install이 아니라 uv add를 사용한다.
	- 프로젝트별 pyproject.toml을 기준으로 의존성을 관리한다.
	- gpu cuda 쓰는데 버전은 Pytorch랑 맞춰야 한다.

---

## 2-1. 코드 작성 Rule
	- 한 함수는 하나의 기능만 담당하도록 작성한다.
	- 함수 길이는 가능하면 50줄 이하로 유지한다.
	- 중복 코드는 utils, services, common 모듈로 분리한다.
	- 설정값은 코드에 직접 쓰지 않고 config 또는 .env로 분리한다.
	- 기능 단위로 주석을 작성한다.
	- 주석은 한국어로 작성한다.
	- 불필요한 주석은 작성하지 않는다.
	- 변수명과 함수명은 의미가 드러나도록 작성한다.

## 2-2. 코드 품질 Rule
	- 코드 포맷팅은 ruff 또는 black 중 하나로 통일한다.
	- import 정리는 ruff를 사용한다.
	- 타입 힌트를 가능한 작성한다.
	- 핵심 함수에는 입력값과 반환값 타입을 명시한다.
	- 에러는 무시하지 않고 명시적으로 처리한다.
	- print 디버깅은 최종 코드에서 제거하고 logging을 사용한다.

---

## 3. 데이터 처리 Rule
	데이터 작업은 다음 순서로 진행한다.

	- 1. 데이터 불러오기
	- 2. 데이터 구조 확인
	- 3. 결측치 확인
	- 4. 이상치 확인
	- 5. 중복값 확인
	- 6. 전처리
	- 7. EDA
	- 8. 모델 입력 데이터 생성
	- 원본 데이터는 data/raw에 저장하고 수정하지 않는다.
	- 전처리 결과는 data/processed에 저장한다.
	- 외부에서 가져온 데이터는 data/external에 저장한다.
	- 데이터 출처와 수집 기준을 문서화한다.
	- 전처리 기준은 notebook과 md 문서에 함께 기록한다.

### 1. Notebook 작성 규칙
=====================
# 1. 데이터 불러오기
## 1.1 라이브러리 import
## 1.2 데이터 경로 설정
## 1.3 데이터 로드
# 2. 데이터 기본 확인
## 2.1 데이터 크기 확인
## 2.2 컬럼 타입 확인
## 2.3 결측치 확인
# 3. 전처리 (어떤 방법으로 어떻게 전처리 하는지 기술)
# 4. EDA
=====================

---

## 4. Model Rule
	- 모델 코드는 notebooks에서 실험 후 src/models 또는 src/services로 분리한다.
	- 모델 학습과 추론 코드는 분리한다.
	- 모델 입력 데이터 생성 과정은 문서화한다.
	- baseline 모델을 먼저 작성한 뒤 개선 모델을 적용한다.
	- 평가 지표를 명확히 기록한다.
	- 모델 파일은 용량이 크면 git에 올리지 않는다.

---

## 5. Backend Rule
	- 기본 서버는 FastAPI를 사용한다.
	- API 라우터는 기능별로 분리한다.
	- 비즈니스 로직은 router에 직접 작성하지 않고 service로 분리한다.
	- DB 접근 로직은 repository 또는 db 모듈로 분리한다.
	- Request / Response 구조는 schema로 분리한다.
	- API 응답 형식은 최대한 통일한다.

### Logging Rule

- print 대신 logging을 사용한다.
- API 요청, DB 저장, Agent 실행, 모델 예측, 에러 발생 시 로그를 남긴다.
- 로그 메시지는 한국어로 작성하되, 에러 원인은 원문을 함께 남긴다.
- 민감 정보는 로그에 남기지 않는다.

### API 응답 형식 Rule

API 응답은 가능한 다음 형식을 따른다.

성공 응답:
{
  "success": true,
  "message": "요청이 성공했습니다.",
  "data": {}
}

실패 응답:
{
  "success": false,
  "message": "요청 처리 중 오류가 발생했습니다.",
  "error": "error_detail"
}
	
---

## 6. DB Rule
	- DB는 SQL / MySQL / PostgreSQL / TimescaleDB 중 프로젝트 목적에 맞게 사용한다.
	- 시계열 데이터가 중심이면 PostgreSQL 또는 TimescaleDB를 우선 고려한다.
	- DB 연결 정보는 .env로 관리한다.
	- 테이블 생성 SQL 또는 ORM 모델을 문서화한다.
	- 원본 로그성 데이터와 가공 데이터는 분리한다.
	- created_at, updated_at 컬럼을 가능한 포함한다.

---

## 7. Agent Rule
	- Agent 구성에는 LangChain과 LangGraph를 사용한다.
	- Agent 흐름은 node 단위로 분리한다.
	- 각 node는 하나의 역할만 담당한다.
	- Agent 상태는 State 객체로 관리한다.
	- LLM 호출, DB 조회, RAG 검색, 모델 예측 기능은 tool 또는 service로 분리한다.
	- Agent 실패 시 fallback 응답을 제공한다.
	- Agent 실행 로그를 남긴다.

---

## 8. RAG / 지식그래프 코드 Rule
	- RAG 기능은 문서 로드, chunking, embedding, retrieval, generation 단계로 분리한다.
	- 벡터 DB는 프로젝트 상황에 맞게 선택한다.
	- 검색 결과에는 가능한 출처 정보를 포함한다.
	- 지식그래프를 사용하는 경우 Entity와 Relation을 명확히 정의한다.
	- RAG와 Agent는 직접 결합하지 않고 service 또는 tool을 통해 연결한다.

---

## 9. Frontend Rule
	- 기본 화면은 HTML로 작성한다.
	- 확장 시 React / Vite / TypeScript 사용을 고려한다.
	- 컴포넌트는 기능 단위로 분리한다.
	- API 호출 코드는 별도 파일로 분리한다.
	- 화면 상태, 로딩 상태, 에러 상태를 구분한다.

--- 

## 10. 환경변수 Rule
	- API Key, DB URL, 비밀번호는 코드에 직접 작성하지 않는다.
	- .env 파일을 사용한다.
	- .env 파일은 git에 올리지 않는다.
	- .env.example 파일을 제공한다.
	- 환경변수 이름은 대문자와 언더스코어를 사용한다.

---

## 11. 실행 명령어 Rule
### 가상환경 생성
uv venv
### 패키지 설치
uv sync
### 패키지 추가
uv add 패키지명
### 서버 실행
uv run uvicorn src.api.main:app --reload
### 테스트 실행
uv run pytest
### 노트북 실행
uv run jupyter lab

---

## 12. Git 규칙
	- main 브랜치에는 안정된 코드만 둔다.
	- 기능 개발은 feature 브랜치에서 진행한다.
	- 커밋 메시지는 작업 내용을 명확히 작성한다.
	- 대용량 데이터, 모델 파일, .env는 git에 올리지 않는다.
	- 실험 결과 파일은 필요한 경우만 선별해서 저장한다.
===================
커밋 예시
feat: 센서 데이터 저장 API 추가
fix: 결측치 처리 로직 수정
docs: 프로젝트 실행 방법 추가
refactor: agent node 구조 분리
test: DB 연결 테스트 추가
====================

---

## 13. 테스트 Rule
	- 테스트는 pytest를 사용한다.
	- 핵심 로직은 tests 폴더에 테스트 코드를 작성한다.
	- API는 FastAPI TestClient 또는 httpx로 테스트한다.
	- DB 연결 테스트를 작성한다.
	- Agent는 node 단위로 최소 동작 테스트를 작성한다.
	- 모델은 입력 shape과 출력 shape을 테스트한다.

---

## 14. 금지 Rule
	- pip install 사용 금지
	- 코드에 API Key 직접 작성 금지
	- 루트 디렉토리에 임시 테스트 파일 생성 금지
	- router 안에 비즈니스 로직 직접 작성 금지
	- 데이터 원본 파일 직접 수정 금지
	- .env, 대용량 데이터, 모델 파일 git 업로드 금지
	- 하나의 파일에 여러 책임을 몰아넣는 구조 금지
	- 사용하지 않는 라이브러리 추가 금지


