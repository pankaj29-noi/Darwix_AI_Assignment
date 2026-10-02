"""Runtime configuration. Credentials come from the environment only."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_provider: str = "mock"

    asr_api_key: str = ""
    asr_provider: str = "mock"

    tts_api_key: str = ""
    tts_provider: str = "mock"

    voice_api_key: str = ""
    voice_provider: str = "mock"

    database_url: str = "sqlite:///./data/app.db"
    vector_db_path: str = "./data/vector"
    kb_data_path: str = ""

    embedding_provider: str = "tfidf"
    chunk_size: int = 180
    chunk_overlap: int = 40
    top_k: int = 4
    confidence_threshold: float = 0.12

    nudge_confidence_threshold: float = 0.62
    nudge_cooldown_seconds: int = 45
    auto_ingest: bool = True

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def resolve(self, value: str) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    @property
    def database_path(self) -> Path:
        raw = self.database_url
        if raw.startswith("sqlite:///"):
            raw = raw[len("sqlite:///") :]
        return self.resolve(raw)

    @property
    def vector_path(self) -> Path:
        return self.resolve(self.vector_db_path)

    @property
    def knowledge_path(self) -> Path:
        if self.kb_data_path:
            return self.resolve(self.kb_data_path)
        return PROJECT_ROOT / "data" / "kb"

    @property
    def results_path(self) -> Path:
        return PROJECT_ROOT / "results"

    @property
    def llm_mode(self) -> str:
        if self.llm_provider == "openai" and self.llm_api_key.strip():
            return "openai_compatible"
        return "mock"

    @property
    def asr_mode(self) -> str:
        if self.asr_provider != "mock" and self.asr_api_key.strip():
            return self.asr_provider
        return "mock"

    @property
    def tts_mode(self) -> str:
        if self.tts_provider != "mock" and self.tts_api_key.strip():
            return self.tts_provider
        return "mock"

    @property
    def voice_mode(self) -> str:
        if self.voice_provider != "mock" and self.voice_api_key.strip():
            return self.voice_provider
        return "mock_web"


@lru_cache
def get_settings() -> Settings:
    return Settings()
