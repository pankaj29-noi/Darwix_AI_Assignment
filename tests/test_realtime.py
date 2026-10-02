"""Realtime signals, suppression, and latency math."""

from realtime.latency import percentile
from realtime.nudges import NudgeEngine
from realtime.pipeline import RealtimePipeline
from realtime.signals import SignalDetector


def test_percentiles():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([], 95) is None


def test_family_and_vehicle_nudges_quote_the_customer(tmp_path):
    from app.database import Database

    database = Database(tmp_path / "rt.db")
    pipeline = RealtimePipeline(database, threshold=0.62, cooldown_s=45)
    family = pipeline.process_chunk("c1", "customer", "My wife also needs cover, and we have two kids.", 0)
    assert family["nudges"]
    assert "wife" in family["nudges"][0]["evidence"].lower() or "kids" in family["nudges"][0]["evidence"].lower()
    vehicle = pipeline.process_chunk("c2", "customer", "My wife has another vehicle too.", 0)
    topics = {nudge["topic"] for nudge in vehicle["nudges"]}
    assert "multi_vehicle" in topics


def test_compliance_frustration_and_noisy(tmp_path):
    from app.database import Database

    database = Database(tmp_path / "rt.db")
    pipeline = RealtimePipeline(database)
    pipeline.process_chunk("c3", "agent", "I can mark you eligible right now.", 0)
    purchase = pipeline.process_chunk("c3", "customer", "I want to purchase today.", 5000)
    kinds = {signal["type"] for signal in purchase["signals"]}
    assert "buying_signal" in kinds
    assert "compliance" in kinds or any(signal["type"] == "compliance" for signal in pipeline.detector.detect("c3", "agent", "I can mark you eligible right now.", 0))
    frustrated = pipeline.process_chunk(
        "c4",
        "customer",
        "This is ridiculous. I already told you my budget. You are not listening.",
        0,
    )
    assert any(nudge["type"] == "frustration" for nudge in frustrated["nudges"])
    noisy = pipeline.process_chunk("c5", "customer", "uhhh hmm the the asdf policy thing maybe qwerty I dunno", 0)
    assert noisy["nudges"] == []


def test_duplicate_nudges_are_suppressed():
    engine = NudgeEngine(threshold=0.62, cooldown_s=45, max_repeats=2)
    signal = {
        "signal_id": "s1",
        "timestamp": "t",
        "type": "frustration",
        "severity": "high",
        "confidence": 0.9,
        "evidence": "This is ridiculous",
        "recommended_action": "Acknowledge the concern before continuing.",
        "expires_at": "later",
        "topic": "frustration",
    }
    assert len(engine.consider([signal], now_s=0)) == 1
    assert engine.consider([dict(signal, signal_id="s2")], now_s=10) == []
    assert len(engine.consider([dict(signal, signal_id="s3")], now_s=120)) == 1
    assert engine.consider([dict(signal, signal_id="s4")], now_s=400) == []


def test_neutral_replay_has_no_nudges(tmp_path):
    from app.database import Database

    database = Database(tmp_path / "rt.db")
    pipeline = RealtimePipeline(database)
    result = pipeline.replay("neutral", "neutral-call", speed=0)
    assert result["nudge_count"] == 0
    assert result["latency"]["llm_ms"] == "NOT MEASURED"
    assert result["latency"]["signal_ms"]["n"] >= 1
    assert result["latency"]["e2e_ms"]["p50"] is not None
