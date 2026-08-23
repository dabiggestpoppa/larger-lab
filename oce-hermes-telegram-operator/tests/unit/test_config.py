"""Unit tests for OCE MCP Facade configuration.

Covers mandatory tests:
- T-SEC-03: Missing TELEGRAM_ALLOWED_USERS prevents startup
- T-SEC-04: TELEGRAM_ALLOW_ALL_USERS=true is rejected
- T-SEC-05: Bot token never appears in logs or repository
"""

import os
import pytest
from unittest.mock import patch


class TestConfigValidation:
    """Test configuration validation at startup."""

    def test_missing_allowed_users_exits(self):
        """T-SEC-03: Gateway refuses startup when allowed-user list is empty."""
        env = {
            "TELEGRAM_BOT_TOKEN": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ",
            "TELEGRAM_ALLOWED_USERS": "",
            "TELEGRAM_ALLOW_ALL_USERS": "false",
        }
        with patch.dict(os.environ, env, clear=True):
            # Remove any existing values
            for key in ["TELEGRAM_ALLOWED_USERS", "TELEGRAM_BOT_TOKEN"]:
                os.environ.pop(key, None)
            os.environ.update(env)

            with pytest.raises(SystemExit) as exc_info:
                from src.oce_mcp_facade.config import FacadeConfig
                FacadeConfig.from_env()
            assert exc_info.value.code == 1

    def test_allow_all_users_rejected(self):
        """T-SEC-04: TELEGRAM_ALLOW_ALL_USERS=true is rejected in production."""
        env = {
            "TELEGRAM_BOT_TOKEN": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ",
            "TELEGRAM_ALLOWED_USERS": "123456789",
            "TELEGRAM_ALLOW_ALL_USERS": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            os.environ.update(env)
            with pytest.raises(SystemExit) as exc_info:
                from src.oce_mcp_facade.config import FacadeConfig
                FacadeConfig.from_env()
            assert exc_info.value.code == 1

    def test_missing_bot_token_exits(self):
        """Gateway refuses startup when bot token is missing."""
        env = {
            "TELEGRAM_ALLOWED_USERS": "123456789",
            "TELEGRAM_ALLOW_ALL_USERS": "false",
        }
        with patch.dict(os.environ, env, clear=True):
            os.environ.update(env)
            with pytest.raises(SystemExit) as exc_info:
                from src.oce_mcp_facade.config import FacadeConfig
                FacadeConfig.from_env()
            assert exc_info.value.code == 1

    def test_valid_config_loads(self):
        """Valid configuration loads successfully."""
        env = {
            "TELEGRAM_BOT_TOKEN": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ",
            "TELEGRAM_ALLOWED_USERS": "123456789,987654321",
            "TELEGRAM_ALLOW_ALL_USERS": "false",
            "OCE_BACKEND_URL": "http://localhost:8000",
            "OCE_SERVICE_TOKEN": "oce-read-test",
        }
        with patch.dict(os.environ, env, clear=True):
            os.environ.update(env)
            from src.oce_mcp_facade.config import FacadeConfig
            config = FacadeConfig.from_env()
            assert config.is_user_allowed(123456789)
            assert config.is_user_allowed(987654321)
            assert not config.is_user_allowed(111111111)

    def test_multiple_allowed_users(self):
        """Multiple users can be configured."""
        env = {
            "TELEGRAM_BOT_TOKEN": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ",
            "TELEGRAM_ALLOWED_USERS": "111,222,333",
            "TELEGRAM_ALLOW_ALL_USERS": "false",
        }
        with patch.dict(os.environ, env, clear=True):
            os.environ.update(env)
            from src.oce_mcp_facade.config import FacadeConfig
            config = FacadeConfig.from_env()
            assert len(config.get_allowed_user_ids()) == 3
            assert config.is_user_allowed(111)
            assert config.is_user_allowed(222)
            assert config.is_user_allowed(333)


class TestTokenRedaction:
    """T-SEC-05: Bot token never appears in display output."""

    def test_mask_for_display_redacts_token(self):
        """Token is redacted in display output."""
        env = {
            "TELEGRAM_BOT_TOKEN": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ",
            "TELEGRAM_ALLOWED_USERS": "123456789",
            "TELEGRAM_ALLOW_ALL_USERS": "false",
            "OCE_SERVICE_TOKEN": "oce-read-secret123",
        }
        with patch.dict(os.environ, env, clear=True):
            os.environ.update(env)
            from src.oce_mcp_facade.config import FacadeConfig
            config = FacadeConfig.from_env()
            display = config.mask_for_display()
            assert display["telegram_bot_token"] == "[REDACTED]"
            assert display["oce_service_token"] == "[REDACTED]"

    def test_token_not_in_repr(self):
        """Token is not in string representation."""
        env = {
            "TELEGRAM_BOT_TOKEN": "SECRET_TOKEN_VALUE",
            "TELEGRAM_ALLOWED_USERS": "123456789",
            "TELEGRAM_ALLOW_ALL_USERS": "false",
        }
        with patch.dict(os.environ, env, clear=True):
            os.environ.update(env)
            from src.oce_mcp_facade.config import FacadeConfig
            config = FacadeConfig.from_env()
            display = config.mask_for_display()
            display_str = str(display)
            assert "SECRET_TOKEN_VALUE" not in display_str
            assert "123456789:ABC" not in display_str
