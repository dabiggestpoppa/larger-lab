"""Configuration management for OCE MCP Facade.

Loads configuration from environment variables and .env files.
Never logs secrets. Validates required fields at startup.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class FacadeConfig:
    """Immutable configuration for the OCE MCP Facade."""

    # OCE Backend connection
    oce_backend_url: str = "http://localhost:8000"
    oce_service_token: str = ""
    oce_request_timeout: int = 30  # seconds

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Telegram security
    telegram_allowed_users: str = ""
    telegram_allow_all_users: bool = False
    telegram_bot_token: str = ""

    # Logging
    log_level: str = "INFO"
    audit_log_path: str = "evidence/audit.jsonl"

    # Mock mode
    use_mock: bool = True  # Default to mock when OCE is unavailable

    @classmethod
    def from_env(cls) -> "FacadeConfig":
        """Load configuration from environment variables.

        Raises:
            SystemExit: If critical configuration is missing or invalid.
        """
        # Telegram security — fail-closed
        allowed_users = os.environ.get("TELEGRAM_ALLOWED_USERS", "").strip()
        allow_all = os.environ.get("TELEGRAM_ALLOW_ALL_USERS", "false").lower()

        if allow_all == "true":
            print(
                "FATAL: TELEGRAM_ALLOW_ALL_USERS=true is rejected in production. "
                "Set TELEGRAM_ALLOW_ALL_USERS=false.",
                file=sys.stderr,
            )
            sys.exit(1)

        if not allowed_users:
            print(
                "FATAL: TELEGRAM_ALLOWED_USERS is missing or empty. "
                "The gateway refuses to start without an explicit allowlist. "
                "Set TELEGRAM_ALLOWED_USERS to a comma-separated list of "
                "numeric Telegram user IDs.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Bot token — never log
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not bot_token:
            print(
                "FATAL: TELEGRAM_BOT_TOKEN is missing. "
                "Set it to the BotFather token for your bot.",
                file=sys.stderr,
            )
            sys.exit(1)

        # OCE backend
        backend_url = os.environ.get("OCE_BACKEND_URL", "http://localhost:8000").strip()
        service_token = os.environ.get("OCE_SERVICE_TOKEN", "").strip()

        use_mock = not bool(service_token)

        return cls(
            oce_backend_url=backend_url,
            oce_service_token=service_token,
            oce_request_timeout=int(os.environ.get("OCE_REQUEST_TIMEOUT", "30")),
            rate_limit_per_minute=int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60")),
            telegram_allowed_users=allowed_users,
            telegram_allow_all_users=False,  # Always False after validation
            telegram_bot_token=bot_token,
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            audit_log_path=os.environ.get("AUDIT_LOG_PATH", "evidence/audit.jsonl"),
            use_mock=use_mock,
        )

    def get_allowed_user_ids(self) -> list[int]:
        """Parse allowed user IDs from comma-separated string."""
        if not self.telegram_allowed_users:
            return []
        return [int(uid.strip()) for uid in self.telegram_allowed_users.split(",") if uid.strip()]

    def is_user_allowed(self, user_id: int) -> bool:
        """Check if a Telegram user ID is in the allowlist."""
        return user_id in self.get_allowed_user_ids()

    def mask_for_display(self) -> dict:
        """Return config values safe for display (no secrets)."""
        return {
            "oce_backend_url": self.oce_backend_url,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "use_mock": self.use_mock,
            "log_level": self.log_level,
            "audit_log_path": self.audit_log_path,
            "allowed_user_count": len(self.get_allowed_user_ids()),
            "telegram_bot_token": "[REDACTED]",
            "oce_service_token": "[REDACTED]" if self.oce_service_token else "[NOT SET]",
        }
