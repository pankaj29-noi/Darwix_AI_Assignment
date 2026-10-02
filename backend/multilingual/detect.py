"""Language and register detection for Philippines and Indonesia turns."""

from __future__ import annotations

import re

TL_STRONG = {
    "po",
    "opo",
    "yung",
    "hindi",
    "naman",
    "kasi",
    "mga",
    "wala",
    "meron",
    "magkano",
    "sige",
    "kayo",
    "akong",
    "taga",
    "asawa",
    "bukas",
    "kumusta",
    "swak",
    "gusto",
    "ako",
}
TL_WEAK = {"ang", "ng", "sa", "na", "ba", "ko", "mo", "ka", "oo"}
EN_STRONG = {
    "what",
    "please",
    "already",
    "explain",
    "coverage",
    "month",
    "have",
    "need",
    "insurance",
    "premium",
    "policy",
    "can",
    "the",
    "this",
    "rider",
}
ID_FORMAL = {"apakah", "dapat", "saya", "bapak", "ibu", "mohon", "silakan", "pembiayaan", "angsuran"}
ID_COLLOQUIAL = {"gue", "gua", "nggak", "gak", "dong", "sih", "udah", "banget", "nego"}
ID_SHARED = {"cicilan", "tenor", "denda", "jatuh", "tempo", "angsuran", "pembiayaan"}
JAVANESE = {"nyuwun", "sewu", "piye", "cicilane", "nggih", "mboten", "bayare"}

JAVANESE_REPLACEMENTS = (
    (re.compile(r"\bnyuwun sewu\b", re.I), "permisi"),
    (re.compile(r"\bcicilane\b", re.I), "cicilan"),
    (re.compile(r"\bbayare\b", re.I), "pembayaran"),
    (re.compile(r"\bpiye\b", re.I), "bagaimana"),
)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def detect_philippines(text: str) -> str:
    tokens = set(_tokens(text))
    tl = len(tokens & TL_STRONG) + (1 if len(tokens & TL_WEAK) >= 2 else 0)
    en = len(tokens & EN_STRONG)
    if tl and en:
        return "taglish"
    if tl:
        return "tl"
    return "en"


def detect_indonesia(text: str) -> str:
    tokens = set(_tokens(text))
    if tokens & JAVANESE:
        return "javanese_regional"
    if tokens & ID_COLLOQUIAL:
        return "colloquial"
    if tokens & ID_FORMAL or tokens & ID_SHARED:
        return "formal"
    return "id_unmarked"


def normalize_javanese_lexicon(text: str) -> str:
    """Map a few Central Java forms into standard Indonesian.

    This is a text lexicon for phrases that are already transcribed.
    It is not accent recognition.
    """

    updated = text
    for pattern, replacement in JAVANESE_REPLACEMENTS:
        updated = pattern.sub(replacement, updated)
    return updated
