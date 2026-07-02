"""joblib 모델 4개 로드 + runtime policy 메타데이터.

m1_full_gate_runtime_policy_metadata.json 이 피처 순서/threshold의 source of truth.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .config import get_settings

GATE_NAMES = ["fault_gate", "task_gate", "activity_gate"]
PRE_EVENT_NAME = "fault_pre_event_gate"


@dataclass
class GateModel:
    name: str
    pipeline: object
    threshold: float
    features: list[str]

    def probability(self, feats: dict[str, float]) -> float:
        row = pd.DataFrame([[feats.get(f, np.nan) for f in self.features]], columns=self.features)
        proba = self.pipeline.predict_proba(row)
        classes = list(getattr(self.pipeline, "classes_", [0, 1]))
        if 1 in classes:
            return float(proba[0][classes.index(1)])
        return float(proba[0][-1])


@dataclass
class ModelRegistry:
    gates: dict[str, GateModel] = field(default_factory=dict)
    pre_event: GateModel | None = None
    priority_weights: dict[str, float] = field(default_factory=dict)

    @property
    def loaded(self) -> bool:
        return len(self.gates) == 3 and self.pre_event is not None


_registry: ModelRegistry | None = None


def load_registry() -> ModelRegistry:
    global _registry
    if _registry is not None:
        return _registry

    settings = get_settings()
    metadata_path = Path(settings.runtime_metadata_path)
    if not metadata_path.exists():
        raise FileNotFoundError(f"runtime metadata not found: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    registry = ModelRegistry()
    registry.priority_weights = metadata["runtime_policy"]["priority_policy"]["weights"]

    for name in [*GATE_NAMES, PRE_EVENT_NAME]:
        spec = metadata["models"][name]
        model_file = Path(settings.model_dir) / Path(spec["model_path"].replace("\\", "/")).name
        if not model_file.exists():
            raise FileNotFoundError(f"model joblib not found: {model_file}")
        gate = GateModel(
            name=name,
            pipeline=joblib.load(model_file),
            threshold=float(spec["threshold"]),
            features=list(spec["features"]),
        )
        if name == PRE_EVENT_NAME:
            registry.pre_event = gate
        else:
            registry.gates[name] = gate

    _registry = registry
    return registry
