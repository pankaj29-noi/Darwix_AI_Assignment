"""PII detection and redaction for synthetic and ingested text.

The detector is pattern-based. It flags obvious identifiers. It is not a
complete privacy classifier.
"""

from __future__ import annotations

import re

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    (
        "phone",
        re.compile(
            r"(?:\+?\d{1,3}[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b|(?:\+\d{1,3}[\s-]?)?\d{3}[\s-]\d{3}[\s-]\d{4}\b"
        ),
    ),
    ("aadhaar", re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")),
    ("card", re.compile(r"\b(?:\d{4}[-\s]){3}\d{4}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("dob", re.compile(r"\b(?:dob|date of birth)\s*[:\-]\s*\d{4}-\d{2}-\d{2}\b", re.I)),
]


def find_pii(text: str) -> list[dict]:
    found: list[dict] = []
    for label, pattern in PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0)
            digits = re.sub(r"\D", "", value)
            if label == "phone" and len(digits) < 10:
                continue
            found.append({"type": label, "start": match.start(), "end": match.end()})
    found.sort(key=lambda item: item["start"])
    return found


def redact(text: str) -> tuple[str, bool, list[str]]:
    matches = find_pii(text)
    if not matches:
        return text, False, []
    types = sorted({item["type"] for item in matches})
    redacted = text
    for item in reversed(matches):
        token = f"[REDACTED_{item['type'].upper()}]"
        redacted = redacted[: item["start"]] + token + redacted[item["end"] :]
    return redacted, True, types
