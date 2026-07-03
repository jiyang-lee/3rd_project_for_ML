from __future__ import annotations

from dataclasses import dataclass

from ..config import get_settings

EmbeddingVector = list[float] | None


@dataclass(frozen=True, slots=True)
class LocalEmbedder:
    model_name: str

    def embed(self, texts: list[str]) -> list[EmbeddingVector]:
        try:
            from sentence_transformers import SentenceTransformer
        except ModuleNotFoundError as exc:
            if exc.name != "sentence_transformers":
                raise
            return [None for _ in texts]

        model = SentenceTransformer(self.model_name)
        vectors = model.encode(texts, normalize_embeddings=True)
        return [[float(value) for value in row] for row in vectors]


def get_embedder() -> LocalEmbedder:
    return LocalEmbedder(model_name=get_settings().embedding_model)
