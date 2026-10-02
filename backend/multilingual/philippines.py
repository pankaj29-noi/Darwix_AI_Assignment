"""Philippines bancassurance locale pack."""

from __future__ import annotations

import json
import re

from app.config import PROJECT_ROOT
from multilingual.detect import detect_philippines

CONFIG_PATH = PROJECT_ROOT / "data" / "philippines_config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


FIELDS = [
    "insurance_requirement",
    "name",
    "location",
    "bank_customer",
    "beneficiary",
    "budget_range",
    "current_insurance",
    "callback_preference",
]

PROMPTS = {
    "insurance_requirement": "Anong klaseng life cover ang tinitingnan mo, individual o may rider?",
    "name": "Ano po ang pangalan mo?",
    "location": "Saang lungsod ka nakatira?",
    "bank_customer": "May savings account ka na ba sa partner bank, o wala pa?",
    "beneficiary": "Sino ang beneficiary na gusto mo, halimbawa asawa o anak?",
    "budget_range": "Magkano ang premium kada buwan na swak sa budget mo, in pesos?",
    "current_insurance": "May existing life policy ka na ba, o wala pa?",
    "callback_preference": "Kailan puwedeng tumawag ulit kung kailangan ng follow-up?",
}

CONSENT_YES = ("oo", "opo", "sige", "yes", "go ahead", "i agree", "i consent")
CONSENT_NO = ("hindi", "ayaw", "no", "huwag", "stop")


def greeting() -> str:
    return load_config()["examples"][0]["text"]


def fallback() -> str:
    return load_config()["fallback"]


def escalation() -> str:
    return (
        "Sige po. Iko-connect kita sa isang tao mula sa team. "
        "Hindi na ako magpapatuloy sa qualification."
    )


def goodbye() -> str:
    return "Salamat sa oras mo. Tatapusin ko na ang call na ito. Ingat."


def summary_intro() -> str:
    return "Ito ang buod ng usapan, base sa sinabi mo at sa knowledge base:"


def filters_for(text: str) -> dict:
    language = detect_philippines(text)
    if language == "en":
        return {"source_prefix": "philippines/", "language": "en"}
    return {"source_prefix": "philippines/", "language": "tl"}


def _term(text: str, term: str) -> bool:
    return re.search(rf"\b{re.escape(term)}\b", text.lower()) is not None


def consent(text: str) -> str | None:
    if any(_term(text, term) for term in ("hindi", "ayaw", "huwag")) or _term(text, "no"):
        return "no"
    yes_terms = ("oo", "opo", "sige", "yes", "agree", "consent")
    if any(_term(text, term) for term in yes_terms) or "go ahead" in text.lower():
        return "yes"
    return None
