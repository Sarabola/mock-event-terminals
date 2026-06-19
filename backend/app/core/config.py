from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Mock Terminal Emulator"
    database_url: str = Field(default="sqlite+aiosqlite:////app/data/app.db")
    images_path: Path = Field(default=Path("/app/images"))
    cors_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173")
    auth_secret_key: str = Field(default="change-me-in-compose-env")
    access_token_ttl_seconds: int = Field(default=60 * 60 * 24 * 14)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
