from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    title: str
    breadcrumb: str
    content: str


def chunk_text(title: str, breadcrumb: str, text: str, size: int = 800, overlap: int = 120) -> list[TextChunk]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks: list[TextChunk] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + size)
        chunks.append(TextChunk(title=title, breadcrumb=breadcrumb, content=normalized[start:end]))
        if end == len(normalized):
            break
        start = max(0, end - overlap)
    return chunks
