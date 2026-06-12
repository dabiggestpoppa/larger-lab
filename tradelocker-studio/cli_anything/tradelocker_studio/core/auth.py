"""
Authentication for TradeLocker Studio.

Handles JWT token flow: login → access token → refresh token.
"""

import requests
from typing import Any, Dict, Optional

from .config import get_credentials


def login(
    email: Optional[str] = None,
    password: Optional[str] = None,
    server: Optional[str] = None,
    environment: str = "demo",
) -> Dict[str, Any]:
    """
    Authenticate with TradeLocker and get JWT tokens.

    Args:
        email: TradeLocker email (or from config)
        password: TradeLocker password (or from config)
        server: TradeLocker server name (or from config)
        environment: "demo" or "live"

    Returns:
        Dict with accessToken, refreshToken, expireDate
    """
    creds = get_credentials()
    email = email or creds.get("email", "")
    password = password or creds.get("password", "")
    server = server or creds.get("server", "")

    if not all([email, password, server]):
        raise ValueError(
            "Missing credentials. Set TRADELOCKER_EMAIL, TRADELOCKER_PASSWORD, "
            "TRADELOCKER_SERVER environment variables or run 'tl-studio auth setup'."
        )

    base_url = f"https://{environment}.tradelocker.com"
    r = requests.post(
        f"{base_url}/backend-api/auth/jwt/token",
        json={"email": email, "password": password, "server": server},
        timeout=(10, 30),
    )
    r.raise_for_status()
    return r.json()


def refresh_token(refresh_token: str, environment: str = "demo") -> Dict[str, Any]:
    """Refresh an expired access token."""
    base_url = f"https://{environment}.tradelocker.com"
    r = requests.post(
        f"{base_url}/backend-api/auth/jwt/refresh",
        json={"refreshToken": refresh_token},
        timeout=(10, 30),
    )
    r.raise_for_status()
    return r.json()


def get_all_accounts(jwt_token: str, environment: str = "demo") -> Dict[str, Any]:
    """Get all accounts for the authenticated user."""
    base_url = f"https://{environment}.tradelocker.com"
    r = requests.get(
        f"{base_url}/backend-api/auth/jwt/all-accounts",
        headers={"Authorization": f"Bearer {jwt_token}"},
        timeout=(10, 30),
    )
    r.raise_for_status()
    return r.json()
