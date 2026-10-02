"""OpenAI-compatible chat client and an explicit local fallback."""

from __future__ import annotations

from typing import Protocol

import httpx

from providers.base import MissingCredentialError


class LLMProvider(Protocol):
    mode: str

    def complete(self, system: str, user: str) -> str: ...


class OpenAICompatibleLLM:
    """Live chat completions. This class never invents a response."""

    mode = "openai_compatible"

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float = 30.0):
        if not api_key.strip():
            raise MissingCredentialError(
                "LLM_API_KEY is empty. Refusing to call the chat completions API."
            )
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, system: str, user: str) -> str:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "temperature": 0.1,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()


def build_llm(provider: str, api_key: str, model: str, base_url: str) -> OpenAICompatibleLLM | None:
    """Return a live client, or None when the process must stay in local mode."""

    if provider == "openai" and api_key.strip():
        return OpenAICompatibleLLM(api_key=api_key, model=model, base_url=base_url)
    return None
