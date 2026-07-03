from __future__ import annotations

from pathlib import Path

from heatgrid_ops.config import REPO_ROOT, SERVICE_ROOT, Settings, ensure_allowed_input_path


def test_relative_env_paths_resolve_from_service_root() -> None:
    settings = Settings(subdataset_dir=Path("../13_서브데이터셋"))

    assert settings.subdataset_dir == REPO_ROOT / "13_서브데이터셋"
    assert settings.subdataset_dir != SERVICE_ROOT / "backend" / "../13_서브데이터셋"


def test_resolved_subdataset_dir_passes_input_guard() -> None:
    settings = Settings(subdataset_dir=Path("../13_서브데이터셋"))

    ensure_allowed_input_path(settings.subdataset_dir)
