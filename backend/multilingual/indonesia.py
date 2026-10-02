"""Indonesia multifinance locale pack."""

from __future__ import annotations

import json
import re

from app.config import PROJECT_ROOT
from multilingual.detect import detect_indonesia, normalize_javanese_lexicon

CONFIG_PATH = PROJECT_ROOT / "data" / "indonesia_config.json"

FIELDS = [
    "insurance_requirement",
    "name",
    "budget_range",
    "tenor",
    "current_insurance",
    "callback_preference",
]

PROMPTS_FORMAL = {
    "insurance_requirement": "Produk pembiayaan yang mana yang ingin kita bahas?",
    "name": "Siapa nama Bapak/Ibu?",
    "budget_range": "Berapa nilai cicilan per bulan yang sedang berjalan?",
    "tenor": "Berapa tenor yang tertera di perjanjian?",
    "current_insurance": "Apakah angsuran bulan ini sudah jatuh tempo, atau masih sebelum tanggalnya?",
    "callback_preference": "Kapan waktu yang tepat jika perlu callback?",
}

PROMPTS_COLLOQUIAL = {
    "insurance_requirement": "Mau bahas cicilan yang mana?",
    "name": "Siapa namanya?",
    "budget_range": "Cicilan per bulannya berapa?",
    "tenor": "Tenornya berapa lama?",
    "current_insurance": "Cicilan bulan ini sudah jatuh tempo belum?",
    "callback_preference": "Kapan enak kalau perlu ditelpon lagi?",
}


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def greeting() -> str:
    return load_config()["examples"][0]["text"]


def fallback(register: str) -> str:
    config = load_config()
    if register == "colloquial":
        return config["fallback_colloquial"]
    return config["fallback"]


def escalation(register: str) -> str:
    if register == "colloquial":
        return "Oke, saya hubungkan ke petugas. Saya berhenti di sini, nggak saya lanjutin pitch-nya."
    return "Baik. Saya hubungkan Bapak/Ibu dengan petugas. Saya tidak melanjutkan kualifikasi."


def goodbye(register: str) -> str:
    if register == "colloquial":
        return "Sip, saya akhiri dulu. Terima kasih ya."
    return "Terima kasih atas waktunya. Saya akhiri percakapan ini."


def prompts_for(register: str) -> dict:
    if register == "colloquial":
        return PROMPTS_COLLOQUIAL
    return PROMPTS_FORMAL


def filters_for(register: str) -> dict:
    if register == "colloquial":
        return {"source_prefix": "indonesia/", "document_type": "id_colloquial"}
    return {"source_prefix": "indonesia/", "document_type": "id_formal"}


def prepare_text(text: str) -> tuple[str, str, bool]:
    register = detect_indonesia(text)
    normalized = normalize_javanese_lexicon(text) if register == "javanese_regional" else text
    return normalized, register, normalized != text


def _term(text: str, term: str) -> bool:
    return re.search(rf"\b{re.escape(term)}\b", text.lower()) is not None


def consent(text: str) -> str | None:
    if any(_term(text, term) for term in ("tidak", "jangan", "no")) or "nggak mau" in text.lower():
        return "no"
    if any(_term(text, term) for term in ("ya", "silakan", "boleh", "siap", "oke", "ok", "gas", "yes")):
        return "yes"
    return None


ACCENT_TEST = {
    "region": "Javanese-influenced Indonesian, Central Java, outside standard Jakarta speech",
    "test_phrase": "Nyuwun sewu, cicilane telat, bayare piye?",
    "expected_meaning": "Excuse me, the installment is late, how do I pay?",
    "expected_transcript_if_normalized_to_standard_indonesian": "Permisi, cicilan telat, pembayaran bagaimana?",
    "actual_transcript": "NOT MEASURED",
    "asr_provider": "mock",
    "observed_error": "NOT MEASURED. No cloud ASR credential is configured, so accent recognition accuracy was not measured.",
    "lexicon_normalization_preview": "permisi, cicilan telat, pembayaran bagaimana?",
    "fallback_behavior": (
        "If ASR confidence were low, the bot would stay in Indonesian and ask the caller to repeat slowly. "
        "It would not switch to English. The lexicon preview above is only for text that is already transcribed."
    ),
    "low_confidence_fallback_response": "Maaf, saya kurang jelas mendengarnya. Bisa diulang pelan-pelan?",
}
