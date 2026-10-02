"""SQLite persistence for local development."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_records (
    record_id TEXT PRIMARY KEY,
    title TEXT,
    content TEXT,
    category TEXT,
    source TEXT,
    source_url TEXT,
    section TEXT,
    version TEXT,
    created_at TEXT,
    updated_at TEXT,
    pii INTEGER,
    language TEXT,
    document_type TEXT,
    chunk_id TEXT,
    hash TEXT
);
CREATE TABLE IF NOT EXISTS calls (
    id TEXT PRIMARY KEY,
    use_case TEXT,
    state TEXT,
    status TEXT,
    qualification_json TEXT,
    summary TEXT,
    escalated INTEGER,
    mode TEXT,
    crm_json TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT,
    speaker TEXT,
    text TEXT,
    ts TEXT,
    offset_ms INTEGER
);
CREATE TABLE IF NOT EXISTS retrieval_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT,
    question TEXT,
    result_json TEXT,
    confidence REAL,
    fallback INTEGER,
    fallback_reason TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id TEXT,
    call_id TEXT,
    timestamp TEXT,
    type TEXT,
    severity TEXT,
    confidence REAL,
    evidence TEXT,
    recommended_action TEXT,
    expires_at TEXT
);
CREATE TABLE IF NOT EXISTS nudges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nudge_id TEXT,
    call_id TEXT,
    signal_id TEXT,
    timestamp TEXT,
    text TEXT,
    priority INTEGER,
    confidence REAL,
    evidence TEXT,
    topic TEXT,
    expires_at TEXT
);
CREATE TABLE IF NOT EXISTS latency_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT,
    chunk_index INTEGER,
    asr_ms REAL,
    signal_ms REAL,
    llm_ms TEXT,
    nudge_ms REAL,
    delivery_ms REAL,
    e2e_ms REAL,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS evaluation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suite TEXT,
    payload_json TEXT,
    created_at TEXT
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.executescript(SCHEMA)
            self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def replace_knowledge(self, records: list[dict[str, Any]]) -> None:
        with self._lock:
            self.conn.execute("DELETE FROM knowledge_records")
            self.conn.executemany(
                """
                INSERT INTO knowledge_records (
                    record_id, title, content, category, source, source_url, section,
                    version, created_at, updated_at, pii, language, document_type,
                    chunk_id, hash
                ) VALUES (
                    :record_id, :title, :content, :category, :source, :source_url, :section,
                    :version, :created_at, :updated_at, :pii, :language, :document_type,
                    :chunk_id, :hash
                )
                """,
                records,
            )
            self.conn.commit()

    def list_knowledge(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM knowledge_records ORDER BY record_id"
            ).fetchall()
        return [self._record(row) for row in rows]

    def _record(self, row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["pii"] = bool(item["pii"])
        return item

    def upsert_call(self, call: dict[str, Any]) -> None:
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO calls (
                    id, use_case, state, status, qualification_json, summary,
                    escalated, mode, crm_json, created_at, updated_at
                ) VALUES (
                    :id, :use_case, :state, :status, :qualification_json, :summary,
                    :escalated, :mode, :crm_json, :created_at, :updated_at
                )
                ON CONFLICT(id) DO UPDATE SET
                    state=excluded.state,
                    status=excluded.status,
                    qualification_json=excluded.qualification_json,
                    summary=excluded.summary,
                    escalated=excluded.escalated,
                    crm_json=excluded.crm_json,
                    updated_at=excluded.updated_at
                """,
                call,
            )
            self.conn.commit()

    def get_call(self, call_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["escalated"] = bool(item["escalated"])
        item["qualification"] = json.loads(item.pop("qualification_json") or "{}")
        item["crm"] = json.loads(item.pop("crm_json") or "null")
        return item

    def add_transcript(
        self, call_id: str, speaker: str, text: str, offset_ms: int | None = None
    ) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT INTO transcripts (call_id, speaker, text, ts, offset_ms) VALUES (?, ?, ?, ?, ?)",
                (call_id, speaker, text, utc_now(), offset_ms),
            )
            self.conn.commit()

    def get_transcript(self, call_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT speaker, text, ts, offset_ms FROM transcripts WHERE call_id = ? ORDER BY id",
                (call_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def log_retrieval(
        self,
        call_id: str | None,
        question: str,
        result: dict[str, Any],
        confidence: float,
        fallback: bool,
        reason: str,
    ) -> None:
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO retrieval_logs (
                    call_id, question, result_json, confidence, fallback, fallback_reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id or "",
                    question,
                    json.dumps(result),
                    confidence,
                    int(fallback),
                    reason,
                    utc_now(),
                ),
            )
            self.conn.commit()

    def add_signal(self, call_id: str, signal: dict[str, Any]) -> None:
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO signals (
                    signal_id, call_id, timestamp, type, severity, confidence, evidence,
                    recommended_action, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal["signal_id"],
                    call_id,
                    signal["timestamp"],
                    signal["type"],
                    signal["severity"],
                    signal["confidence"],
                    signal["evidence"],
                    signal["recommended_action"],
                    signal["expires_at"],
                ),
            )
            self.conn.commit()

    def add_nudge(self, call_id: str, nudge: dict[str, Any]) -> None:
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO nudges (
                    nudge_id, call_id, signal_id, timestamp, text, priority, confidence,
                    evidence, topic, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    nudge["nudge_id"],
                    call_id,
                    nudge["signal_id"],
                    nudge["timestamp"],
                    nudge["text"],
                    nudge["priority"],
                    nudge["confidence"],
                    nudge["evidence"],
                    nudge.get("topic", ""),
                    nudge["expires_at"],
                ),
            )
            self.conn.commit()

    def add_latency(self, call_id: str, chunk_index: int, metrics: dict[str, Any]) -> None:
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO latency_metrics (
                    call_id, chunk_index, asr_ms, signal_ms, llm_ms, nudge_ms,
                    delivery_ms, e2e_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    chunk_index,
                    metrics.get("asr_ms"),
                    metrics.get("signal_ms"),
                    str(metrics.get("llm_ms")),
                    metrics.get("nudge_ms"),
                    metrics.get("delivery_ms"),
                    metrics.get("e2e_ms"),
                    utc_now(),
                ),
            )
            self.conn.commit()

    def save_evaluation(self, suite: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT INTO evaluation_results (suite, payload_json, created_at) VALUES (?, ?, ?)",
                (suite, json.dumps(payload), utc_now()),
            )
            self.conn.commit()

    def table_names(self) -> list[str]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        return [row["name"] for row in rows]
