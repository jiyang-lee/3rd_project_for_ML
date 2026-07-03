#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = [
#     "matplotlib==3.10.9",
# ]
# ///

# ─── How to run ───
# 1. Install uv (if not installed):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Run directly from the project root:
#      uv run 14_회의자료/make_diagrams.py
# 3. Output PNG files are written to 14_회의자료/images/.
# ──────────────────

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, assert_never

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

Side = Literal["left", "right", "top", "bottom"]

ROOT: Final = Path(__file__).resolve().parent
IMAGE_DIR: Final = ROOT / "images"

INK: Final = "#152238"
MUTED: Final = "#5F6878"
PANEL: Final = "#F2F4F7"
PANEL_DARK: Final = "#E5EAF0"
ACCENT: Final = "#0F766E"
ACCENT_2: Final = "#D97706"
ACCENT_3: Final = "#2563EB"
LINE: Final = "#8B95A7"
WHITE: Final = "#FFFFFF"


@dataclass(frozen=True, slots=True)
class Box:
    key: str
    xy: tuple[float, float]
    size: tuple[float, float]
    text: str
    fill: str = PANEL
    edge: str = LINE
    text_color: str = INK
    fontsize: int = 12


@dataclass(frozen=True, slots=True)
class Link:
    source: str
    target: str
    source_side: Side = "right"
    target_side: Side = "left"
    label: str = ""


@dataclass(frozen=True, slots=True)
class Diagram:
    filename: str
    title: str
    subtitle: str
    boxes: tuple[Box, ...]
    links: tuple[Link, ...]
    notes: tuple[str, ...] = ()


def anchor(box: Box, side: Side) -> tuple[float, float]:
    left, top = box.xy
    width, height = box.size
    match side:
        case "left":
            return left, top + height / 2
        case "right":
            return left + width, top + height / 2
        case "top":
            return left + width / 2, top + height
        case "bottom":
            return left + width / 2, top
        case unreachable:
            assert_never(unreachable)


def draw_box(ax: Axes, box: Box) -> None:
    left, bottom = box.xy
    width, height = box.size
    patch = FancyBboxPatch(
        (left, bottom),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.4,
        edgecolor=box.edge,
        facecolor=box.fill,
    )
    ax.add_patch(patch)
    ax.text(
        left + width / 2,
        bottom + height / 2,
        box.text,
        ha="center",
        va="center",
        color=box.text_color,
        fontsize=box.fontsize,
        linespacing=1.28,
        fontweight="bold" if box.fill in {ACCENT, ACCENT_2, ACCENT_3} else "normal",
    )


def draw_link(ax: Axes, boxes: dict[str, Box], link: Link) -> None:
    start = anchor(boxes[link.source], link.source_side)
    end = anchor(boxes[link.target], link.target_side)
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=1.25,
        color=LINE,
        shrinkA=7,
        shrinkB=7,
        connectionstyle="arc3,rad=0.0",
    )
    ax.add_patch(arrow)
    if link.label:
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        ax.text(
            mid_x,
            mid_y + 0.02,
            link.label,
            ha="center",
            va="center",
            fontsize=9.5,
            color=MUTED,
            bbox={"boxstyle": "round,pad=0.25", "fc": WHITE, "ec": "none"},
        )


def setup_canvas() -> tuple[Figure, Axes]:
    fig, ax = plt.subplots(figsize=(14, 8), dpi=200)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)
    return fig, ax


def render_diagram(diagram: Diagram) -> None:
    fig, ax = setup_canvas()
    ax.text(0.04, 0.965, diagram.title, ha="left", va="top", fontsize=23, fontweight="bold", color=INK)
    ax.text(0.04, 0.875, diagram.subtitle, ha="left", va="top", fontsize=12.5, color=MUTED)
    boxes = {box.key: box for box in diagram.boxes}
    for link in diagram.links:
        draw_link(ax, boxes, link)
    for box in diagram.boxes:
        draw_box(ax, box)
    for index, note in enumerate(diagram.notes):
        ax.text(0.04, 0.06 - index * 0.032, note, ha="left", va="top", fontsize=10, color=MUTED)
    fig.savefig(IMAGE_DIR / diagram.filename, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


def ml_diagram() -> Diagram:
    return Diagram(
        filename="01_ml_구조도.png",
        title="ML 모델 병합 구조",
        subtitle="단일 모델이 아니라 역할 분리 모델을 Priority Engine에서 병합한다.",
        boxes=(
            Box("input", (0.04, 0.46), (0.17, 0.15), "10분 시계열\n기계실 센서"),
            Box("feature", (0.28, 0.46), (0.18, 0.15), "7일 window feature\ncompact13 + 품질"),
            Box("anomaly", (0.54, 0.67), (0.18, 0.13), "Anomaly\nMahalanobis\nIsolationForest"),
            Box("risk", (0.54, 0.48), (0.18, 0.13), "Risk\nLightGBM 이진"),
            Box("leadtime", (0.54, 0.29), (0.18, 0.13), "Leadtime\nLightGBM 다중"),
            Box("specialist", (0.54, 0.10), (0.18, 0.13), "M1 Specialist\nRF x3 + LR x1"),
            Box("merge", (0.79, 0.39), (0.17, 0.20), "Hybrid Priority\n0.65 current best\n0.35 specialist", ACCENT, ACCENT),
            Box("card", (0.79, 0.13), (0.17, 0.13), "Agent Card\nscore / level\nreason / action", ACCENT_3, ACCENT_3),
        ),
        links=(
            Link("input", "feature"),
            Link("feature", "anomaly"),
            Link("feature", "risk"),
            Link("feature", "leadtime"),
            Link("feature", "specialist"),
            Link("anomaly", "merge"),
            Link("risk", "merge"),
            Link("leadtime", "merge"),
            Link("specialist", "merge"),
            Link("merge", "card", "bottom", "top"),
        ),
        notes=("근거: final_validation_report.md, m1_specialist_report.md",),
    )


def db_diagram() -> Diagram:
    return Diagram(
        filename="02_db_구성도.png",
        title="Agent DB 구성",
        subtitle="자동 감지 결과, RAG 근거, 피처 설명을 운영 카드 생성에 연결한다.",
        boxes=(
            Box("raw", (0.06, 0.62), (0.24, 0.18), "1. Raw 데이터\nPreDist 기반 합성\nsensor_readings\nwindow_features"),
            Box("card", (0.38, 0.62), (0.24, 0.18), "2. 자동 감지 출력\nagent_priority_card.csv\n1226행"),
            Box("rag", (0.70, 0.62), (0.24, 0.18), "3. RAG 자료\n법규 / 날씨 / 시설\n공개자료 9종"),
            Box("guide", (0.22, 0.24), (0.24, 0.18), "4. 가이드북\n컬럼 사전\n값 매핑"),
            Box("pg", (0.54, 0.24), (0.28, 0.18), "PostgreSQL + pgvector\ncard / runs / cache\ndoc_source / doc_chunks", ACCENT, ACCENT),
        ),
        links=(
            Link("raw", "pg", "bottom", "left"),
            Link("card", "pg", "bottom", "top"),
            Link("rag", "pg", "bottom", "right"),
            Link("guide", "pg"),
        ),
        notes=("근거: db/init/02_schema.sql, 보조자료 데이터_jiyang Notion",),
    )


def agent_diagram() -> Diagram:
    return Diagram(
        filename="03_agent_구조도.png",
        title="자동 감지와 LLM 에이전트 구조",
        subtitle="OPS_GRAPH가 카드를 만들고 CARD_GRAPH가 근거를 모아 문서화한다.",
        boxes=(
            Box("ops", (0.05, 0.50), (0.22, 0.20), "OPS_GRAPH\nobserve -> record\n10 nodes"),
            Box("card", (0.36, 0.53), (0.18, 0.14), "운영 카드\npriority_score\nrecommended_action", ACCENT_3, ACCENT_3),
            Box("cardgraph", (0.63, 0.50), (0.25, 0.20), "CARD_GRAPH\nload_card -> persist\n5 nodes"),
            Box("db", (0.38, 0.20), (0.18, 0.13), "DB 조회\n과거 카드\n비용 / 티켓"),
            Box("rag", (0.62, 0.20), (0.18, 0.13), "RAG 검색\n기술기준\n책임구간"),
            Box("outputs", (0.76, 0.08), (0.18, 0.16), "산출물 4종\n카드 / 보고서\n지시서 / 알림", ACCENT, ACCENT),
        ),
        links=(
            Link("ops", "card"),
            Link("card", "cardgraph"),
            Link("db", "cardgraph", "top", "bottom"),
            Link("rag", "cardgraph", "top", "bottom"),
            Link("cardgraph", "outputs", "bottom", "top"),
        ),
        notes=("LLM 역할: 설명, 문서화, 문장 생성. 판단 후보는 룰과 ML이 담당.",),
    )


def server_diagram() -> Diagram:
    return Diagram(
        filename="04_서버_프론트_구조도.png",
        title="서버 및 프론트 권장 구조",
        subtitle="ML과 Agent 결과를 운영자가 반복 확인할 수 있는 서비스 표면으로 연결한다.",
        boxes=(
            Box("scheduler", (0.04, 0.55), (0.18, 0.15), "스케줄러\nreplay tick\n주기 실행"),
            Box("api", (0.29, 0.53), (0.22, 0.19), "FastAPI Backend\n/cards / actions\n/rag / replay / ws", ACCENT_3, ACCENT_3),
            Box("front", (0.75, 0.53), (0.18, 0.19), "React Front\n운영 카드\nRAG 검색\n티켓"),
            Box("db", (0.57, 0.28), (0.20, 0.16), "PostgreSQL\nagent_priority_card\nagent_runs"),
            Box("llm", (0.80, 0.28), (0.16, 0.16), "LLM API\ncache + budget\nfallback template"),
            Box("rag", (0.29, 0.24), (0.22, 0.14), "RAG Pipeline\ndoc_source\ndoc_chunks"),
        ),
        links=(
            Link("scheduler", "api"),
            Link("api", "front", "right", "left", "REST / WebSocket"),
            Link("api", "db", "bottom", "top"),
            Link("api", "llm", "right", "top"),
            Link("rag", "api", "top", "bottom"),
        ),
        notes=("근거: docker-compose.yml, api/app.py, frontend/src/api/client.ts, db/init/02_schema.sql",),
    )


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False
    for diagram in (ml_diagram(), db_diagram(), agent_diagram(), server_diagram()):
        render_diagram(diagram)


if __name__ == "__main__":
    main()
