"""Text helpers shared by cleaning, chunking, and retrieval."""

from __future__ import annotations

import hashlib
import re

STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "of",
    "for",
    "to",
    "and",
    "in",
    "on",
    "with",
    "that",
    "this",
    "my",
    "i",
    "you",
    "we",
    "our",
    "are",
    "be",
    "or",
    "if",
    "it",
    "as",
    "at",
    "by",
    "from",
    "was",
    "were",
    "will",
    "can",
    "do",
    "does",
    "what",
    "how",
    "when",
    "which",
    "who",
    "whom",
    "your",
    "their",
    "they",
    "me",
    "about",
    "into",
    "should",
    "please",
}


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower())


def content_tokens(text: str) -> list[str]:
    return [token for token in tokenize(text) if token not in STOPWORDS and len(token) > 1]


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]
