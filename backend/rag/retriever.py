"""FAISS retrieval with an explicit NumPy fallback only when FAISS is unavailable."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from rag.schemas import RetrievedChunk

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - exercised in environments without FAISS.
    faiss = None


class VectorIndex:
    def __init__(self) -> None:
        self.matrix = np.zeros((0, 1), dtype=np.float32)
        self.records: list[dict] = []
        self.backend = "empty"
        self._faiss = None

    def build(self, vectors: np.ndarray, records: list[dict]) -> str:
        self.records = records
        if len(records) == 0:
            self.matrix = np.zeros((0, 1), dtype=np.float32)
            self.backend = "empty"
            self._faiss = None
            return self.backend

        self.matrix = np.ascontiguousarray(vectors.astype(np.float32))
        if faiss is not None:
            index = faiss.IndexFlatIP(self.matrix.shape[1])
            index.add(self.matrix)
            self._faiss = index
            self.backend = "faiss"
            return self.backend

        self._faiss = None
        self.backend = "numpy"
        return self.backend

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        np.save(directory / "vectors.npy", self.matrix)
        if self._faiss is not None and faiss is not None:
            faiss.write_index(self._faiss, str(directory / "index.faiss"))

    def search(self, query: np.ndarray, limit: int) -> list[tuple[int, float]]:
        if not self.records:
            return []
        query = np.ascontiguousarray(query.astype(np.float32).reshape(1, -1))
        k = min(limit, len(self.records))
        if self._faiss is not None and faiss is not None:
            scores, ids = self._faiss.search(query, k)
            pairs = []
            for score, index in zip(scores[0], ids[0]):
                if index < 0:
                    continue
                pairs.append((int(index), float(score)))
            return pairs
        scores = (self.matrix @ query[0]).tolist()
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        return [(index, float(score)) for index, score in ranked[:k]]


def passes_filters(record: dict, filters: dict | None) -> bool:
    if not filters:
        return True
    prefix = filters.get("source_prefix")
    if prefix and not str(record.get("source", "")).startswith(prefix):
        return False
    for key in ("category", "language", "document_type"):
        expected = filters.get(key)
        if expected and str(record.get(key, "")).lower() != str(expected).lower():
            return False
    return True


def to_chunk(record: dict, embedding_score: float) -> RetrievedChunk:
    return RetrievedChunk(
        record_id=record["record_id"],
        chunk_id=record["chunk_id"],
        title=record["title"],
        content=record["content"],
        source=record["source"],
        source_url=record.get("source_url", ""),
        section=record.get("section", ""),
        category=record.get("category", ""),
        language=record.get("language", "en"),
        document_type=record.get("document_type", ""),
        version=record.get("version", "1.0"),
        score=embedding_score,
        embedding_score=embedding_score,
    )
