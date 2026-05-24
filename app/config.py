from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    APP_NAME: str = "Org Structure API"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://orguser:orgpass123@localhost:5432/orgstructure"
    SYNC_DATABASE_URL: str = "postgresql://orguser:orgpass123@localhost:5432/orgstructure"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
