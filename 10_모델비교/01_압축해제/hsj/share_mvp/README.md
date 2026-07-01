# 지역난방 운영 보조 AIoT Agent

PreDist 데이터셋을 활용하여 지역난방 설비의 이상 징후를 조기에 탐지하고, 운영자가 이해할 수 있는 형태로 모델 결과를 요약하는 AIoT 운영 보조 Agent MVP 프로젝트입니다.

이 프로젝트는 단순히 고장 여부를 분류하는 모델을 만드는 것이 아니라, 운영 데이터 수집부터 전처리, 라벨 정렬, 윈도우 기반 Feature Engineering, 모델 비교, Lead Time 평가, LLM Agent 입력 구조 설계까지 이어지는 End-to-End 파이프라인을 구축하는 것을 목표로 합니다.

## 1. 프로젝트 소개

### 프로젝트명

지역난방 운영 보조 AIoT Agent

### 프로젝트 개요

지역난방 설비의 시계열 운영 데이터와 고장 라벨 정보를 이용해 고장 이전 위험 신호를 탐지하고, 최종적으로 운영자가 이해할 수 있는 알림 메시지와 점검 권고 구조를 생성합니다.

### 프로젝트 배경

지역난방 설비는 온도, 유량, 열량, 밸브, 저장조 등 다양한 센서 신호가 복합적으로 변화합니다. 고장이 발생한 뒤 대응하는 방식보다, 고장 전 이상 징후를 조기에 포착해 운영자가 선제적으로 점검할 수 있는 구조가 중요합니다.

이 프로젝트는 연구/발표용 MVP로, 약 1개월 내 구현 가능한 수준에서 재현 가능한 머신러닝 파이프라인과 운영 보조 Agent 구조를 제안합니다.

### 프로젝트 목표

- 운영 데이터부터 Agent 결과까지 이어지는 재현 가능한 AIoT 파이프라인 구축
- Event-aware Split을 적용하여 Event Leakage 방지
- RandomForest, Isolation Forest, LightGBM 모델 비교
- Lead Time 기반 고장 전 조기 탐지 성능 평가
- LLM을 예측 모델이 아닌 운영 결과 해석 Agent로 설계

## 2. 시스템 아키텍처

전체 흐름은 다음과 같습니다.

```text
운영 데이터
  ↓
전처리
  ↓
라벨 정렬
  ↓
Window Dataset
  ↓
Feature Engineering
  ↓
Training Dataset
  ↓
Event-aware Split
  ↓
RandomForest Baseline
  ↓
Isolation Forest
  ↓
LightGBM
  ↓
Model Evaluation
  ↓
LLM Agent
```

Pipeline 관점에서는 다음 역할로 나뉩니다.

```text
data/raw
  └─ 원본 PreDist 데이터

src/preprocessing.py
  └─ 운영 데이터 표준화

src/labeling.py
  └─ 고장 라벨 구간 정렬

src/windowing.py
  └─ 시계열 윈도우 생성

src/features.py
  └─ 윈도우 단위 Feature 생성

src/training_dataset.py, src/splitting.py
  └─ 학습 데이터셋 생성 및 Event-aware Split

src/baseline.py, src/isolation_forest.py, src/lightgbm_model.py
  └─ 모델 학습 및 예측 결과 생성

src/evaluation.py
  └─ 모델 비교 및 Lead Time 평가

src/agent.py
  └─ LLM Agent 입력/출력 구조 생성
```

## 3. 프로젝트 디렉터리 구조

```text
project3.0_data/
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── docs/
│   ├── development_principles.md
│   ├── decision_log.md
│   ├── experiment_log.md
│   ├── feature_log.md
│   └── model_log.md
├── notebooks/
│   ├── 01_data_structure_check.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_label_alignment.ipynb
│   ├── 04_window_dataset.ipynb
│   ├── 05_feature_engineering.ipynb
│   ├── 06_training_dataset_builder.ipynb
│   ├── 06_train_valid_test_split.ipynb
│   ├── 07_baseline_model.ipynb
│   ├── 08_isolation_forest.ipynb
│   ├── 09_lightgbm_model.ipynb
│   ├── 10_model_evaluation.ipynb
│   └── 11_llm_agent.ipynb
├── outputs/
│   ├── models/
│   ├── figures/
│   └── reports/
├── src/
│   ├── agent.py
│   ├── baseline.py
│   ├── config.py
│   ├── evaluation.py
│   ├── features.py
│   ├── isolation_forest.py
│   ├── labeling.py
│   ├── lightgbm_model.py
│   ├── preprocessing.py
│   ├── splitting.py
│   ├── training_dataset.py
│   ├── validation.py
│   └── windowing.py
├── README.md
├── pyproject.toml
└── uv.lock
```

## 4. Notebook 실행 순서

```text
01_data_structure_check.ipynb
↓
02_preprocessing.ipynb
↓
03_label_alignment.ipynb
↓
04_window_dataset.ipynb
↓
05_feature_engineering.ipynb
↓
06_training_dataset_builder.ipynb
↓
06_train_valid_test_split.ipynb
↓
07_baseline_model.ipynb
↓
08_isolation_forest.ipynb
↓
09_lightgbm_model.ipynb
↓
10_model_evaluation.ipynb
↓
11_llm_agent.ipynb
```

| 순서 | Notebook | 역할 |
|---:|---|---|
| 01 | `01_data_structure_check.ipynb` | 원본 데이터 파일 목록, 컬럼 구조, 시간 컬럼, 설비 ID, 결측률, 라벨 구조를 확인합니다. |
| 02 | `02_preprocessing.ipynb` | 운영 데이터 로딩, 제조사/설비 ID 추출, datetime 표준화, 숫자형 센서 변환, 결측/중복 확인을 수행합니다. |
| 03 | `03_label_alignment.ipynb` | 고장 신고 시점 기준으로 `pre_fault`, `uncertain`, `normal_candidate` 라벨 구간을 정렬합니다. |
| 04 | `04_window_dataset.ipynb` | 60분 window, 10분 stride 기준으로 윈도우 단위 데이터셋과 라벨을 생성합니다. |
| 05 | `05_feature_engineering.ipynb` | 윈도우별 평균, 표준편차, 최소/최대, delta, missing rate, slope feature를 생성합니다. |
| 06 | `06_training_dataset_builder.ipynb` | 실제 라벨 구간과 겹치는 운영 데이터를 이용해 학습 가능한 확장 training dataset을 생성합니다. |
| 06 | `06_train_valid_test_split.ipynb` | 시간 기준 split과 event-aware split을 수행하고, event leakage를 제거한 최종 split 파일을 생성합니다. |
| 07 | `07_baseline_model.ipynb` | DummyClassifier와 RandomForest Baseline을 학습하고 평가합니다. |
| 08 | `08_isolation_forest.ipynb` | 정상 데이터만으로 Isolation Forest를 학습해 비지도 이상 탐지 결과를 생성합니다. |
| 09 | `09_lightgbm_model.ipynb` | LightGBM 이진 분류 모델을 학습하고 threshold별 예측 결과를 저장합니다. |
| 10 | `10_model_evaluation.ipynb` | RandomForest, Isolation Forest, LightGBM을 종합 비교하고 Lead Time 평가를 수행합니다. |
| 11 | `11_llm_agent.ipynb` | LightGBM 결과와 Isolation Forest 보조 신호를 이용해 LLM Agent 입력/출력 JSON 구조를 생성합니다. |

## 5. 사용 기술

- Python
- Pandas
- NumPy
- Scikit-learn
- LightGBM
- Jupyter Notebook
- OpenAI API (Agent 설계)
- uv
- Git
- VS Code

## 6. 모델 구성

| 단계 | 모델 | 목적 |
|---|---|---|
| 07 | RandomForest | 지도학습 Baseline 모델 |
| 08 | Isolation Forest | 정상 패턴 기반 비지도 이상 탐지 |
| 09 | LightGBM | 최종 위험 예측 후보 모델 |
| 11 | OpenAI LLM | 운영자 브리핑 및 점검 권고 구조 설계 |

라벨 정책은 다음과 같습니다.

| 원본 라벨 | 이진 라벨 | 의미 |
|---|---:|---|
| `normal_candidate` | 0 | 정상 후보 |
| `pre_fault` | 1 | 고장 전 위험 구간 |
| `fault` | 1 | 고장 구간 |
| `disturbance_marker` | 1 | 외란 또는 위험 이벤트 |
| `uncertain` | 제외 | 고장 직전 불확실 구간 |
| `unlabeled` | 제외 | 정상으로 단정하지 않는 미라벨 구간 |

## 7. 프로젝트 결과

최종 운영 MVP 모델은 **LightGBM**으로 선정했습니다.

### 모델별 해석

RandomForest는 위험 구간 Recall과 `pre_fault` Recall이 가장 높았습니다. 하지만 False Positive가 많아 실제 운영 환경에서는 알람 피로도가 커질 수 있습니다.

Isolation Forest는 정상 패턴 기반 이상 탐지 모델로 False Positive가 가장 적었습니다. 하지만 위험 구간 Recall과 `pre_fault` Recall이 낮아 단독 운영 모델로 사용하기에는 탐지 누락 가능성이 큽니다.

LightGBM은 RandomForest보다 False Positive를 줄이면서도 Isolation Forest보다 높은 위험 탐지 성능을 보였습니다. Precision, Recall, False Positive 사이 균형이 가장 좋아 최종 운영 MVP 모델로 선정했습니다.

### Test 기준 모델 비교

| 모델 | Precision | Recall | F1 | pre_fault Recall | False Positive | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|
| RandomForest | 0.8760 | 0.9717 | 0.9214 | 0.9883 | 175 | 0.9536 |
| Isolation Forest | 0.9287 | 0.6447 | 0.7610 | 0.8033 | 63 | 0.9338 |
| LightGBM | 0.9163 | 0.8090 | 0.8593 | 0.8759 | 94 | 0.9402 |

### Lead Time 평가 결과

Lead Time은 동일 event에서 fault 발생 시각 이전 최초 위험 탐지 시각까지의 시간으로 계산했습니다.

| 모델 | 탐지 이벤트 수 / 전체 이벤트 수 | 평균 Lead Time | 중앙값 Lead Time |
|---|---:|---:|---:|
| RandomForest | 9 / 11 | 1416.7분 | 1440.0분 |
| Isolation Forest | 7 / 11 | 1440.0분 | 1440.0분 |
| LightGBM | 8 / 11 | 1440.0분 | 1440.0분 |

LightGBM threshold는 `0.5`를 권장합니다. `0.3`, `0.4`는 `pre_fault` Recall은 높지만 False Positive가 과도하고, `0.6`은 위험 탐지를 거의 수행하지 못했습니다.

## 8. 프로젝트 특징

- Event-aware Train/Test Split 적용으로 Event Leakage 방지
- Lead Time 기반 조기 탐지 성능 평가 수행
- Threshold Analysis로 운영 threshold 선택 근거 확보
- Isolation Forest와 LightGBM을 결합한 위험 신호 해석 구조 설계
- LLM은 예측하지 않고 ML 모델 결과를 조회·해석·요약·권고
- 재현 가능한 AIoT 운영 파이프라인 구축
- 각 단계별 Summary Report를 `outputs/reports/`에 저장

## 9. 향후 개선 방향

- FastAPI 기반 실시간 추론 서버 구축
- PostgreSQL 또는 SQLite 기반 Agent 결과 저장소 연동
- 실시간 데이터 수집 파이프라인 구축
- OpenAI API 기반 실시간 운영 Agent 구현
- Streamlit 또는 React 기반 운영 Dashboard 구축
- 운영 로그와 조치 이력 기반 지속 학습 구조 도입
- SHAP 기반 개별 예측 설명 추가
- 설비별 정상 운전 범위와 운영 규칙 기반 추천 고도화

## 실행 방법

이 프로젝트는 `uv` 기반 Python 프로젝트입니다.

```bash
uv sync
```

Notebook은 `notebooks/` 디렉터리에서 순서대로 실행합니다. 원본 데이터는 `data/raw/`에 보관하며, 원본 파일은 수정하지 않습니다.

```bash
uv run jupyter notebook
```

주요 결과물은 다음 위치에 저장됩니다.

```text
data/processed/
  ├── train_dataset_event_split.csv
  ├── validation_dataset_event_split.csv
  ├── test_dataset_event_split.csv
  ├── 09_lightgbm_test_results.csv
  └── agent_outputs_sample.json

outputs/models/
  ├── 07_random_forest_baseline.joblib
  ├── 08_isolation_forest.joblib
  └── 09_lightgbm_model.joblib

outputs/reports/
  ├── 07_baseline_summary.md
  ├── 08_isolation_forest_summary.md
  ├── 09_lightgbm_summary.md
  ├── 10_model_evaluation_summary.md
  └── 11_agent_summary.md
```

## 프로젝트 핵심 성과

- 운영 데이터부터 AI Agent까지 이어지는 End-to-End AIoT 파이프라인 구축
- Event-aware Split을 적용하여 데이터 누수(Event Leakage) 방지
- RandomForest, Isolation Forest, LightGBM을 비교하여 최적 모델 선정
- Lead Time 기반 조기 탐지 성능 평가 수행
- LLM을 예측 모델이 아닌 운영 보조 Agent로 설계하여 실제 산업 환경을 고려한 AI 시스템 구현
