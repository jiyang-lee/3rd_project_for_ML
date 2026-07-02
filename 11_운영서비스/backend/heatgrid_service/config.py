from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 11_운영서비스/ 디렉터리 (backend/heatgrid_service/config.py 기준 2단계 상위)
SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SERVICE_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(SERVICE_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://heatgrid:heatgrid_dev@127.0.0.1:5433/heatgrid"

    model_dir: Path = REPO_ROOT / "08_모델산출물"
    runtime_metadata_path: Path = REPO_ROOT / "08_모델산출물" / "m1_full_gate_runtime_policy_metadata.json"
    group_profile_csv: Path = REPO_ROOT / "07_데이터산출물" / "m1_fault_group_priority_profile.csv"
    leadtime_summary_csv: Path = REPO_ROOT / "07_데이터산출물" / "m1_fault_group_leadtime_summary.csv"
    predist_metadata_dir: Path = REPO_ROOT / "05_데이터셋" / "PreDist" / "metadata"
    predist_zip_path: Path = REPO_ROOT / "05_데이터셋" / "PreDist" / "predist_dataset.zip"

    replay_data_dir: Path = SERVICE_ROOT / "data" / "predist"
    replay_substations: str = "M1_11,M1_12,M1_30,M1_4,M1_18"
    replay_virtual_start: str = ""
    replay_speed_factor: float = 60.0
    replay_warmup_days: int = 7

    inference_virtual_stride_hours: int = 6
    inference_real_interval_sec: int = 10
    coverage_min: float = 0.5

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    agent_min_interval_sec: int = 30
    agent_dispatch_top_k: int = 3

    api_base_url: str = "http://127.0.0.1:8000"
    api_port: int = 8000

    def _resolve(self, value: Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = (SERVICE_ROOT / path).resolve()
        return path

    def model_post_init(self, __context) -> None:
        for field in [
            "model_dir",
            "runtime_metadata_path",
            "group_profile_csv",
            "leadtime_summary_csv",
            "predist_metadata_dir",
            "predist_zip_path",
            "replay_data_dir",
        ]:
            object.__setattr__(self, field, self._resolve(getattr(self, field)))

    @property
    def replay_substation_list(self) -> list[str]:
        return [s.strip() for s in self.replay_substations.split(",") if s.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
