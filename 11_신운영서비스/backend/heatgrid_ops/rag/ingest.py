from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

from ..config import ensure_allowed_input_path, get_settings
from ..db import get_pool
from .chunker import TextChunk, chunk_text
from .embedder import get_embedder


@dataclass(frozen=True)
class SourceDocument:
    path: Path
    title: str
    source_type: str
    text: str


def html_text(path: Path) -> str:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    return soup.get_text("\n")


def pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(parts).strip()
    if len(text) < 200:
        return f"drawing_reference: {path.stem}"
    return text


def iter_sources(root: Path) -> list[SourceDocument]:
    ensure_allowed_input_path(root)
    documents: list[SourceDocument] = []
    for path in sorted(root.rglob("*")):
        suffix = path.suffix.lower()
        if suffix == ".html":
            documents.append(SourceDocument(path=path, title=path.stem, source_type="html", text=html_text(path)))
        elif suffix == ".pdf":
            documents.append(SourceDocument(path=path, title=path.stem, source_type="pdf", text=pdf_text(path)))
    return documents


def build_chunks(root: Path) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for doc in iter_sources(root):
        rel = str(doc.path.relative_to(root))
        chunks.extend(chunk_text(doc.title, rel, doc.text))
    return chunks


async def ingest_chunks(chunks: list[TextChunk]) -> int:
    settings = get_settings()
    embedder = get_embedder()
    texts = [chunk.content for chunk in chunks]
    vectors = embedder.embed(texts)
    first_vector = next((vector for vector in vectors if vector is not None), None)
    if first_vector is not None and len(first_vector) != settings.embedding_dim:
        raise RuntimeError(f"embedding dim mismatch: {len(first_vector)} != {settings.embedding_dim}")
    pool = await get_pool()
    async with pool.acquire() as conn:
        inserted = 0
        for chunk, vector in zip(chunks, vectors, strict=True):
            source_id = await conn.fetchval(
                "INSERT INTO doc_source (path, title, source_type) VALUES ($1, $2, $3) "
                "ON CONFLICT (path) DO UPDATE SET title = EXCLUDED.title RETURNING source_id",
                chunk.breadcrumb,
                chunk.title,
                "document",
            )
            await conn.execute(
                "INSERT INTO doc_chunks (source_id, title, breadcrumb, content, embedding) VALUES ($1, $2, $3, $4, $5)",
                source_id,
                chunk.title,
                chunk.breadcrumb,
                chunk.content,
                vector,
            )
            inserted += 1
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    chunks = build_chunks(settings.subdataset_dir)
    if args.dry_run:
        print(f"chunks={len(chunks)}")
        for chunk in chunks[:5]:
            print(f"- {chunk.breadcrumb}: {chunk.content[:80]}")
        return
    import anyio

    inserted = anyio.run(ingest_chunks, chunks)
    print(f"inserted={inserted}")


if __name__ == "__main__":
    main()
