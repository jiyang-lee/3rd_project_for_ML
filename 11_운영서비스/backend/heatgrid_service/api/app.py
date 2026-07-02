from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from ..db import close_pool, get_pool
from ..models_registry import load_registry
from .ingest import router as ingest_router
from .queries import router as queries_router
from .ws import broadcaster

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("heatgrid")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_registry()  # fail fast if joblib/metadata missing
    await get_pool()
    from ..scheduler import inference_loop

    task = asyncio.create_task(inference_loop())
    logger.info("heatgrid service started: models loaded, inference loop running")
    try:
        yield
    finally:
        task.cancel()
        await close_pool()


app = FastAPI(title="HeatGrid 운영서비스", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(queries_router)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await broadcaster.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keepalive; 클라이언트 메시지는 무시
    except WebSocketDisconnect:
        await broadcaster.disconnect(ws)
