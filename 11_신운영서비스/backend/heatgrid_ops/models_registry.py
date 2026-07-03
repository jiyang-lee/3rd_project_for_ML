from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

from .config import get_settings
from .pipeline.priority import WEIGHTS

GATE_NAMES = ["fault_gate", "task_gate", "activity_gate"]
PRE_EVENT_NAME = "fault_pre_event_gate"
EXPECTED_SKLEARN_VERSION = "1.9.0"


@dataclass
class GateModel:
    name: str
    pipeline: object
    threshold: float
    features: list[str]
    system_thresholds: dict[str, float] = field(default_factory=dict)
    model_name: str = ""
    model_status: str = ""

    def probability(self, feats: dict[str, float]) -> float:
        row = pd.DataFrame([[feats.get(f, np.nan) for f in self.features]], columns=self.features)
        proba = self.pipeline.predict_proba(row)
        classes = list(getattr(self.pipeline, "classes_", [0, 1]))
        if 1 in classes:
            return float(proba[0][classes.index(1)])
        return float(proba[0][-1])

    def threshold_for(self, system_capability_group: str | None) -> float:
        if system_capability_group is None:
            return self.threshold
        return float(self.system_thresholds.get(system_capability_group, self.threshold))


@dataclass
class ModelRegistry:
    gates: dict[str, GateModel] = field(default_factory=dict)
    pre_event: GateModel | None = None
    priority_weights: dict[str, float] = field(default_factory=dict)

    @property
    def loaded(self) -> bool:
        return len(self.gates) == 3 and self.pre_event is not None


_registry: ModelRegistry | None = None


def assert_sklearn_runtime() -> None:
    if sklearn.__version__ != EXPECTED_SKLEARN_VERSION:
        msg = f"sklearn joblib 호환 위험: expected {EXPECTED_SKLEARN_VERSION}, got {sklearn.__version__}"
        raise RuntimeError(msg)


def _package_root(metadata_path: Path) -> Path:
    return metadata_path.parent.parent.parent


def _resolve_model_file(metadata_path: Path, spec: dict[str, object]) -> Path:
    if "packaged_model_path" in spec:
        raw = str(spec["packaged_model_path"]).replace("\\", "/")
        return _package_root(metadata_path) / raw
    raw_path = Path(str(spec["model_path"]).replace("\\", "/"))
    if raw_path.is_absolute():
        return raw_path
    return metadata_path.parent / raw_path.name


def _load_pipeline(model_file: Path) -> object:
    loaded = joblib.load(model_file)
    if isinstance(loaded, dict) and "model" in loaded:
        return loaded["model"]
    return loaded


def _gate_from_spec(name: str, spec: dict[str, object], metadata_path: Path, threshold: float | None = None) -> GateModel:
    model_file = _resolve_model_file(metadata_path, spec)
    if not model_file.exists():
        raise FileNotFoundError(f"model joblib not found: {model_file}")
    raw_features = spec.get("features", [])
    if not isinstance(raw_features, list):
        raise RuntimeError(f"{name} features contract is not a list")
    return GateModel(
        name=name,
        pipeline=_load_pipeline(model_file),
        threshold=float(threshold if threshold is not None else spec["threshold"]),
        features=[str(f) for f in raw_features],
        system_thresholds={str(k): float(v) for k, v in dict(spec.get("system_thresholds", {})).items()},
        model_name=str(spec.get("model_type") or spec.get("model_name") or ""),
        model_status=str(spec.get("status") or ""),
    )


def load_registry() -> ModelRegistry:
    global _registry
    if _registry is not None:
        return _registry
    assert_sklearn_runtime()
    metadata_path = get_settings().runtime_metadata_path
    if not metadata_path.exists():
        raise FileNotFoundError(f"runtime metadata not found: {metadata_path}; run setup/bootstrap.py first")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    registry = ModelRegistry(priority_weights=dict(WEIGHTS))
    for name in GATE_NAMES:
        registry.gates[name] = _gate_from_spec(name, metadata["front_gates"][name], metadata_path)
    spec = metadata["pre_event_gate"]
    registry.pre_event = _gate_from_spec(
        PRE_EVENT_NAME,
        spec,
        metadata_path,
        threshold=float(spec["fallback_threshold"]),
    )
    _registry = registry
    return registry
