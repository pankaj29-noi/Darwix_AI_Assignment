"""Voice-session providers.

The default provider is a web session. It must not be described as a phone call.
"""

from __future__ import annotations

from typing import Protocol
from uuid import uuid4

from providers.base import MissingCredentialError, ProviderNotConfiguredError


class VoiceProvider(Protocol):
    mode: str

    def start_session(self, use_case: str) -> dict: ...


class MockWebVoice:
    mode = "mock_web"

    def start_session(self, use_case: str) -> dict:
        return {
            "session_id": uuid4().hex,
            "use_case": use_case,
            "mode": self.mode,
            "phone_number": None,
            "note": "Web session only. No outbound or inbound phone call was placed.",
        }


class HttpVoice:
    mode = "http"

    def __init__(self, api_key: str, provider_name: str):
        if not api_key.strip():
            raise MissingCredentialError("VOICE_API_KEY is empty.")
        self.provider_name = provider_name

    def start_session(self, use_case: str) -> dict:
        raise ProviderNotConfiguredError(
            f"Voice provider '{self.provider_name}' is not connected. No call was placed."
        )


def build_voice(provider: str, api_key: str) -> VoiceProvider:
    if provider != "mock" and api_key.strip():
        return HttpVoice(api_key, provider)
    return MockWebVoice()
