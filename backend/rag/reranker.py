"""Blend embedding similarity with lexical overlap."""

from __future__ import annotations

from rag.cleaning import jaccard, shingles
from rag.schemas import RetrievedChunk


def rerank(query: str, chunks: list[RetrievedChunk], limit: int) -> list[RetrievedChunk]:
    query_shingles = shingles(query)
    ranked: list[RetrievedChunk] = []
    for chunk in chunks:
        lexical = jaccard(query_shingles, shingles(chunk.content))
        blended = (0.8 * chunk.embedding_score) + (0.2 * lexical)
        ranked.append(chunk.model_copy(update={"lexical_score": lexical, "score": blended}))
    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:limit]
