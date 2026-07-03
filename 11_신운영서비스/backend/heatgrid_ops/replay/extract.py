from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ZIP_PREFIX = {"M1": "manufacturer 1", "M2": "manufacturer 2"}
META_DIR = {"M1": "manufacturer_1", "M2": "manufacturer_2"}


def parse_substation(substation_id: str) -> tuple[str, int]:
    manufacturer, raw = substation_id.split("_", 1)
    return manufacturer, int(raw)


def member_for_substation(manufacturer: str, raw_id: int) -> str:
    prefix = ZIP_PREFIX[manufacturer]
    return f"{prefix}/operational_data/substation_{raw_id}.csv"


def extract_substations(zip_path: Path, output_dir: Path, substations: list[str]) -> list[Path]:
    output_paths: list[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        for substation in substations:
            manufacturer, raw_id = parse_substation(substation)
            member = member_for_substation(manufacturer, raw_id)
            if member not in names:
                raise RuntimeError(f"PreDist zip 멤버 없음: {member}")
            target = output_dir / manufacturer / f"substation_{raw_id}.csv"
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                with archive.open(member) as source:
                    target.write_bytes(source.read())
            output_paths.append(target)
    return output_paths


def main() -> None:
    from ..config import get_settings

    settings = get_settings()
    parser = argparse.ArgumentParser()
    parser.add_argument("--substations", default=settings.replay_substations)
    args = parser.parse_args()
    substations = [s.strip() for s in args.substations.split(",") if s.strip()]
    paths = extract_substations(settings.predist_zip_path, settings.replay_data_dir, substations)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
