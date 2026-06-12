"""
Configuration loader for TradeLocker Studio CLI.

Loads credentials and settings from environment or config file.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR = Path.home() / ".tradelocker-studio"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> Dict[str, Any]:
    """Load configuration from file and environment."""
    config: Dict[str, Any] = {}

    # Load from config file if exists
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config = json.load(f)

    # Environment variables override file config
    env_mappings = {
        "TRADELOCKER_ENV": "environment",  # "demo" or "live"
        "TRADELOCKER_EMAIL": "email",
        "TRADELOCKER_PASSWORD": "password",
        "TRADELOCKER_SERVER": "server",
        "TRADELOCKER_ACCOUNT_ID": "account_id",
        "TRADELOCKER_ACC_NUM": "acc_num",
        "TRADELOCKER_STUDIO_HOST": "studio_host",
        "TRADELOCKER_JWT_TOKEN": "jwt_token",
        "TRADELOCKER_REFRESH_TOKEN": "refresh_token",
    }

    for env_key, config_key in env_mappings.items():
        val = os.environ.get(env_key)
        if val is not None:
            config[config_key] = val

    return config


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_studio_host() -> str:
    """Get the Studio engine host URL."""
    config = load_config()
    return config.get("studio_host", "http://127.0.0.1:53163")


def get_credentials() -> Dict[str, str]:
    """Get TradeLocker credentials."""
    config = load_config()
    return {
        "email": config.get("email", ""),
        "password": config.get("password", ""),
        "server": config.get("server", ""),
        "environment": config.get("environment", "demo"),
    }


def get_account_info() -> Dict[str, Any]:
    """Get TradeLocker account info."""
    config = load_config()
    return {
        "account_id": config.get("account_id"),
        "acc_num": config.get("acc_num"),
        "jwt_token": config.get("jwt_token", ""),
        "refresh_token": config.get("refresh_token", ""),
    }
