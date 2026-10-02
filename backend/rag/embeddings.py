"""Embedding providers.

Default: TF-IDF vectors stored in FAISS.
Optional: sentence-transformers MiniLM when that package is installed and
EMBEDDING_PROVIDER=sentence-transformers.
"""

from __future__ import annotations

import math
from collections import Counter

import numpy as np

from rag.textutil import content_tokens


class TfidfEmbedder:
    name = "tfidf"

    def __init__(self) -> None:
        self.vocab: dict[str, int] = {}
        self.idf: np.ndarray | None = None

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        docs = [content_tokens(text) for text in texts]
        df: Counter[str] = Counter()
        for tokens in docs:
            df.update(set(tokens))
        terms = sorted(df)
        self.vocab = {term: index for index, term in enumerate(terms)}
        count = max(1, len(docs))
        self.idf = np.asarray(
            [math.log((1 + count) / (1 + df[term])) + 1.0 for term in terms],
            dtype=np.float32,
        )
        if not terms:
            return np.zeros((len(texts), 1), dtype=np.float32)
        return self._vectors(docs)

    def transform(self, texts: list[str]) -> np.ndarray:
        docs = [content_tokens(text) for text in texts]
        if not self.vocab:
            return np.zeros((len(texts), 1), dtype=np.float32)
        return self._vectors(docs)

    def _vectors(self, docs: list[list[str]]) -> np.ndarray:
        matrix = np.zeros((len(docs), len(self.vocab)), dtype=np.float32)
        assert self.idf is not None
        for row, tokens in enumerate(docs):
            if not tokens:
                continue
            counts = Counter(tokens)
            for token, freq in counts.items():
                index = self.vocab.get(token)
                if index is None:
                    continue
                matrix[row, index] = (1.0 + math.log(freq)) * float(self.idf[index])
            norm = np.linalg.norm(matrix[row])
            if norm > 0:
                matrix[row] /= norm
        return matrix


class SentenceTransformerEmbedder:
    """Dense MiniLM embeddings. Constructing this imports sentence-transformers."""

    name = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        return self.transform(texts)

    def transform(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return np.asarray(vectors, dtype=np.float32)


def build_embedder(provider: str):
    if provider == "sentence-transformers":
        return SentenceTransformerEmbedder()
    if provider != "tfidf":
        raise ValueError(f"Unknown EMBEDDING_PROVIDER '{provider}'")
    return TfidfEmbedder()
