"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Database
from app.routes import register
from providers.asr import build_asr
from providers.llm import build_llm
from providers.tts import build_tts
from providers.voice import build_voice
from rag.service import KnowledgeBase
from realtime.hub import Hub
from realtime.pipeline import RealtimePipeline
from voice.orchestrator import VoiceOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("darwix")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Darwix AI Voice Intelligence Platform")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    database = Database(settings.database_path)
    knowledge = KnowledgeBase(database, settings.vector_path, settings)
    if settings.auto_ingest:
        knowledge.ingest_directory(settings.knowledge_path)
    llm = build_llm(settings.llm_provider, settings.llm_api_key, settings.llm_model, settings.llm_base_url)
    voice = build_voice(settings.voice_provider, settings.voice_api_key)
    asr = build_asr(settings.asr_provider, settings.asr_api_key)
    tts = build_tts(settings.tts_provider, settings.tts_api_key)
    app.state.settings = settings
    app.state.db = database
    app.state.kb = knowledge
    app.state.llm = llm
    app.state.tts = tts
    app.state.hub = Hub()
    app.state.pipeline = RealtimePipeline(
        database,
        asr=asr,
        threshold=settings.nudge_confidence_threshold,
        cooldown_s=settings.nudge_cooldown_seconds,
    )
    app.state.orchestrator = VoiceOrchestrator(knowledge, database, voice, llm=llm)
    register(app)
    return app
