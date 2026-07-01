"""
inference_example.py
====================
설비별 하이브리드 모델(hybrid_model.joblib)로 '한 이벤트(설비의 window들)'를 채점하는 예제.
이 스크립트는 repo 없이 이 패키지 파일만으로 동작한다 (필요 패키지: numpy, pandas, scikit-learn).

입력: 한 이벤트의 window 피처 표 (행=window, 열=feature_names 순서).
출력: 0/1 (1=고장 전조로 판정) + 근거 점수.

핵심 로직:
  ● covered 설비(자기 정상 이력 보유) → 설비별 LOF 백분위 점수
  ● uncovered 설비 → 전역 NaiveBayes 확률
  ● 두 갈래 모두 '이벤트 규칙': longest_run(window_score >= thr) >= K → 고장
"""
from __future__ import annotations

from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

MODEL = joblib.load(Path(__file__).with_name("hybrid_model.joblib"))
FEAT = MODEL["feature_names"]
COVERED = set(MODEL["covered_substations"])


def longest_run(flags: np.ndarray) -> int:
    """연속으로 True인 최대 길이."""
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return best


def _anomaly_score(pipe, X: pd.DataFrame) -> np.ndarray:
    """높을수록 이상. score_samples/decision_function 부호 반전."""
    est = pipe.named_steps["est"]
    if isinstance(est, IsolationForest):
        return -pipe.score_samples(X)
    return -pipe.decision_function(X)   # LOF(novelty) / OneClassSVM


def _to_percentile(scores: np.ndarray, ref_normal: np.ndarray) -> np.ndarray:
    """이상점수 → 정상분포 대비 백분위 [0,1] (높을수록 이상)."""
    ref = np.sort(ref_normal)
    return np.searchsorted(ref, scores, side="right") / max(1, len(ref))


def predict_event(substation_id, window_features: pd.DataFrame) -> dict:
    """
    substation_id : 이 이벤트가 속한 설비 id
    window_features : DataFrame, 열 순서 = MODEL['feature_names']
    반환 : {'pred':0/1, 'branch':'per-sub'|'nb', 'window_scores':..., 'thr':..., 'K':...}
    """
    sub = str(substation_id)
    X = window_features[FEAT]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")   # DHW 미보유 설비의 빈 컬럼 경고 무시
        if sub in COVERED:
            pipe = MODEL["persub_detectors"][sub]
            ref = MODEL["persub_refs"][sub]
            scores = _to_percentile(_anomaly_score(pipe, X), ref)
            op = MODEL["persub_operating_point"]
            branch = "per-sub"
        else:
            scores = MODEL["nb_pipeline"].predict_proba(X)[:, 1]
            op = MODEL["nb_operating_point"]
            branch = "nb"
    pred = int(longest_run(scores >= op["thr"]) >= op["K"])
    return {"pred": pred, "branch": branch, "window_scores": scores,
            "thr": op["thr"], "K": op["K"]}


if __name__ == "__main__":
    # 데모: 무작위 window 표로 형식만 확인 (실제로는 전처리된 이벤트 window를 넣는다)
    demo = pd.DataFrame(np.random.RandomState(0).randn(10, len(FEAT)), columns=FEAT)
    covered_example = next(iter(COVERED))
    print("covered 설비 예:", predict_event(covered_example, demo)["branch"],
          "→ pred", predict_event(covered_example, demo)["pred"])
    print("uncovered(미지 설비) 예:", predict_event("UNKNOWN_SUB", demo)["branch"],
          "→ pred", predict_event("UNKNOWN_SUB", demo)["pred"])
    print("\n입력 피처 개수:", len(FEAT), "| covered 설비 수:", len(COVERED))
    print("운영점 per-sub:", MODEL["persub_operating_point"],
          "| nb:", MODEL["nb_operating_point"])
