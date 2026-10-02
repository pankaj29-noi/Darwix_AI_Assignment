"""Streaming call pipeline used by the WebSocket and the replay script."""

from __future__ import annotations

import json
import time
from pathlib import Path

from app.config import PROJECT_ROOT
from providers.asr import MockASR
from realtime.latency import summarize
from realtime.nudges import NudgeEngine
from realtime.signals import SignalDetector


def load_scenarios() -> dict:
    path = PROJECT_ROOT / "data" / "realtime" / "scenarios.json"
    return json.loads(path.read_text(encoding="utf-8"))


class RealtimePipeline:
    def __init__(self, database, asr=None, threshold: float = 0.62, cooldown_s: float = 45):
        self.db = database
        self.asr = asr or MockASR()
        self.detector = SignalDetector()
        self.engines: dict[str, NudgeEngine] = {}
        self.threshold = threshold
        self.cooldown_s = cooldown_s
        self.chunk_counts: dict[str, int] = {}

    def engine(self, call_id: str) -> NudgeEngine:
        if call_id not in self.engines:
            self.engines[call_id] = NudgeEngine(self.threshold, self.cooldown_s)
        return self.engines[call_id]

    def process_chunk(self, call_id: str, speaker: str, text: str, offset_ms: int = 0) -> dict:
        index = self.chunk_counts.get(call_id, 0)
        self.chunk_counts[call_id] = index + 1
        received = time.perf_counter()
        asr_result = self.asr.transcribe(b"", language="en", aligned_text=text)
        after_asr = time.perf_counter()
        signals = self.detector.detect(call_id, speaker, asr_result["text"], offset_ms / 1000)
        after_signal = time.perf_counter()
        llm_ms = "NOT MEASURED"
        nudges = self.engine(call_id).consider(signals, now_s=offset_ms / 1000)
        after_nudge = time.perf_counter()
        self.db.add_transcript(call_id, speaker, asr_result["text"], offset_ms)
        for signal in signals:
            self.db.add_signal(call_id, signal)
        for nudge in nudges:
            self.db.add_nudge(call_id, nudge)
        after_delivery = time.perf_counter()
        metrics = {
            "asr_ms": (after_asr - received) * 1000,
            "signal_ms": (after_signal - after_asr) * 1000,
            "llm_ms": llm_ms,
            "nudge_ms": (after_nudge - after_signal) * 1000,
            "delivery_ms": (after_delivery - after_nudge) * 1000,
            "e2e_ms": (after_delivery - received) * 1000,
        }
        self.db.add_latency(call_id, index, metrics)
        return {
            "type": "chunk_result",
            "call_id": call_id,
            "chunk_index": index,
            "speaker": speaker,
            "text": asr_result["text"],
            "offset_ms": offset_ms,
            "signals": signals,
            "nudges": nudges,
            "latency_ms": metrics,
            "asr_mode": asr_result["mode"],
            "asr_note": asr_result["note"],
        }

    def replay(self, scenario_name: str, call_id: str, speed: float = 0) -> dict:
        scenario = load_scenarios()[scenario_name]
        events = []
        previous = 0
        for turn in scenario["turns"]:
            offset = int(turn.get("t_ms", previous))
            if speed > 0 and events:
                delay = max(0, (offset - previous) / 1000) / speed
                time.sleep(delay)
            previous = offset
            events.append(
                self.process_chunk(call_id, turn["speaker"], turn["text"], offset)
            )
        samples = [event["latency_ms"] for event in events]
        return {
            "scenario": scenario_name,
            "call_id": call_id,
            "description": scenario.get("description", ""),
            "speed": speed,
            "events": events,
            "latency": summarize(samples),
            "nudge_count": sum(len(event["nudges"]) for event in events),
            "signal_count": sum(len(event["signals"]) for event in events),
        }


def replay_in_memory(database, scenario_name: str, call_id: str, speed: float = 0, threshold: float = 0.62) -> dict:
    pipeline = RealtimePipeline(database, threshold=threshold)
    return pipeline.replay(scenario_name, call_id, speed=speed)
