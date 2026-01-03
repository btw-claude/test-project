"""Application settings using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Slack Configuration
    slack_bot_token: str = Field(
        ...,
        description="Slack Bot OAuth Token (xoxb-...)",
    )
    slack_app_token: str = Field(
        ...,
        description="Slack App-Level Token (xapp-...)",
    )
    slack_signing_secret: str = Field(
        ...,
        description="Slack Signing Secret for request verification",
    )

    # Application Settings
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )
    app_debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    app_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API host address",
    )
    api_port: int = Field(
        default=8000,
        description="API port number",
    )

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins. Use ['*'] for development, restrict for production.",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
