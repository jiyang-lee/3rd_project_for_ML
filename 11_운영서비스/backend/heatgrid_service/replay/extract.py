"""PreDist zip에서 리플레이 대상 substation CSV를 1회 추출하는 CLI.

사용:
  python -m heatgrid_service.replay.extract                 # .env의 REPLAY_SUBSTATIONS 추출
  python -m heatgrid_service.replay.extract --list-scenarios # fault Report date 목록 출력
"""

from __future__ import annotations

import argparse
import logging
import zipfile
from pathlib import Path

import pandas as pd

from ..config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("replay.extract")

ZIP_PREFIX = {"M1": "manufacturer 1", "M2": "manufacturer 2"}
META_DIR = {"M1": "manufacturer_1", "M2": "manufacturer_2"}


def parse_substation(sub: str) -> tuple[str, int]:
    manufacturer, raw = sub.split("_", 1)
    return manufacturer, int(raw)


def extract_substations(substations: list[str]) -> None:
    settings = get_settings()
    out_root = Path(settings.replay_data_dir)
    with zipfile.ZipFile(settings.predist_zip_path) as zf:
        names = set(zf.namelist())
        for sub in substations:
            manufacturer, raw_id = parse_substation(sub)
            member = f"{ZIP_PREFIX[manufacturer]}/operational_data/substation_{raw_id}.csv"
            if member not in names:
                logger.warning("zip에 없음: %s", member)
                continue
            target = out_root / manufacturer / f"substation_{raw_id}.csv"
            if target.exists():
                logger.info("이미 추출됨: %s", target)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src:
                target.write_bytes(src.read())
            logger.info("추출 완료: %s (%.1f MB)", target, target.stat().st_size / 1e6)


def list_scenarios() -> None:
    settings = get_settings()
    for manufacturer in ["M1", "M2"]:
        path = Path(settings.predist_metadata_dir) / META_DIR[manufacturer] / "faults.csv"
        if not path.exists():
            continue
        faults = pd.read_csv(path, sep=";")
        faults["Report date"] = pd.to_datetime(faults["Report date"], errors="coerce")
        view = faults.sort_values("Report date")[
            ["Event ID", "substation ID", "Report date", "Fault label", "efd_possible"]
        ]
        print(f"\n=== {manufacturer} fault events ===")
        print(view.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--substations", default=None, help="쉼표구분 목록 (기본: .env REPLAY_SUBSTATIONS)")
    parser.add_argument("--list-scenarios", action="store_true")
    args = parser.parse_args()

    if args.list_scenarios:
        list_scenarios()
        return

    settings = get_settings()
    subs = (
        [s.strip() for s in args.substations.split(",") if s.strip()]
        if args.substations
        else settings.replay_substation_list
    )
    extract_substations(subs)


if __name__ == "__main__":
    main()
