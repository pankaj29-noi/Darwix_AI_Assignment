"""Ingest documents and answer questions from the local index."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.database import Database
from rag.chunking import chunk_text
from rag.cleaning import clean_text, flag_extraction_issues, jaccard, shingles
from rag.embeddings import build_embedder
from rag.generator import generate
from rag.ingestion import discover_files, load_file
from rag.pii import redact
from rag.reranker import rerank
from rag.retriever import VectorIndex, passes_filters, to_chunk
from rag.schemas import FALLBACK_EN, GroundedAnswer
from rag.textutil import content_hash

NEAR_DUP = 0.75


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class KnowledgeBase:
    def __init__(self, database: Database, vector_dir: Path, settings):
        self.database = database
        self.vector_dir = Path(vector_dir)
        self.settings = settings
        self.embedder = build_embedder(settings.embedding_provider)
        self.index = VectorIndex()
        self.records: list[dict] = []
        self.ingest_report: dict = {}

    def ingest_directory(self, root: Path) -> dict:
        root = Path(root)
        accepted_text: list[tuple[str, set]] = []
        drafts: list[dict] = []
        report = {
            "indexed_files": [],
            "skipped_duplicates": [],
            "skipped_extraction": [],
            "pii_flagged": [],
            "embedding_model": self.embedder.name,
        }
        now = _now()
        for path in discover_files(root):
            relative = path.relative_to(root).as_posix()
            loaded = load_file(path, relative)
            if loaded.rows:
                self._add_rows(loaded, relative, now, drafts, report)
                continue
            issues = list(loaded.issues)
            cleaned = clean_text(loaded.text)
            issues.extend(flag_extraction_issues(cleaned))
            if "extraction_too_short" in issues or any(item.startswith("extraction_failed") for item in issues) or "extraction_empty_pdf" in issues:
                report["skipped_extraction"].append({"source": relative, "issues": issues})
                continue
            signature = shingles(cleaned)
            duplicate_of = None
            for previous, previous_signature in accepted_text:
                if jaccard(signature, previous_signature) >= NEAR_DUP:
                    duplicate_of = previous
                    break
            if duplicate_of:
                report["skipped_duplicates"].append({"source": relative, "duplicate_of": duplicate_of})
                continue
            accepted_text.append((relative, signature))
            redacted, has_pii, pii_types = redact(cleaned)
            if has_pii:
                report["pii_flagged"].append({"source": relative, "types": pii_types})
            meta = loaded.metadata
            base_id = meta.get("record_id") or f"kb_{path.stem}"
            chunks = chunk_text(
                redacted,
                chunk_size=self.settings.chunk_size,
                overlap=self.settings.chunk_overlap,
                default_section=meta.get("section") or "Body",
            )
            for chunk in chunks:
                record_id = f"{base_id}_c{chunk.index + 1:03d}"
                drafts.append(
                    {
                        "record_id": record_id,
                        "title": meta.get("title") or loaded.title,
                        "content": chunk.text,
                        "category": meta.get("category", "general"),
                        "source": relative,
                        "source_url": meta.get("source_url", ""),
                        "section": chunk.section,
                        "version": meta.get("version", "1.0"),
                        "created_at": now,
                        "updated_at": now,
                        "pii": int(has_pii),
                        "language": meta.get("language", "en"),
                        "document_type": meta.get("document_type", "policy"),
                        "chunk_id": f"chunk_{chunk.index + 1:03d}",
                        "hash": content_hash(chunk.text),
                    }
                )
            report["indexed_files"].append(relative)
        self._finalize(drafts, report)
        return report

    def _add_rows(self, loaded, relative: str, now: str, drafts: list[dict], report: dict) -> None:
        if not loaded.rows:
            report["skipped_extraction"].append({"source": relative, "issues": ["empty_csv"]})
            return
        for index, row in enumerate(loaded.rows, start=1):
            content = clean_text(row.get("content") or "")
            if not content:
                continue
            redacted, has_pii, pii_types = redact(content)
            base_id = row.get("record_id") or f"kb_{Path(relative).stem}_{index:03d}"
            drafts.append(
                {
                    "record_id": f"{base_id}_c001",
                    "title": row.get("title") or base_id,
                    "content": redacted,
                    "category": row.get("category") or "general",
                    "source": relative,
                    "source_url": row.get("source_url") or "",
                    "section": row.get("section") or "Table",
                    "version": row.get("version") or "1.0",
                    "created_at": now,
                    "updated_at": now,
                    "pii": int(has_pii),
                    "language": row.get("language") or "en",
                    "document_type": row.get("document_type") or "table",
                    "chunk_id": "chunk_001",
                    "hash": content_hash(redacted),
                }
            )
            if has_pii:
                report["pii_flagged"].append({"source": relative, "types": pii_types})
        report["indexed_files"].append(relative)

    def _finalize(self, drafts: list[dict], report: dict) -> None:
        texts = [item["content"] for item in drafts]
        vectors = self.embedder.fit_transform(texts) if texts else None
        if vectors is not None:
            backend = self.index.build(vectors, drafts)
        else:
            backend = self.index.build(
                __import__("numpy").zeros((0, 1), dtype="float32"),
                [],
            )
        self.records = drafts
        self.database.replace_knowledge([{**item, "pii": int(item["pii"])} for item in drafts])
        self.index.save(self.vector_dir)
        manifest = {
            "embedding_model": self.embedder.name,
            "vector_backend": backend,
            "records": len(drafts),
            "vocab": getattr(self.embedder, "vocab", {}),
        }
        # Vocab can be large; store only the size for the manifest.
        manifest["vocab_size"] = len(getattr(self.embedder, "vocab", {}) or {})
        manifest.pop("vocab")
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        (self.vector_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        report["vector_backend"] = backend
        report["records"] = len(drafts)
        self.ingest_report = report

    def search(self, query: str, top_k: int | None = None, filters: dict | None = None) -> list:
        limit = top_k or self.settings.top_k
        if not query.strip() or not self.records:
            return []
        query_vector = self.embedder.transform([query])[0]
        pool = self.index.search(query_vector, limit=max(limit * 4, limit))
        chunks = []
        for index, score in pool:
            record = self.records[index]
            if not passes_filters(record, filters):
                continue
            chunks.append(to_chunk(record, score))
        return rerank(query, chunks, limit)

    def answer(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict | None = None,
        fallback_message: str = FALLBACK_EN,
        call_id: str | None = None,
        llm=None,
        system_prompt: str = "",
    ) -> GroundedAnswer:
        chunks = self.search(query, top_k=top_k, filters=filters)
        result = generate(
            query,
            chunks,
            threshold=self.settings.confidence_threshold,
            fallback_message=fallback_message,
            llm=llm,
            system_prompt=system_prompt,
        )
        self.database.log_retrieval(
            call_id,
            query,
            result.model_dump(),
            result.confidence,
            result.fallback,
            result.fallback_reason,
        )
        return result
