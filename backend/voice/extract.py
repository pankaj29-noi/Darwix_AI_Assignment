"""Slot extraction for the health-insurance qualification flow."""

from __future__ import annotations

import re


def _search(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.I)
    return match.group(1).strip(" .,") if match else None


def extract_health_slots(text: str) -> dict:
    found: dict = {}
    name = _search(r"\bmy name is\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", text)
    if name and not name.split()[0].isdigit():
        found["name"] = name.title()
    age = _search(r"\b(\d{1,2})\s+years?\s+old\b", text) or _search(r"\bi am\s+(\d{1,2})\b", text)
    if age:
        found["age"] = int(age)
    location = _search(r"\bi live in\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)", text)
    if location:
        found["location"] = location.title()
    if re.search(r"\bhealth insurance\b|\bhospitalization\b", text, re.I):
        found["insurance_requirement"] = "health insurance"
    if re.search(r"\bjust me\b|\bonly me\b|\bindividual\b|\bmyself\b", text, re.I):
        found["family_coverage"] = "self"
    elif re.search(r"\bfamily\b|\bspouse\b|\bchildren\b|\bkids\b|\bwife\b|\bhusband\b", text, re.I):
        found["family_coverage"] = "family"
    if re.search(r"\b(do not|don't|do not)\s+have\b|\bno current insurance\b|\bi do not have current", text, re.I):
        found["current_insurance"] = "none"
    elif re.search(r"\balready have\b|\bi have (a |current )?insurance\b|\bi have a policy\b", text, re.I):
        found["current_insurance"] = "yes"
    budget = _search(r"\b(?:budget|afford)\s+(?:is\s+)?(?:inr\s+|rs\.?\s+|rupees\s+)?(\d[\d,]*)", text)
    if budget is None:
        budget = _search(r"\b(\d[\d,]*)\s+rupees\b", text)
    if budget:
        found["budget_range"] = int(budget.replace(",", ""))
    cover = _search(r"\b(\d+(?:\.\d+)?)\s+lakh\b", text)
    if cover:
        found["preferred_coverage"] = f"{cover} lakh"
    if re.search(r"\bthis month\b|\burgent\b|\bimmediately\b|\bthis week\b", text, re.I):
        found["urgency"] = "high"
    elif re.search(r"\bno rush\b|\bjust looking\b", text, re.I):
        found["urgency"] = "low"
    callback = _search(r"\b((?:tomorrow|today|bukas)[^.]{0,40}|after\s+\d{1,2}[^.]{0,20})", text)
    if callback:
        found["callback_preference"] = callback.strip()
    elif re.search(r"\bcall me\b", text, re.I):
        found["callback_preference"] = text.strip()
    return found


def is_question(text: str) -> bool:
    lowered = text.lower().strip()
    if "?" in text:
        return True
    starters = ("what ", "how ", "when ", "why ", "where ", "which ", "does ", "can you ", "is the ", "are there ")
    return lowered.startswith(starters)


def is_objection(text: str) -> bool:
    lowered = text.lower()
    phrases = (
        "too expensive",
        "too costly",
        "can't afford",
        "cannot afford",
        "not interested",
        "waste of money",
        "mahal",
        "di ko kaya",
        "ang mahal",
        "denda",
        "kemahalan",
        "belum gajian",
    )
    return any(phrase in lowered for phrase in phrases)


def is_human_request(text: str) -> bool:
    lowered = text.lower()
    phrases = (
        "human",
        "real person",
        "representative",
        "totoong tao",
        "petugas",
        "supervisor",
        "live agent",
        "customer care",
        "makausap",
    )
    return any(re.search(rf"\b{re.escape(phrase)}\b", lowered) for phrase in phrases)


def is_refusal(text: str) -> bool:
    lowered = text.lower()
    phrases = ("rather not", "prefer not", "don't want to say", "do not want to share", "skip this", "ayaw ko sabihin")
    return any(phrase in lowered for phrase in phrases)
