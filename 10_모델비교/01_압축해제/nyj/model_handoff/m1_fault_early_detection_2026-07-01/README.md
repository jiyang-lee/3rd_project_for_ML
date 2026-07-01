# M1 지역난방 고장 조기탐지 — Handoff 패키지

이 폴더는 **manufacturer 1(M1) 지역난방 설비 고장 조기탐지** 프로젝트의 최종 산출물만 모은 전달 패키지다.
다음 단계(Agent/서비스/리뷰)에서 바로 추론·재현·검토할 수 있게 **최종 모델·결과·메타데이터·보고서**를 담았다.

> ⚠️ 이 프로젝트는 **manufacturer 1 전용**이다. manufacturer 2 데이터는 사용하지 않는다.
> ⚠️ 최종 채택 모델(설비별 하이브리드)의 성능 수치(0.679 @ 0.114)는 **nested CV 추정치**다.
> 배포 모델은 전체 데이터로 학습했으므로, 자기 학습 데이터로 재채점하면 낙관적으로 나온다. (§9)

원본 raw 센서 CSV, 대량 전처리 parquet, 실험 노트북은 제외했다.

## 1. 폴더 구조

```text
m1_fault_early_detection_2026-07-01/
├─ model/
│  ├─ hybrid_model.joblib            # ⭐ 최종 채택 모델 (설비별 LOF + 전역 NB 하이브리드)
│  ├─ hybrid_model_meta.json         # 최종 모델 메타(피처·운영점·라우팅·성능추정)
│  ├─ inference_example.py           # 최종 모델 로드+이벤트 채점 예제 (repo 불필요)
│  ├─ baseline_model.joblib          # 참고용 baseline (GradBoost) — 최종 채택 모델 아님
│  └─ baseline_model_meta.json       # baseline 피처 목록·운영점·CV 성능
├─ results/
│  ├─ validate_hybrid_frontier_dhw.csv   # ⭐ 최종 결과 (0.679 @ 0.114)
│  ├─ validate_hybrid_dhw.csv            # 하이브리드 vs NaiveBayes 비교
│  ├─ validate_persub_matched_dhw.csv    # 설비별 갈래 분해 (LOF 담당 14건)
│  ├─ validate_anomaly_persub_dhw.csv    # 설비별 이상탐지 단독 성적
│  └─ anomaly_on_original.csv            # 리치(115) vs lean(85) 피처 비교 근거
├─ docs/
│  ├─ 01_preprocessing_pipeline_review.md
│  ├─ 02_model_performance_review.md
│  ├─ 03_design_rationale.md
│  ├─ 04_easy_overview.md
│  ├─ 05_full_summary.md                 # 종합 정리(핵심 결론)
│  └─ 보고서_M1_고장조기탐지.md
├─ MANIFEST.json
└─ README.md
```

## 2. 전체 파이프라인 흐름

```text
원본 센서 CSV (M1, 10분 간격)
+ context: faults / normal_events / disturbances
→ cleaning (10분 격자 · 이상치방어 · 누적→증분)
→ 파생 (dev, dT, +DHW 파생)
→ window×통계 (6h window, 변수 17 × 통계 5 = 피처 85)
→ 라벨링 (pre_fault 전조구간, horizon 7일)
→ 설비별 LOF(비지도) + 전역 NaiveBayes(지도) 하이브리드 라우팅
→ 이벤트 판정 (K연속 window ≥ threshold → 고장)
→ 탐지율 / 오경보율 / 리드타임
```

## 3. 입력 데이터 기준

- **입력 원본:** `manufacturer 1/` (git 포함, 이 패키지엔 미포함)
  - operational sensor CSV (설비별, 10분 간격)
  - `faults.csv` — 고장 신고 이력 (efd_possible, Possible anomaly start/end 등)
  - `normal_events.csv` — 정상 기준 이벤트 (정상 오염 방지용)
  - `disturbances.csv` — 정비/작업 이력
- **공통 센서 13종 → 변수 17개 → 피처 85개** (변수 17 × 통계 5종: 평균·변동·최소·최대·추세)
- window 6시간, horizon 3/5/7일 비교 후 **7일 채택**, 최종 학습셋 `m1_windows_7d_dhw.parquet`
- 규모: 설비 35개 / 고장 학습 29건 / 정상 35건 / window 1,494장 (정상 980 · 전조 514)

주의: 이 패키지는 결과·메타·문서 묶음이다. raw data, 전처리 parquet, score 원본은 포함하지 않는다.
정확한 컬럼·전처리 정의는 `docs/01_preprocessing_pipeline_review.md`와 `docs/05_full_summary.md` §1~2를 기준으로 한다.

## 4. 최종 채택 모델 — 설비별 하이브리드

**설비별 자기기준 하이브리드**: `설비별 LOF(비지도)` + `전역 NaiveBayes(지도)` 라우팅.

| 지표 | 최종(하이브리드) | 기존 최고(NaiveBayes 단독) |
|---|---:|---:|
| **탐지율** | **0.679** (28건 중 19건) | 0.500 |
| **오경보율** | **0.114** (35건 중 4건) | 0.171 |

역할:
- 설비마다 **자기 정상 이력** 기준으로 이상 정도를 본다 (LOF). 자기 정상 이력이 있는 설비(14/28)를 담당.
- 자기 기준을 못 만드는 설비는 **전역 NaiveBayes**로 폴백.

핵심 돌파구 2가지:
- **① 온수(DHW) 센서 추가** — 탐지 0.25 → 0.50 (난방센서엔 안 보이던 온수 고장 포착).
- **② 설비별 자기기준 하이브리드** — 0.50 → 0.68 (설비마다 정상 baseline이 달라서 자기기준이 유효).

정직성:
- 모든 수치는 **설비단위 nested CV(안 본 데이터)** 값이다. 시간 누수·설비 누수 제거.
- 조합·부스팅·추가 피처 등 다른 시도는 엄격한 검증에서 **대부분 "가짜 향상"으로 판명**. (§성적표: `docs/05_full_summary.md` §3-2)

리드타임(조기탐지 여유): 조기 7건 / 임박 6건 / 미탐 15건, 최대 **6.2일** 전 탐지.

배포 모델 (`model/hybrid_model.joblib`):
- 위 하이브리드를 **전체 데이터로 학습**해 직렬화한 배포 아티팩트. 커스텀 클래스 없이 `joblib.load`만으로 로드된다.
- 구성: 전역 NaiveBayes(폴백) + 설비별 LOF 탐지기(covered 설비) + 라우팅 규칙 + 운영점(thr, K).
- 라우팅: `substation_id ∈ covered_substations → per-sub LOF`, 아니면 `→ 전역 NaiveBayes`.
- 채점 예제는 `model/inference_example.py` 참고 (한 이벤트의 window 표 → 0/1 판정).

## 5. 결과 파일 설명 (`results/`)

| 파일 | 내용 |
|---|---|
| `validate_hybrid_frontier_dhw.csv` | ⭐ **최종 결과** — 오경보 cap(0.05~0.20)별 정직한 test 프론티어. 운영점 0.679 @ 0.114 |
| `validate_hybrid_dhw.csv` | 하이브리드 vs NaiveBayes 단독 직접 비교 |
| `validate_persub_matched_dhw.csv` | 설비별 갈래 분해 — LOF 담당 14건 성적 (0.857 @ 0.057) |
| `validate_anomaly_persub_dhw.csv` | 설비별 이상탐지 단독 성적 (하이브리드 이전 단계) |
| `anomaly_on_original.csv` | 리치(115) vs lean(85) 피처 비교 — "피처는 많이가 아니라 알맞게"의 수치 근거 |

## 6. 참고 모델 — `model/baseline_model.joblib`

- 이 joblib은 **초기 baseline(GradBoost, 55피처)** 이며 **최종 채택 모델이 아니다**.
- 로드 가능한 유일한 직렬화 모델이라 재현/비교 기준선으로 포함한다.
- 운영점·CV 성능·피처 순서는 `model/baseline_model_meta.json` 참고 (탐지 0.214 @ 오경보 0.20 수준).
- 최종 채택 모델(설비별 하이브리드)은 아래 §9의 검증 스크립트로 재현한다.

## 7. 문서 안내 (`docs/`)

- `05_full_summary.md` — **종합 정리(핵심 결론)**. 데이터·전처리·모델을 한 장에 (이유+근거).
- `04_easy_overview.md` — 비전문가 설명용.
- `03_design_rationale.md` — 설계 근거 상세.
- `02_model_performance_review.md` — 모델별 성능 리뷰.
- `01_preprocessing_pipeline_review.md` — 전처리 파이프라인 상세.
- `보고서_M1_고장조기탐지.md` — 조기탐지 요약 보고서.

## 8. Python 로딩 예시 (최종 하이브리드 모델)

```python
from pathlib import Path
import joblib

ROOT = Path("m1_fault_early_detection_2026-07-01")

model = joblib.load(ROOT / "model" / "hybrid_model.joblib")   # dict (커스텀 클래스 불필요)
feat = model["feature_names"]                 # 입력 피처 순서 (85개)
covered = set(model["covered_substations"])   # per-sub 갈래를 쓰는 설비 목록

# 한 이벤트(설비의 window 표) 채점: model/inference_example.py 의 predict_event() 참고
#   covered 설비   → 설비별 LOF 백분위 점수, 운영점 model["persub_operating_point"]
#   uncovered 설비 → 전역 NaiveBayes 확률,   운영점 model["nb_operating_point"]
#   공통 규칙: longest_run(window_score >= thr) >= K → 고장(1)
```

바로 실행:

```bash
python model/inference_example.py     # 형식 데모 + 로드 확인 (numpy/pandas/scikit-learn 필요)
```

## 9. 최종 모델 사용 / 재학습 주의사항

- **성능 수치(0.679 @ 0.114)는 nested CV 추정치**다. `hybrid_model.joblib`은 전체 데이터로 학습했으므로
  자기 학습 데이터로 재채점하면 낙관적으로 나온다. 진짜 일반화 성능은 이 nested CV 값으로 인용한다.
- 입력 feature **순서**는 `model["feature_names"]`(=metadata `feature_names`)와 반드시 맞춘다.
- 이벤트 판정 규칙: **K연속 window가 threshold 초과 → 고장**. 운영점은 갈래별로 다르다
  (per-sub / nb 각각 `*_operating_point`).
- covered 목록에 없는 **새 설비**는 자동으로 전역 NaiveBayes 폴백으로 라우팅된다.
- 처음부터 재학습/재현하려면 원본 repo에서 (코드는 이 패키지에 미포함):
  1. `pipeline/run_preprocessing.py` — 3/5/7일 데이터셋 생성
  2. `pipeline/run_dhw_experiment.py` — DHW 확장 데이터셋 생성
  3. `pipeline/train_hybrid_deploy.py` — ⭐ `hybrid_model.joblib` 재생성
  4. `pipeline/validate_hybrid_frontier_dhw.py` — 성능(0.679 @ 0.114) 재검증
- baseline joblib(§6)은 참고선이며, 운영 해석은 §4 하이브리드 결과를 기준으로 한다.

## 10. 제외한 파일

- 원본 raw 센서 CSV (`manufacturer 1/operational_data/*`)
- 전처리 parquet (`data/processed/*.parquet`) — 코드로 재생성
- 실험 노트북 (`modeling/*.ipynb`) 및 중간 실험 CSV
- manufacturer 2 관련 일체

## 11. 무결성 확인

`MANIFEST.json`에 각 파일의 byte size와 SHA256 hash가 들어 있다.
전달 후 파일 손상 여부를 확인할 때 이 값을 비교한다.

## 12. 필요한 Python 패키지

모델 로딩/재현에는 최소한 아래 계열 패키지가 필요하다.

- `joblib`
- `scikit-learn`
- `lightgbm`
- `pandas`
- `numpy`

프로젝트 전체 실행 환경은 repository의 `pyproject.toml`과 `uv.lock`을 기준으로 맞춘다 (Python 3.12 + uv).
