from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import get_settings


@dataclass(frozen=True)
class AnomalyDecision:
    detected: bool
    reason: str


def load_anomaly_metadata(path: Path | None = None) -> dict[str, str | int | float | list[str]]:
    metadata_path = path or get_settings().handoff_dir / "models" / "anomaly" / "anomaly_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"anomaly metadata not found: {metadata_path}")
    raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    return dict(raw)


def decide_anomaly(features: dict[str, float | int | None]) -> AnomalyDecision:
    iforest = float(features.get("iforest_score_ratio") or 0.0)
    mahal = float(features.get("mahalanobis_score_ratio") or 0.0)
    criticality = float(features.get("anomaly_criticality") or 0.0)
    detected = iforest >= 0.90 and mahal >= 1.00 and criticality > 5.0
    reason = f"iforest={iforest:.2f}, mahalanobis={mahal:.2f}, criticality={criticality:.1f}"
    return AnomalyDecision(detected=detected, reason=reason)
