from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import anyio
import pandas as pd
from httpx import AsyncClient

from ..config import get_settings
from ..features import COMMON10, DHW_OPTIONAL_SIGNALS
from .extract import parse_substation

SENSOR_COLUMNS = [*COMMON10, *DHW_OPTIONAL_SIGNALS]
TICK_REAL_SECONDS = 0.5


def load_substation_frame(data_dir: Path, substation_id: str) -> pd.DataFrame:
    manufacturer, raw_id = parse_substation(substation_id)
    path = data_dir / manufacturer / f"substation_{raw_id}.csv"
    if not path.exists():
        raise FileNotFoundError(f"추출된 CSV 없음: {path}")
    frame = pd.read_csv(path, sep=";")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    for column in frame.columns:
        if column != "timestamp":
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)


def rows_to_readings(substation_id: str, rows: pd.DataFrame) -> list[dict[str, object]]:
    readings: list[dict[str, object]] = []
    for _, row in rows.iterrows():
        values = {col: None if pd.isna(row.get(col)) else float(row[col]) for col in SENSOR_COLUMNS if col in rows.columns}
        readings.append({"substation_id": substation_id, "ts": row["timestamp"].isoformat(), "values": values})
    return readings


async def post_batch(client: AsyncClient, base_url: str, readings: list[dict[str, object]]) -> None:
    if not readings:
        return
    response = await client.post(f"{base_url}/ingest/readings", json={"readings": readings}, timeout=60)
    response.raise_for_status()


async def run_replay(speed_factor: float, virtual_start: datetime | None) -> None:
    settings = get_settings()
    frames = {sub: load_substation_frame(settings.replay_data_dir, sub) for sub in settings.replay_substation_list}
    if virtual_start is None:
        first_ts = min(pd.Timestamp(frame["timestamp"].min()).to_pydatetime() for frame in frames.values())
        virtual_start = first_ts.replace(tzinfo=timezone.utc) + timedelta(days=settings.replay_warmup_days)
    if virtual_start.tzinfo is None:
        virtual_start = virtual_start.replace(tzinfo=timezone.utc)
    async with AsyncClient() as client:
        substation_payload = []
        for substation, frame in frames.items():
            manufacturer, raw_id = parse_substation(substation)
            substation_payload.append(
                {
                    "substation_id": substation,
                    "manufacturer": manufacturer,
                    "raw_id": raw_id,
                    "sensor_columns": [c for c in frame.columns if c != "timestamp"],
                }
            )
        response = await client.post(f"{settings.api_base_url}/ingest/substations", json=substation_payload, timeout=30)
        response.raise_for_status()
        virtual_time = virtual_start
        while True:
            next_virtual = virtual_time + timedelta(minutes=speed_factor * TICK_REAL_SECONDS)
            batch: list[dict[str, object]] = []
            done_count = 0
            for substation, frame in frames.items():
                lo = pd.Timestamp(virtual_time.replace(tzinfo=None))
                hi = pd.Timestamp(next_virtual.replace(tzinfo=None))
                chunk = frame[(frame["timestamp"] >= lo) & (frame["timestamp"] < hi)]
                batch.extend(rows_to_readings(substation, chunk))
                if frame["timestamp"].iloc[-1] < lo:
                    done_count += 1
            await post_batch(client, settings.api_base_url, batch)
            await client.post(
                f"{settings.api_base_url}/replay/clock",
                json={"virtual_time": next_virtual.isoformat(), "speed_factor": speed_factor, "running": True},
                timeout=30,
            )
            if done_count == len(frames):
                await client.post(
                    f"{settings.api_base_url}/replay/clock",
                    json={"virtual_time": next_virtual.isoformat(), "speed_factor": speed_factor, "running": False},
                    timeout=30,
                )
                return
            virtual_time = next_virtual
            await anyio.sleep(TICK_REAL_SECONDS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--speed", type=float, default=None)
    parser.add_argument("--start", default=None)
    args = parser.parse_args()
    settings = get_settings()
    speed = args.speed if args.speed is not None else settings.replay_speed_factor
    start = datetime.fromisoformat(args.start) if args.start else None
    anyio.run(run_replay, speed, start)


if __name__ == "__main__":
    main()
