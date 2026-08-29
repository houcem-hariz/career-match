"""Runtime configuration. Secrets stay in the environment, never in code."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_PROJECT_ROOT / ".env", _BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "groq"
    llm_chat_model: str = "openai/gpt-oss-20b"
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    llm_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    database_url: str = "postgresql://career_match:career_match@127.0.0.1:5433/career_match"

    extraction_cache_enabled: bool = True
    extraction_cache_dir: Path = _PROJECT_ROOT / "data" / "cache"
    embedding_cache_dir: Path = _PROJECT_ROOT / "data" / "cache" / "embeddings"


def get_settings() -> Settings:
    return Settings()


def project_root() -> Path:
    return _PROJECT_ROOT
