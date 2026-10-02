"""ASR providers.

Mock mode returns text that the caller already has (a typed utterance or a
replay script). It does not claim to have recognized audio.
"""

from __future__ import annotations

import time
from typing import Protocol

from providers.base import MissingCredentialError, ProviderNotConfiguredError


class ASRProvider(Protocol):
    mode: str

    def transcribe(self, audio: bytes, language: str, aligned_text: str = "") -> dict: ...


class MockASR:
    mode = "mock"

    def transcribe(self, audio: bytes, language: str, aligned_text: str = "") -> dict:
        started = time.perf_counter()
        if not aligned_text and not audio:
            text = ""
        else:
            text = " ".join((aligned_text or "").split())
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "text": text,
            "language": language,
            "mode": self.mode,
            "latency_ms": elapsed_ms,
            "note": "Mock ASR returned aligned text. Cloud speech recognition was not called.",
        }


class HttpASR:
    """Placeholder for a future HTTP ASR vendor. It fails closed without a key."""

    mode = "http"

    def __init__(self, api_key: str, provider_name: str):
        if not api_key.strip():
            raise MissingCredentialError("ASR_API_KEY is empty.")
        self.provider_name = provider_name

    def transcribe(self, audio: bytes, language: str, aligned_text: str = "") -> dict:
        raise ProviderNotConfiguredError(
            f"ASR provider '{self.provider_name}' is not wired to a vendor SDK. "
            "No transcript was fabricated."
        )


def build_asr(provider: str, api_key: str) -> ASRProvider:
    if provider != "mock" and api_key.strip():
        return HttpASR(api_key, provider)
    return MockASR()
