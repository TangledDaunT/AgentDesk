"""Configuration management for AgentDesk backend."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM
    anthropic_api_key: str

    # Services
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "agentdesk_memory"
    database_url: str = "sqlite+aiosqlite:///./agentdesk.db"

    # Optional search API
    serpapi_key: str | None = None

    # Agent config
    working_dir: str = "./workspace"
    max_retries: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
