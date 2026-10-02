"""Write measured evaluation files. Run from the project root with PYTHONPATH=backend."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("EMBEDDING_PROVIDER", "tfidf")
os.environ.setdefault("LLM_PROVIDER", "mock")

from app.config import PROJECT_ROOT, get_settings
from app.main import create_app
from multilingual.detect import detect_indonesia, detect_philippines, normalize_javanese_lexicon
from multilingual.indonesia import ACCENT_TEST
from rag.evaluation import run_evaluation
from realtime.pipeline import RealtimePipeline, load_scenarios

RESULTS = PROJECT_ROOT / "results"
TRANSCRIPTS = PROJECT_ROOT / "transcripts"


def main() -> None:
    get_settings.cache_clear()
    app = create_app()
    RESULTS.mkdir(parents=True, exist_ok=True)
    rag = run_evaluation(app.state.kb)
    (RESULTS / "rag_evaluation.json").write_text(json.dumps(rag, indent=2), encoding="utf-8")
    app.state.db.save_evaluation("rag", rag)

    voice_path = PROJECT_ROOT / "data" / "voice" / "scenarios.json"
    scenarios = json.loads(voice_path.read_text(encoding="utf-8"))
    multilingual_cases = []
    for key, scenario in scenarios.items():
        use_case, name = key.split(":", 1)
        if use_case == "health":
            folder = TRANSCRIPTS / "q1"
        elif use_case == "philippines":
            folder = TRANSCRIPTS / "q3_philippines"
        else:
            folder = TRANSCRIPTS / "q3_indonesia"
        folder.mkdir(parents=True, exist_ok=True)
        started = app.state.orchestrator.start(use_case)
        turns = [{"speaker": "agent", "text": started["message"], "state": started["state"]}]
        latest = started
        for text in scenario["turns"]:
            latest = app.state.orchestrator.handle(started["call_id"], text)
            turns.append({"speaker": "customer", "text": text})
            turns.append(
                {
                    "speaker": "agent",
                    "text": latest["message"],
                    "state": latest["state"],
                    "fallback": latest["fallback"],
                    "sources": latest["sources"],
                }
            )
        record = {
            "scenario": key,
            "call_id": started["call_id"],
            "final_state": latest["state"],
            "escalated": latest["escalated"],
            "qualification": latest["qualification"],
            "eligibility": latest["eligibility"],
            "mode": latest["mode"],
            "turns": turns,
        }
        (folder / f"{name}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        if use_case != "health":
            multilingual_cases.append(
                {
                    "scenario": key,
                    "final_state": latest["state"],
                    "escalated": latest["escalated"],
                    "fallback_seen": any(turn.get("fallback") for turn in turns),
                    "last_message": latest["message"],
                }
            )

    detector_cases = [
        {"text": "Magkano yung premium per month?", "expected": "taglish", "actual": detect_philippines("Magkano yung premium per month?")},
        {"text": "Wala pa akong beneficiary", "expected": "tl", "actual": detect_philippines("Wala pa akong beneficiary")},
        {"text": "I need a life insurance policy", "expected": "en", "actual": detect_philippines("I need a life insurance policy")},
        {"text": "Apakah tenor pembiayaan dapat diubah?", "expected": "formal", "actual": detect_indonesia("Apakah tenor pembiayaan dapat diubah?")},
        {"text": "Gue telat bayar cicilan, bisa nego denda nggak?", "expected": "colloquial", "actual": detect_indonesia("Gue telat bayar cicilan, bisa nego denda nggak?")},
        {
            "text": "Nyuwun sewu, cicilane telat, bayare piye?",
            "expected": "javanese_regional",
            "actual": detect_indonesia("Nyuwun sewu, cicilane telat, bayare piye?"),
        },
    ]
    multilingual = {
        "asr": {
            "provider": app.state.settings.asr_mode,
            "model": "NOT MEASURED",
            "languages_configured": ["en", "fil", "tl", "id"],
            "code_switching": "Detector results below are text rules, not ASR quality.",
            "approximate_quality": "NOT MEASURED",
            "latency": "NOT MEASURED",
            "observed_asr_errors": "NOT MEASURED",
            "reason": "No ASR API key was configured. Mock ASR returns aligned text and does not recognize audio.",
        },
        "tts": {
            "provider": app.state.settings.tts_mode,
            "native_filipino_voice": "NOT MEASURED",
            "native_indonesian_voice": "NOT MEASURED",
            "note": "Server TTS did not synthesize audio. Browser voice selection has to be checked in the UI.",
        },
        "detector_cases": detector_cases,
        "detector_mismatches": [case for case in detector_cases if case["actual"] != case["expected"]],
        "scenarios": multilingual_cases,
        "accent_test": {
            **ACCENT_TEST,
            "lexicon_normalization_actual": normalize_javanese_lexicon(ACCENT_TEST["test_phrase"]),
        },
    }
    (RESULTS / "multilingual_results.json").write_text(json.dumps(multilingual, indent=2), encoding="utf-8")

    pipeline = RealtimePipeline(
        app.state.db,
        threshold=app.state.settings.nudge_confidence_threshold,
        cooldown_s=app.state.settings.nudge_cooldown_seconds,
    )
    nudge_runs = []
    for name in load_scenarios():
        outcome = pipeline.replay(name, f"eval-{name}", speed=0)
        nudge_runs.append(
            {
                "scenario": name,
                "description": outcome["description"],
                "signal_count": outcome["signal_count"],
                "nudge_count": outcome["nudge_count"],
                "nudges": [
                    {
                        "type": nudge["type"],
                        "text": nudge["text"],
                        "confidence": nudge["confidence"],
                        "evidence": nudge["evidence"],
                        "offset_ms": event["offset_ms"],
                    }
                    for event in outcome["events"]
                    for nudge in event["nudges"]
                ],
            }
        )
    false_positive_check = {
        "neutral_nudge_count": next(item["nudge_count"] for item in nudge_runs if item["scenario"] == "neutral"),
        "noisy_nudge_count": next(item["nudge_count"] for item in nudge_runs if item["scenario"] == "noisy"),
        "note": "Neutral and noisy replays are the false-positive check. Counts are from this run.",
    }
    nudge_payload = {"runs": nudge_runs, "false_positive_check": false_positive_check}
    (RESULTS / "nudge_results.json").write_text(json.dumps(nudge_payload, indent=2), encoding="utf-8")
    (TRANSCRIPTS / "q4").mkdir(parents=True, exist_ok=True)
    (TRANSCRIPTS / "q4" / "full_demo.json").write_text(
        json.dumps(next(item for item in nudge_runs if item["scenario"] == "full_demo"), indent=2),
        encoding="utf-8",
    )

    latency_run = pipeline.replay("full_demo", "latency-full-demo", speed=0)
    latency_payload = {
        "scenario": "full_demo",
        "speed": 0,
        "speed_note": "Processing latency excludes intentional real-time sleep. Use scripts/replay_call.py --speed 1 for a wall-clock demo.",
        "latency": latency_run["latency"],
        "chunk_latencies_ms": [event["latency_ms"] for event in latency_run["events"]],
    }
    (RESULTS / "latency_results.json").write_text(json.dumps(latency_payload, indent=2), encoding="utf-8")
    print(json.dumps({"rag_verdicts": [row["verdict"] for row in rag["results"]], "latency": latency_run["latency"]}, indent=2))


if __name__ == "__main__":
    main()
