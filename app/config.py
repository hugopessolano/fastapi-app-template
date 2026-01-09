from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the template to simplify customization."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="FastAPI Template")
    environment: str = Field(default="development")
    database_url: str = Field(default="sqlite:///./app/app.db")
    logs_db_path: str = Field(default="app/mi_aplicacion_logs.db")
    external_database_url: Optional[str] = Field(default=None, alias="EXTERNAL_DB_URL")

    secret_key: str = Field(default="change-me")
    access_token_expire_minutes: int = Field(default=720)
    token_algorithm: str = Field(default="HS256")

    auto_build_permissions: bool = Field(default=True)
    enable_seed_data: bool = Field(default=True)
    seed_check_existing_users: bool = Field(default=True)

    logging_stdout_level: str = Field(default="INFO")
    logging_db_level: str = Field(default="INFO")
    auth_mode: str = Field(default="built_in", description="built_in | disabled | custom")
    tenants_enabled: bool = Field(default=True)
    rate_limit_default_requests: int = Field(default=60)
    rate_limit_default_window_seconds: int = Field(default=60)
    retry_max_attempts: int = Field(default=3)
    retry_base_delay_seconds: float = Field(default=0.2)
    retry_max_delay_seconds: float = Field(default=2.0)
    retry_jitter_seconds: float = Field(default=0.1)
    cache_enabled: bool = Field(default=False)
    cache_default_ttl_seconds: int = Field(default=60)

    @property
    def resolved_logs_db_path(self) -> str:
        """Returns the absolute path for the logs database."""
        return str(Path(self.logs_db_path).resolve())

    @property
    def normalized_auth_mode(self) -> str:
        value = (self.auth_mode or "built_in").strip().lower()
        if value not in {"built_in", "disabled", "custom"}:
            raise ValueError(f"Invalid AUTH_MODE '{self.auth_mode}'. Allowed values: built_in, disabled, custom.")
        return value


@lru_cache
def get_settings() -> Settings:
    """Ensure we only instantiate settings once."""
    return Settings()
