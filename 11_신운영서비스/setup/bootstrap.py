from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import pandas as pd

import sys

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from heatgrid_ops.config import ensure_allowed_input_path, get_settings  # noqa: E402
from heatgrid_ops.pipeline.priority import semantic_fault_group  # noqa: E402
from heatgrid_ops.replay.extract import member_for_substation, parse_substation  # noqa: E402

REQUIRED_HANDOFF_ENTRIES = {
    "m1_specialist_handoff/agent_contract/agent_priority_card.csv",
    "m1_specialist_handoff/agent_contract/agent_state_card_schema.json",
    "m1_specialist_handoff/models/m1_specialist/m1_full_gate_runtime_policy_metadata.json",
    "m1_specialist_handoff/models/m1_specialist/m1_fault_gate_rf_depth3.joblib",
    "m1_specialist_handoff/models/m1_specialist/m1_task_gate_rf_depth3.joblib",
    "m1_specialist_handoff/models/m1_specialist/m1_activity_gate_rf_depth3.joblib",
    "m1_specialist_handoff/models/m1_specialist/m1_fault_pre_event_logistic.joblib",
    "m1_specialist_handoff/models/anomaly/anomaly_metadata.json",
    "m1_specialist_handoff/scores/priority_scores.csv",
    "m1_specialist_handoff/scores/leadtime_scores.csv",
}


def extract_handoff() -> None:
    settings = get_settings()
    ensure_allowed_input_path(settings.final_model_zip)
    with zipfile.ZipFile(settings.final_model_zip) as archive:
        names = set(archive.namelist())
        missing = sorted(REQUIRED_HANDOFF_ENTRIES - names)
        if missing:
            raise RuntimeError(f"handoff zip 필수 엔트리 누락: {missing}")
        archive.extractall(settings.artifact_dir / "handoff")


def derive_priority_profiles() -> None:
    settings = get_settings()
    settings.derived_dir.mkdir(parents=True, exist_ok=True)
    scores = pd.read_csv(settings.handoff_dir / "scores" / "priority_scores.csv")
    cards = pd.read_csv(settings.handoff_agent_card_csv)

    profile = cards.copy()
    profile["fault_group"] = profile["m1_specialist_fault_group"].fillna("unknown_review")
    profile["group_weight"] = pd.to_numeric(profile["m1_specialist_group_weight"], errors="coerce").fillna(0.1)
    profile = profile.groupby("fault_group", as_index=False)["group_weight"].mean()
    profile.to_csv(settings.group_profile_csv, index=False, encoding="utf-8")

    lead = scores.copy()
    lead["fault_group"] = lead["fault_label"].fillna("unknown").map(semantic_fault_group)
    lead["leadtime_label"] = lead["predicted_lead_time_bucket"].fillna("not_available")
    leadtime_column = "estimated_lead_time_hours" if "estimated_lead_time_hours" in lead.columns else "expected_lead_time_hours"
    lead["median_stable_lead_time_hours"] = pd.to_numeric(lead[leadtime_column], errors="coerce")
    lead["scope"] = "main"
    summary = lead.groupby(["scope", "fault_group"], as_index=False).agg(
        leadtime_label=("leadtime_label", "first"),
        median_stable_lead_time_hours=("median_stable_lead_time_hours", "median"),
    )
    summary.to_csv(settings.leadtime_summary_csv, index=False, encoding="utf-8-sig")


def extract_replay_members() -> None:
    settings = get_settings()
    ensure_allowed_input_path(settings.predist_zip_path)
    with zipfile.ZipFile(settings.predist_zip_path) as archive:
        names = set(archive.namelist())
        for substation in settings.replay_substation_list:
            manufacturer, raw_id = parse_substation(substation)
            member = member_for_substation(manufacturer, raw_id)
            if member not in names:
                raise RuntimeError(f"PreDist zip 멤버 없음: {member}")
            target = settings.replay_data_dir / manufacturer / f"substation_{raw_id}.csv"
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                with archive.open(member) as source:
                    target.write_bytes(source.read())


def copy_metadata() -> None:
    settings = get_settings()
    ensure_allowed_input_path(settings.predist_metadata_dir)
    target = settings.replay_data_dir / "metadata"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(settings.predist_metadata_dir, target)


def write_manifest() -> None:
    settings = get_settings()
    schema = json.loads(settings.agent_state_card_schema_json.read_text(encoding="utf-8"))
    manifest = {
        "handoff_entries": len(list(settings.handoff_dir.rglob("*"))),
        "agent_card_columns": len(schema.get("columns", [])),
        "replay_substations": settings.replay_substation_list,
        "allowed_inputs": ["05_데이터셋", "12_최종모델", "13_서브데이터셋"],
    }
    (settings.artifact_dir / "bootstrap_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    settings = get_settings()
    settings.artifact_dir.mkdir(parents=True, exist_ok=True)
    settings.replay_data_dir.mkdir(parents=True, exist_ok=True)
    extract_handoff()
    derive_priority_profiles()
    extract_replay_members()
    copy_metadata()
    write_manifest()
    print(f"bootstrap complete: {settings.artifact_dir}")


if __name__ == "__main__":
    main()
