"""Shared fixtures. Each test gets its own SQLite file and vector index."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'app.db'}")
    monkeypatch.setenv("VECTOR_DB_PATH", str(tmp_path / "vector"))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "tfidf")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("ASR_PROVIDER", "mock")
    monkeypatch.setenv("TTS_PROVIDER", "mock")
    monkeypatch.setenv("VOICE_PROVIDER", "mock")
    monkeypatch.setenv("AUTO_INGEST", "true")
    from app.config import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    application = create_app()
    yield application
    get_settings.cache_clear()


@pytest.fixture()
def client(app):
    return TestClient(app)
