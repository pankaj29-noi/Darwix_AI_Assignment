"""Knowledge-base value objects."""

from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeRecord(BaseModel):
    record_id: str
    title: str
    content: str
    category: str
    source: str
    source_url: str = ""
    section: str = ""
    version: str = "1.0"
    created_at: str
    updated_at: str
    pii: bool = False
    language: str = "en"
    document_type: str = "policy"
    chunk_id: str
    hash: str


class RetrievedChunk(BaseModel):
    record_id: str
    chunk_id: str
    title: str
    content: str
    source: str
    source_url: str = ""
    section: str = ""
    category: str = ""
    language: str = "en"
    document_type: str = ""
    version: str = "1.0"
    score: float
    embedding_score: float = 0.0
    lexical_score: float = 0.0


class GroundedAnswer(BaseModel):
    answer: str
    confidence: float
    sources: list[dict] = Field(default_factory=list)
    retrieved_chunks: list[dict] = Field(default_factory=list)
    fallback: bool = False
    fallback_reason: str = ""
    generation_mode: str = "extractive"


FALLBACK_EN = (
    "I don't have verified information about that in my knowledge base. "
    "I can connect you with a human representative."
)
