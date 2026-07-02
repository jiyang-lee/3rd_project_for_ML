"""PreDist 리플레이 publisher — 추출된 CSV를 가속 가상시계로 API에 재생하는 별도 프로세스.

사용: python -m heatgrid_service.replay.publisher [--speed 60] [--start 2015-11-20T00:00:00]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pandas as pd

from ..config import get_settings
from ..features import COMMON10, DHW_OPTIONAL_SIGNALS
from .extract import META_DIR, parse_substation

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("replay.publisher")

SENSOR_COLUMNS = [*COMMON10, *DHW_OPTIONAL_SIGNALS]
TICK_REAL_SECONDS = 0.5


def load_substation_frame(data_dir: Path, sub_id: str) -> pd.DataFrame:
    manufacturer, raw_id = parse_substation(sub_id)
    path = data_dir / manufacturer / f"substation_{raw_id}.csv"
    if not path.exists():
        raise FileNotFoundError(f"추출된 CSV 없음: {path} — 먼저 replay.extract 를 실행하세요")
    df = pd.read_csv(path, sep=";")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in df.columns:
        if col != "timestamp":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)


def default_virtual_start(substations: list[str]) -> datetime:
    """데모 시나리오: 대상 기계실 fault 중 가장 이른 Report date - 10일."""
    settings = get_settings()
    report_dates = []
    by_manufacturer: dict[str, list[int]] = {}
    for sub in substations:
        manufacturer, raw_id = parse_substation(sub)
        by_manufacturer.setdefault(manufacturer, []).append(raw_id)
    for manufacturer, ids in by_manufacturer.items():
        path = Path(settings.predist_metadata_dir) / META_DIR[manufacturer] / "faults.csv"
        faults = pd.read_csv(path, sep=";")
        faults["Report date"] = pd.to_datetime(faults["Report date"], errors="coerce")
        subset = faults[faults["substation ID"].isin(ids)]
        report_dates.extend(subset["Report date"].dropna().tolist())
    if not report_dates:
        raise ValueError("대상 기계실에 fault 이벤트가 없어 virtual_start를 자동 결정할 수 없습니다")
    return (min(report_dates) - pd.Timedelta(days=10)).to_pydatetime()


def rows_to_readings(sub_id: str, rows: pd.DataFrame) -> list[dict]:
    readings = []
    for _, row in rows.iterrows():
        values = {}
        for col in SENSOR_COLUMNS:
            if col in rows.columns:
                v = row[col]
                values[col] = None if pd.isna(v) else float(v)
        readings.append(
            {
                "substation_id": sub_id,
                "ts": row["timestamp"].isoformat(),
                "values": values,
            }
        )
    return readings


async def post_batch(client: httpx.AsyncClient, base: str, readings: list[dict]) -> None:
    if not readings:
        return
    resp = await client.post(f"{base}/api/ingest/readings", json={"readings": readings}, timeout=60)
    resp.raise_for_status()


async def run_replay(speed_factor: float, virtual_start: datetime | None) -> None:
    settings = get_settings()
    base = settings.api_base_url
    subs = settings.replay_substation_list
    data_dir = Path(settings.replay_data_dir)

    frames = {sub: load_substation_frame(data_dir, sub) for sub in subs}
    logger.info("로드 완료: %s", {s: len(f) for s, f in frames.items()})

    if virtual_start is None:
        if settings.replay_virtual_start:
            virtual_start = datetime.fromisoformat(settings.replay_virtual_start)
        else:
            virtual_start = default_virtual_start(subs)
    if virtual_start.tzinfo is None:
        virtual_start = virtual_start.replace(tzinfo=timezone.utc)
    logger.info("가상 시작시각: %s | 속도: 1초 = %.0f가상분", virtual_start, speed_factor)

    async with httpx.AsyncClient() as client:
        # 기계실 등록
        substation_payload = []
        for sub in subs:
            manufacturer, raw_id = parse_substation(sub)
            substation_payload.append(
                {
                    "substation_id": sub,
                    "manufacturer": manufacturer,
                    "raw_id": raw_id,
                    "sensor_columns": [c for c in frames[sub].columns if c != "timestamp"],
                }
            )
        resp = await client.post(f"{base}/api/ingest/substations", json=substation_payload, timeout=30)
        resp.raise_for_status()
        logger.info("기계실 등록: %s", resp.json())

        # warmup 백필: virtual_start 이전 N일
        warmup_start = virtual_start - timedelta(days=settings.replay_warmup_days)
        for sub, frame in frames.items():
            naive_start = pd.Timestamp(warmup_start.replace(tzinfo=None))
            naive_end = pd.Timestamp(virtual_start.replace(tzinfo=None))
            chunk = frame[(frame["timestamp"] >= naive_start) & (frame["timestamp"] < naive_end)]
            for i in range(0, len(chunk), 2000):
                await post_batch(client, base, rows_to_readings(sub, chunk.iloc[i : i + 2000]))
            logger.info("warmup 백필 %s: %d행", sub, len(chunk))

        # 본 재생 루프
        virtual_time = virtual_start
        cursor = {sub: None for sub in subs}
        while True:
            next_virtual = virtual_time + timedelta(minutes=speed_factor * TICK_REAL_SECONDS)
            batch: list[dict] = []
            done = 0
            for sub, frame in frames.items():
                naive_lo = pd.Timestamp(virtual_time.replace(tzinfo=None))
                naive_hi = pd.Timestamp(next_virtual.replace(tzinfo=None))
                chunk = frame[(frame["timestamp"] >= naive_lo) & (frame["timestamp"] < naive_hi)]
                batch.extend(rows_to_readings(sub, chunk))
                if frame["timestamp"].iloc[-1] < naive_lo:
                    done += 1
            await post_batch(client, base, batch)
            await client.post(
                f"{base}/api/replay/clock",
                json={
                    "virtual_time": next_virtual.isoformat(),
                    "speed_factor": speed_factor,
                    "running": True,
                },
                timeout=30,
            )
            if batch:
                logger.info("가상 %s | %d readings 전송", next_virtual.strftime("%Y-%m-%d %H:%M"), len(batch))
            if done == len(subs):
                logger.info("모든 기계실 데이터 소진 — 리플레이 종료")
                await client.post(
                    f"{base}/api/replay/clock",
                    json={"virtual_time": next_virtual.isoformat(), "speed_factor": speed_factor, "running": False},
                    timeout=30,
                )
                break
            virtual_time = next_virtual
            await asyncio.sleep(TICK_REAL_SECONDS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--speed", type=float, default=None, help="1초당 가상 분 (기본 .env)")
    parser.add_argument("--start", default=None, help="가상 시작시각 ISO (기본: 자동 시나리오)")
    args = parser.parse_args()

    settings = get_settings()
    speed = args.speed if args.speed is not None else settings.replay_speed_factor
    start = datetime.fromisoformat(args.start) if args.start else None
    asyncio.run(run_replay(speed, start))


if __name__ == "__main__":
    main()
