"""TTS providers. Mock mode does not emit fake audio bytes."""

from __future__ import annotations

from typing import Protocol

from providers.base import MissingCredentialError, ProviderNotConfiguredError


class TTSProvider(Protocol):
    mode: str

    def synthesize(self, text: str, language: str) -> dict: ...


class MockTTS:
    mode = "mock"

    def synthesize(self, text: str, language: str) -> dict:
        return {
            "mode": self.mode,
            "language": language,
            "audio_bytes": None,
            "text": text,
            "note": (
                "Server TTS is in mock mode and did not synthesize audio. "
                "The web UI may use the browser speechSynthesis API, which is local "
                "and is not a telephony voice."
            ),
        }


class HttpTTS:
    mode = "http"

    def __init__(self, api_key: str, provider_name: str):
        if not api_key.strip():
            raise MissingCredentialError("TTS_API_KEY is empty.")
        self.provider_name = provider_name

    def synthesize(self, text: str, language: str) -> dict:
        raise ProviderNotConfiguredError(
            f"TTS provider '{self.provider_name}' has no vendor call implemented. "
            "No audio was fabricated."
        )


def build_tts(provider: str, api_key: str) -> TTSProvider:
    if provider != "mock" and api_key.strip():
        return HttpTTS(api_key, provider)
    return MockTTS()
