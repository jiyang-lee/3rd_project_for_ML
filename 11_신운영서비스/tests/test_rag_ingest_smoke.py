from __future__ import annotations

from pathlib import Path

import pytest

from heatgrid_ops.rag.embedder import LocalEmbedder
from heatgrid_ops.rag.chunker import chunk_text
from heatgrid_ops.rag.ingest import html_text

HTML_PATH = (
    Path(__file__).resolve().parents[2]
    / "13_서브데이터셋"
    / "02_kdhc_responsibility"
    / "kdhc_user_responsibility_scope.html"
)


def test_chunk_text_overlaps_long_text() -> None:
    chunks = chunk_text("title", "crumb", "가" * 2000, size=800, overlap=120)
    assert len(chunks) == 3
    assert chunks[0].title == "title"


def test_embedder_allows_text_ingest_without_optional_model_dependency() -> None:
    embedder = LocalEmbedder(model_name="missing-model")

    assert embedder.embed(["책임 범위"]) == [None]


@pytest.mark.skipif(not HTML_PATH.exists(), reason="responsibility HTML not available")
def test_responsibility_html_can_be_read() -> None:
    text = html_text(HTML_PATH)
    assert "책임" in text or "사용자" in text
