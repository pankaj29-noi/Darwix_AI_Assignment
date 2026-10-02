"""HTTP and WebSocket routes."""

from __future__ import annotations

import asyncio
import json
from uuid import uuid4

from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.config import PROJECT_ROOT
from app.database import utc_now
from multilingual.indonesia import ACCENT_TEST, load_config as load_indonesia
from multilingual.philippines import load_config as load_philippines
from rag.evaluation import run_evaluation
from realtime.pipeline import load_scenarios

class IngestIn(BaseModel):
    path: str = ""


class SearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=10)
    category: str | None = None
    source_prefix: str | None = None
    language: str | None = None


class SessionIn(BaseModel):
    use_case: str = "health"


class MessageIn(BaseModel):
    call_id: str = Field(min_length=4, max_length=80)
    text: str = Field(min_length=1, max_length=4000)


class ChunkIn(BaseModel):
    call_id: str
    speaker: str = "customer"
    text: str = Field(min_length=1, max_length=4000)
    t_ms: int = 0


class ReplayIn(BaseModel):
    call_id: str
    scenario: str = "full_demo"
    speed: float = Field(default=1.0, ge=0, le=20)


def _filters(body: SearchIn) -> dict:
    filters = {}
    if body.category:
        filters["category"] = body.category
    if body.source_prefix:
        filters["source_prefix"] = body.source_prefix
    if body.language:
        filters["language"] = body.language
    return filters


def register(app) -> None:
    @app.get("/health")
    def health():
        settings = app.state.settings
        kb = app.state.kb
        return {
            "status": "ok",
            "llm_mode": settings.llm_mode,
            "asr_mode": settings.asr_mode,
            "tts_mode": settings.tts_mode,
            "voice_mode": settings.voice_mode,
            "embedding_mode": kb.embedder.name,
            "vector_index": kb.index.backend,
            "mock_notice": (
                "LLM, ASR, TTS, and telephony are in labeled local/mock mode unless a live "
                "credential is configured. This web session is not a phone call."
                if settings.llm_mode == "mock"
                else "Live LLM mode is configured. ASR/TTS/telephony follow their own credentials."
            ),
        }

    @app.post("/kb/ingest")
    def ingest(_: IngestIn):
        report = app.state.kb.ingest_directory(app.state.settings.knowledge_path)
        return report

    @app.post("/kb/search")
    def search(body: SearchIn):
        result = app.state.kb.answer(body.query, top_k=body.top_k, filters=_filters(body) or None)
        return result.model_dump()

    @app.get("/kb/records")
    def records():
        return {"records": app.state.db.list_knowledge()}

    @app.post("/voice/session")
    def voice_session(body: SessionIn):
        try:
            return app.state.orchestrator.start(body.use_case)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/voice/message")
    def voice_message(body: MessageIn):
        try:
            return app.state.orchestrator.handle(body.call_id, body.text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/voice/scenario")
    def voice_scenario(body: SessionIn, scenario: str = "cooperative"):
        path = PROJECT_ROOT / "data" / "voice" / "scenarios.json"
        scenarios = json.loads(path.read_text(encoding="utf-8"))
        key = f"{body.use_case}:{scenario}"
        if key not in scenarios:
            raise HTTPException(status_code=404, detail=f"Unknown scenario {key}")
        started = app.state.orchestrator.start(body.use_case)
        turns = [{"speaker": "agent", "text": started["message"], "state": started["state"]}]
        latest = started
        for text in scenarios[key]["turns"]:
            latest = app.state.orchestrator.handle(started["call_id"], text)
            turns.append({"speaker": "customer", "text": text, "state": latest["state"]})
            turns.append(
                {
                    "speaker": "agent",
                    "text": latest["message"],
                    "state": latest["state"],
                    "sources": latest.get("sources", []),
                    "fallback": latest.get("fallback", False),
                }
            )
        return {"scenario": key, "call": latest, "turns": turns}

    @app.get("/calls/{call_id}")
    def get_call(call_id: str):
        call = app.state.db.get_call(call_id)
        if call is None:
            raise HTTPException(status_code=404, detail="Call not found")
        return call

    @app.get("/calls/{call_id}/transcript")
    def get_transcript(call_id: str):
        call = app.state.db.get_call(call_id)
        if call is None:
            raise HTTPException(status_code=404, detail="Call not found")
        return {"call_id": call_id, "turns": app.state.db.get_transcript(call_id)}

    @app.get("/evaluation")
    def evaluation():
        payload = run_evaluation(app.state.kb)
        app.state.db.save_evaluation("rag", payload)
        path = app.state.settings.results_path / "rag_evaluation.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    @app.get("/latency")
    def latency():
        path = app.state.settings.results_path / "latency_results.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        call_id = uuid4().hex
        now = utc_now()
        app.state.db.upsert_call(
            {
                "id": call_id,
                "use_case": "realtime",
                "state": "LIVE",
                "status": "measured",
                "qualification_json": "{}",
                "summary": "",
                "escalated": 0,
                "mode": "mock_web",
                "crm_json": "null",
                "created_at": now,
                "updated_at": now,
            }
        )
        measured = app.state.pipeline.replay("full_demo", call_id, speed=0)
        payload = {
            "measured": True,
            "scenario": "full_demo",
            "latency": measured["latency"],
            "nudge_count": measured["nudge_count"],
            "signal_count": measured["signal_count"],
            "note": "Measured inside this process at replay speed 0. Cloud ASR and LLM latencies are NOT MEASURED.",
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    @app.get("/multilingual/philippines")
    def philippines_config():
        return load_philippines()

    @app.get("/multilingual/indonesia")
    def indonesia_config():
        config = load_indonesia()
        config["accent_test"] = ACCENT_TEST
        return config

    @app.get("/multilingual/indonesia/accent-test")
    def accent_test():
        return ACCENT_TEST

    @app.get("/realtime/scenarios")
    def scenarios():
        return load_scenarios()

    @app.post("/realtime/session")
    def realtime_session():
        call_id = uuid4().hex
        now = utc_now()
        app.state.db.upsert_call(
            {
                "id": call_id,
                "use_case": "realtime",
                "state": "LIVE",
                "status": "live",
                "qualification_json": "{}",
                "summary": "",
                "escalated": 0,
                "mode": app.state.settings.voice_mode,
                "crm_json": "null",
                "created_at": now,
                "updated_at": now,
            }
        )
        return {"call_id": call_id, "status": "live", "mode": "streaming_replay"}

    @app.post("/realtime/chunk")
    async def realtime_chunk(body: ChunkIn):
        if body.speaker not in {"agent", "customer", "unknown"}:
            raise HTTPException(status_code=400, detail="speaker must be agent, customer, or unknown")
        result = app.state.pipeline.process_chunk(body.call_id, body.speaker, body.text, body.t_ms)
        await app.state.hub.publish(body.call_id, result)
        return result

    @app.post("/realtime/replay")
    async def realtime_replay(body: ReplayIn):
        scenarios_map = load_scenarios()
        if body.scenario not in scenarios_map:
            raise HTTPException(status_code=404, detail="Unknown scenario")
        turns = scenarios_map[body.scenario]["turns"]

        async def run() -> None:
            previous = 0
            for turn in turns:
                offset = int(turn.get("t_ms", 0))
                if body.speed > 0:
                    await asyncio.sleep(max(0, (offset - previous) / 1000) / body.speed)
                previous = offset
                result = app.state.pipeline.process_chunk(
                    body.call_id, turn["speaker"], turn["text"], offset
                )
                await app.state.hub.publish(body.call_id, result)
            await app.state.hub.publish(
                body.call_id,
                {"type": "replay_complete", "call_id": body.call_id, "scenario": body.scenario},
            )

        asyncio.create_task(run())
        return {"started": True, "call_id": body.call_id, "scenario": body.scenario, "speed": body.speed}

    @app.websocket("/ws/realtime/{call_id}")
    async def websocket_endpoint(websocket: WebSocket, call_id: str):
        await websocket.accept()
        queue = app.state.hub.subscribe(call_id)
        for event in app.state.hub.history.get(call_id, []):
            await websocket.send_json(event)

        async def writer() -> None:
            while True:
                event = await queue.get()
                await websocket.send_json(event)

        writer_task = asyncio.create_task(writer())
        try:
            while True:
                incoming = await websocket.receive_json()
                if incoming.get("type") != "chunk":
                    continue
                result = app.state.pipeline.process_chunk(
                    call_id,
                    incoming.get("speaker", "customer"),
                    incoming.get("text", ""),
                    int(incoming.get("t_ms", 0)),
                )
                await app.state.hub.publish(call_id, result)
        except WebSocketDisconnect:
            pass
        finally:
            writer_task.cancel()
            app.state.hub.unsubscribe(call_id, queue)
