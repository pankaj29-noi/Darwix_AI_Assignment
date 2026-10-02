"""Rule-based signal extraction from a streaming transcript chunk."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4


FRUSTRATION = (
    (re.compile(r"\b(ridiculous|frustrated|annoying|annoyed|useless)\b", re.I), 0.86),
    (re.compile(r"already told you", re.I), 0.9),
    (re.compile(r"not listening", re.I), 0.88),
    (re.compile(r"waste of (my )?time", re.I), 0.9),
    (re.compile(r"this is taking too long", re.I), 0.8),
)
BUYING = re.compile(
    r"\b(i want to (buy|purchase|enroll|proceed)|sign me up|let's proceed|i(?:'m| am) ready to buy)\b",
    re.I,
)
CALLBACK = (
    (re.compile(r"call me (back|later)", re.I), 0.86),
    (re.compile(r"not a good time", re.I), 0.8),
    (re.compile(r"\bbusy now\b", re.I), 0.78),
    (re.compile(r"\bafter \d{1,2}\b", re.I), 0.7),
)
FAMILY = re.compile(r"\b(my wife|my husband|my spouse|our kids|two kids|my children|my parents)\b", re.I)
VEHICLE = re.compile(r"\b(another vehicle|second car|wife'?s car|two cars|multi-vehicle)\b", re.I)
PAYMENT = re.compile(
    r"\b(can(?:not|'t) pay|payment is hard|don'?t have (?:the )?money|salary is delayed|denda kemahalan)\b",
    re.I,
)
TOPICS = (
    ("claims", re.compile(r"\b(claim|reimbursement|cashless)\b", re.I)),
    ("premium", re.compile(r"\b(premium|price|budget|expensive)\b", re.I)),
    ("waiting_period", re.compile(r"waiting period", re.I)),
    ("hospital", re.compile(r"\bhospital\b", re.I)),
)
GARBAGE = ("asdf", "qwerty", "uhhh", "ummm")
ELIGIBILITY_CLAIM = re.compile(r"you are eligible|mark you eligible|confirm eligibility", re.I)


def _now(offset_s: float) -> str:
    moment = datetime.now(timezone.utc) + timedelta(seconds=offset_s)
    return moment.replace(microsecond=0).isoformat()


def _signal(kind: str, severity: str, confidence: float, evidence: str, action: str, topic: str, offset_s: float) -> dict:
    return {
        "signal_id": uuid4().hex[:12],
        "timestamp": _now(0),
        "type": kind,
        "severity": severity,
        "confidence": round(confidence, 4),
        "evidence": evidence,
        "recommended_action": action,
        "expires_at": _now(90),
        "topic": topic,
        "call_offset_s": offset_s,
    }


def is_noisy(text: str) -> bool:
    lowered = text.lower()
    return sum(1 for token in GARBAGE if token in lowered) >= 2


class SignalDetector:
    def __init__(self) -> None:
        self.calls: dict[str, dict] = {}

    def _memory(self, call_id: str) -> dict:
        if call_id not in self.calls:
            self.calls[call_id] = {"agent_text": "", "last_topic": None, "disclosure": False}
        return self.calls[call_id]

    def detect(self, call_id: str, speaker: str, text: str, offset_s: float) -> list[dict]:
        memory = self._memory(call_id)
        if speaker == "agent":
            memory["agent_text"] += " " + text
            if "waiting period" in text.lower():
                memory["disclosure"] = True
        signals: list[dict] = []
        noisy = is_noisy(text)

        if speaker == "customer":
            for pattern, confidence in FRUSTRATION:
                if pattern.search(text):
                    signals.append(
                        _signal(
                            "frustration",
                            "high",
                            confidence,
                            text.strip(),
                            "Customer appears frustrated. Acknowledge the concern before continuing.",
                            "frustration",
                            offset_s,
                        )
                    )
                    break
            if BUYING.search(text):
                signals.append(
                    _signal(
                        "buying_signal",
                        "medium",
                        0.84,
                        text.strip(),
                        "Customer showed a buying signal. Confirm needs and required disclosures before proceeding.",
                        "purchase",
                        offset_s,
                    )
                )
                if "waiting period" not in memory["agent_text"].lower():
                    signals.append(
                        _signal(
                            "compliance",
                            "high",
                            0.9,
                            f"Required disclosure 'waiting period' was not found in the agent transcript before the customer said: \"{text.strip()}\"",
                            "Required waiting-period disclosure may be missing. Confirm that disclosure before proceeding.",
                            "disclosure",
                            offset_s,
                        )
                    )
            for pattern, confidence in CALLBACK:
                if pattern.search(text):
                    signals.append(
                        _signal(
                            "callback",
                            "medium",
                            confidence,
                            text.strip(),
                            "Customer asked for a callback. Confirm the time and pause the pitch.",
                            "callback",
                            offset_s,
                        )
                    )
                    break
            if FAMILY.search(text):
                signals.append(
                    _signal(
                        "missed_opportunity",
                        "medium",
                        0.83,
                        text.strip(),
                        "Customer mentioned family members who may need cover. Ask whether a family floater is relevant.",
                        "family_cover",
                        offset_s,
                    )
                )
            if VEHICLE.search(text):
                signals.append(
                    _signal(
                        "missed_opportunity",
                        "medium",
                        0.86,
                        text.strip(),
                        "Customer mentioned another vehicle. Consider discussing the multi-vehicle option.",
                        "multi_vehicle",
                        offset_s,
                    )
                )
            if PAYMENT.search(text):
                signals.append(
                    _signal(
                        "payment_difficulty",
                        "high",
                        0.84,
                        text.strip(),
                        "Consider the approved payment-support or callback path.",
                        "payment",
                        offset_s,
                    )
                )
            topic = None
            for name, pattern in TOPICS:
                if pattern.search(text):
                    topic = name
                    break
            if topic and memory["last_topic"] and topic != memory["last_topic"]:
                signals.append(
                    _signal(
                        "intent_shift",
                        "low",
                        0.7,
                        text.strip(),
                        f"The topic shifted from {memory['last_topic']} to {topic}. Acknowledge the new topic before returning to the previous one.",
                        f"{memory['last_topic']}_to_{topic}",
                        offset_s,
                    )
                )
            if topic:
                memory["last_topic"] = topic

        if speaker == "agent" and ELIGIBILITY_CLAIM.search(text):
            if "waiting period" not in memory["agent_text"].lower():
                signals.append(
                    _signal(
                        "compliance",
                        "high",
                        0.88,
                        text.strip(),
                        "Required waiting-period disclosure may be missing. Confirm that disclosure before proceeding.",
                        "disclosure",
                        offset_s,
                    )
                )

        if noisy:
            for signal in signals:
                signal["confidence"] = min(signal["confidence"], 0.35)
        return signals
