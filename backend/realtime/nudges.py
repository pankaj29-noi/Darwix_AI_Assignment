"""Nudge control: threshold, cooldown, priority, expiry, topic grouping, repetition."""

from __future__ import annotations

from uuid import uuid4

PRIORITY = {
    "compliance": 0,
    "frustration": 1,
    "payment_difficulty": 2,
    "missed_opportunity": 3,
    "callback": 4,
    "buying_signal": 5,
    "intent_shift": 6,
}


class NudgeEngine:
    def __init__(self, threshold: float = 0.62, cooldown_s: float = 45, max_repeats: int = 2):
        self.threshold = threshold
        self.cooldown_s = cooldown_s
        self.max_repeats = max_repeats
        self.emitted: list[dict] = []

    def consider(self, signals: list[dict], now_s: float) -> list[dict]:
        nudges = []
        ordered = sorted(signals, key=lambda item: PRIORITY.get(item["type"], 9))
        for signal in ordered:
            if signal["confidence"] < self.threshold:
                continue
            if self._blocked(signal, now_s):
                continue
            nudge = {
                "nudge_id": uuid4().hex[:12],
                "signal_id": signal["signal_id"],
                "timestamp": signal["timestamp"],
                "text": signal["recommended_action"],
                "priority": PRIORITY.get(signal["type"], 9),
                "confidence": signal["confidence"],
                "evidence": signal["evidence"],
                "topic": signal["topic"],
                "type": signal["type"],
                "expires_at": signal["expires_at"],
            }
            nudges.append(nudge)
            self.emitted.append({"type": signal["type"], "topic": signal["topic"], "at": now_s})
        return nudges

    def _blocked(self, signal: dict, now_s: float) -> bool:
        same = [item for item in self.emitted if item["type"] == signal["type"] and item["topic"] == signal["topic"]]
        if len(same) >= self.max_repeats:
            return True
        if any(now_s - item["at"] < self.cooldown_s for item in same):
            return True
        return False
