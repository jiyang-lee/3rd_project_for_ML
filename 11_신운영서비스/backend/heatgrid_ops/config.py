from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SERVICE_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(SERVICE_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://heatgrid:heatgrid_dev@127.0.0.1:5434/heatgrid"
    final_model_zip: Path = REPO_ROOT / "12_최종모델" / "m1_specialist_handoff.zip"
    predist_zip_path: Path = REPO_ROOT / "05_데이터셋" / "PreDist" / "predist_dataset.zip"
    predist_metadata_dir: Path = REPO_ROOT / "05_데이터셋" / "PreDist" / "metadata"
    subdataset_dir: Path = REPO_ROOT / "13_서브데이터셋"

    artifact_dir: Path = SERVICE_ROOT / "artifacts"
    handoff_dir: Path = artifact_dir / "handoff" / "m1_specialist_handoff"
    derived_dir: Path = artifact_dir / "derived"
    replay_data_dir: Path = SERVICE_ROOT / "data" / "replay"

    replay_substations: str = "M1_11,M1_12,M1_30,M1_4,M1_18"
    replay_virtual_start: str = ""
    replay_speed_factor: float = 60.0
    replay_warmup_days: int = 7
    inference_virtual_stride_hours: int = 6
    inference_real_interval_sec: int = 10
    coverage_min: float = 0.5

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_daily_token_budget: int = 200000
    llm_cache_ttl_hours: int = 24
    agent_top_n: int = 5
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_dim: int = 384
    api_port: int = 8000
    api_base_url: str = "http://127.0.0.1:8000"

    @field_validator(
        "final_model_zip",
        "predist_zip_path",
        "predist_metadata_dir",
        "subdataset_dir",
        mode="before",
    )
    @classmethod
    def resolve_service_relative_path(cls, value: Path | str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (SERVICE_ROOT / path).resolve()

    @property
    def runtime_metadata_path(self) -> Path:
        return self.handoff_dir / "models" / "m1_specialist" / "m1_full_gate_runtime_policy_metadata.json"

    @property
    def handoff_agent_card_csv(self) -> Path:
        return self.handoff_dir / "agent_contract" / "agent_priority_card.csv"

    @property
    def agent_state_card_schema_json(self) -> Path:
        return self.handoff_dir / "agent_contract" / "agent_state_card_schema.json"

    @property
    def group_profile_csv(self) -> Path:
        return self.derived_dir / "m1_fault_group_priority_profile.csv"

    @property
    def leadtime_summary_csv(self) -> Path:
        return self.derived_dir / "m1_fault_group_leadtime_summary.csv"

    @property
    def replay_substation_list(self) -> list[str]:
        return [s.strip() for s in self.replay_substations.split(",") if s.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def ensure_allowed_input_path(path: Path) -> None:
    resolved = path.resolve()
    allowed_roots = [
        (REPO_ROOT / "05_데이터셋").resolve(),
        (REPO_ROOT / "12_최종모델").resolve(),
        (REPO_ROOT / "13_서브데이터셋").resolve(),
    ]
    if not any(resolved == root or root in resolved.parents for root in allowed_roots):
        msg = f"입력 경로 제약 위반: {resolved}"
        raise RuntimeError(msg)
