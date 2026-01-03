"""Tests for the settings module."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config.settings import Settings, get_settings


class TestSettings:
    """Tests for Settings class."""

    def test_settings_with_required_env_vars(self) -> None:
        """Test that settings loads correctly with required environment variables."""
        env_vars = {
            "SLACK_BOT_TOKEN": "xoxb-test-bot-token",
            "SLACK_APP_TOKEN": "xapp-test-app-token",
            "SLACK_SIGNING_SECRET": "test-signing-secret",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.slack_bot_token == "xoxb-test-bot-token"
            assert settings.slack_app_token == "xapp-test-app-token"
            assert settings.slack_signing_secret == "test-signing-secret"

    def test_settings_missing_required_vars(self) -> None:
        """Test that settings raises error when required vars are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_settings_default_values(self) -> None:
        """Test that settings has correct default values."""
        env_vars = {
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_APP_TOKEN": "xapp-test",
            "SLACK_SIGNING_SECRET": "secret",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.app_env == "development"
            assert settings.app_debug is False
            assert settings.app_log_level == "INFO"
            assert settings.api_host == "0.0.0.0"
            assert settings.api_port == 8000

    def test_settings_custom_values(self) -> None:
        """Test that settings correctly reads custom environment values."""
        env_vars = {
            "SLACK_BOT_TOKEN": "xoxb-custom",
            "SLACK_APP_TOKEN": "xapp-custom",
            "SLACK_SIGNING_SECRET": "custom-secret",
            "APP_ENV": "production",
            "APP_DEBUG": "true",
            "APP_LOG_LEVEL": "DEBUG",
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.app_env == "production"
            assert settings.app_debug is True
            assert settings.app_log_level == "DEBUG"
            assert settings.api_host == "127.0.0.1"
            assert settings.api_port == 9000

    def test_settings_case_insensitive(self) -> None:
        """Test that environment variable names are case insensitive."""
        env_vars = {
            "slack_bot_token": "xoxb-lower",
            "SLACK_APP_TOKEN": "xapp-upper",
            "Slack_Signing_Secret": "mixed-case",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.slack_bot_token == "xoxb-lower"
            assert settings.slack_app_token == "xapp-upper"
            assert settings.slack_signing_secret == "mixed-case"

    def test_settings_app_env_validation(self) -> None:
        """Test that app_env only accepts valid values."""
        env_vars = {
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_APP_TOKEN": "xapp-test",
            "SLACK_SIGNING_SECRET": "secret",
            "APP_ENV": "invalid_environment",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_settings_log_level_validation(self) -> None:
        """Test that app_log_level only accepts valid values."""
        env_vars = {
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_APP_TOKEN": "xapp-test",
            "SLACK_SIGNING_SECRET": "secret",
            "APP_LOG_LEVEL": "INVALID_LEVEL",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_settings_ignores_extra_env_vars(self) -> None:
        """Test that settings ignores extra environment variables."""
        env_vars = {
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_APP_TOKEN": "xapp-test",
            "SLACK_SIGNING_SECRET": "secret",
            "EXTRA_UNKNOWN_VAR": "should-be-ignored",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert not hasattr(settings, "extra_unknown_var")


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings(self) -> None:
        """Test that get_settings returns a Settings instance."""
        env_vars = {
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_APP_TOKEN": "xapp-test",
            "SLACK_SIGNING_SECRET": "secret",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            get_settings.cache_clear()
            settings = get_settings()
            assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self) -> None:
        """Test that get_settings returns the same cached instance."""
        env_vars = {
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_APP_TOKEN": "xapp-test",
            "SLACK_SIGNING_SECRET": "secret",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            get_settings.cache_clear()
            settings1 = get_settings()
            settings2 = get_settings()
            assert settings1 is settings2
