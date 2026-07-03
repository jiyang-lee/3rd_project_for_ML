from __future__ import annotations

import csv
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from heatgrid_ops.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    output = settings.derived_dir / "synthetic_seed_preview.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for path in (settings.predist_metadata_dir).glob("manufacturer_*/faults.csv"):
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            for row in list(reader)[:20]:
                rows.append(
                    {
                        "source": str(path.relative_to(settings.predist_metadata_dir)),
                        "substation_id": row.get("substation ID", ""),
                        "event_time": row.get("Report date", ""),
                        "content": row.get("Fault label", ""),
                    }
                )
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "substation_id", "event_time", "content"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"seed preview written: {output}")


if __name__ == "__main__":
    main()
