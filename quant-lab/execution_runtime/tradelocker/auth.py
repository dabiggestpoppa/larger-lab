"""QL-EXEC-R5 — TradeLocker JWT auth provider.

- Credentials NEVER live in this module: they are resolved at call time from
  an injected secret provider (e.g. an env-var reader) keyed by reference
  names. Nothing is persisted, logged, or committed.
- Refresh is concurrency-safe via a singleflight lock: one refresh per auth
  session, no stampede.
- Access-token expiry is read from the JWT payload itself (base64 decode —
  no third-party JWT dependency) and refreshed 30 minutes before expiry,
  matching the official client's policy.
"""
from __future__ import annotations

import base64
import json
import threading
import time
from typing import Callable, Optional

from .transport import HttpRequest, HttpTransport, HttpResponse, TransportError
from .types import TradeLockerAccount, TradeLockerTokens

REFRESH_THRESHOLD_SECONDS = 30 * 60


class TradeLockerAuthError(Exception):
    """Auth failure (bad credentials, refresh failure, missing secret)."""


def decode_jwt_expiry(token: str) -> Optional[float]:
    """Return ``exp`` epoch seconds from a JWT payload (no signature verify)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1]
        padding = "=" * (-len(payload) % 4)
        raw = base64.urlsafe_b64decode(payload + padding)
        data = json.loads(raw)
        exp = data.get("exp")
        return float(exp) if exp is not None else None
    except Exception:
        return None


class TradeLockerAuthProvider:
    def __init__(
        self,
        *,
        base_url: str,
        transport: HttpTransport,
        secret_provider: Optional[Callable[[str], str]] = None,
        email_ref: str = "",
        password_ref: str = "",
        server: str = "",
        developer_api_key_ref: str = "",
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport
        self._secret_provider = secret_provider or (lambda _name: "")
        self._email_ref = email_ref
        self._password_ref = password_ref
        self._server = server
        self._developer_api_key_ref = developer_api_key_ref
        self._clock = clock or time.time

        self._access_token = ""
        self._refresh_token = ""
        self._auth_lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._last_refresh_at = 0.0
        self._refresh_count = 0
        self._auth_count = 0

    # ── secrets ───────────────────────────────────────────────────────────

    def _email(self) -> str:
        return self._secret_provider(self._email_ref) if self._email_ref else ""

    def _password(self) -> str:
        return self._secret_provider(self._password_ref) if self._password_ref else ""

    def developer_api_key(self) -> str:
        return self._secret_provider(self._developer_api_key_ref) if self._developer_api_key_ref else ""

    def has_credentials(self) -> bool:
        return bool(self._email_ref and self._password_ref and self._server)

    # ── state ─────────────────────────────────────────────────────────────

    @property
    def base_url(self) -> str:
        return self._base_url

    def tokens_present(self) -> bool:
        return bool(self._access_token and self._refresh_token)

    def access_token_expiry_seconds(self) -> Optional[float]:
        """Seconds until access-token expiry (None if unknown/no token)."""
        if not self._access_token:
            return None
        exp = decode_jwt_expiry(self._access_token)
        if exp is None:
            return None
        return exp - self._clock()

    def refresh_count(self) -> int:
        return self._refresh_count

    def auth_count(self) -> int:
        return self._auth_count

    # ── auth flow ─────────────────────────────────────────────────────────

    def authenticate(self) -> None:
        """Fetch fresh JWT tokens from ``/auth/jwt/token``.

        Requires email/password/server via injected secret provider. Raises
        ``TradeLockerAuthError`` on failure — never returns fake success.
        """
        if not self.has_credentials():
            raise TradeLockerAuthError(
                "no credential references configured (email/password/server)"
            )
        body = {
            "email": self._email(),
            "password": self._password(),
            "server": self._server,
        }
        req = HttpRequest(
            method="POST",
            url=f"{self._base_url}/auth/jwt/token",
            json_body=body,
        )
        resp = self._raw_request(req)
        if resp.status != 200:
            raise TradeLockerAuthError(f"auth failed: HTTP {resp.status} {resp.body[:200]}")
        try:
            payload = resp.json()
        except ValueError as err:
            raise TradeLockerAuthError(f"auth failed: {err}") from err
        access = payload.get("accessToken")
        refresh = payload.get("refreshToken")
        if not access or not refresh:
            raise TradeLockerAuthError("auth failed: missing accessToken/refreshToken")
        with self._auth_lock:
            self._access_token = access
            self._refresh_token = refresh
            self._auth_count += 1

    def refresh_access_token(self, force: bool = False) -> None:
        """Refresh tokens via ``/auth/jwt/refresh``. Singleflight: concurrent
        callers share ONE refresh; they never stampede the endpoint.

        ``force=True`` bypasses the local "still fresh" check — used when the
        SERVER rejected the token (401), which is the only authoritative
        signal that the local expiry estimate is wrong."""
        with self._refresh_lock:
            if not self._refresh_token:
                raise TradeLockerAuthError("cannot refresh: no refresh token")
            # A concurrent caller may have just refreshed while we waited.
            if not force and self._access_token:
                left = self.access_token_expiry_seconds()
                if left is not None and left > REFRESH_THRESHOLD_SECONDS:
                    return
            body = {"refreshToken": self._refresh_token}
            req = HttpRequest(
                method="POST",
                url=f"{self._base_url}/auth/jwt/refresh",
                json_body=body,
            )
            resp = self._raw_request(req)
            if resp.status != 200:
                raise TradeLockerAuthError(
                    f"refresh failed: HTTP {resp.status} {resp.body[:200]}"
                )
            try:
                payload = resp.json()
            except ValueError as err:
                raise TradeLockerAuthError(f"refresh failed: {err}") from err
            access = payload.get("accessToken")
            refresh = payload.get("refreshToken")
            if not access or not refresh:
                raise TradeLockerAuthError("refresh failed: missing tokens")
            self._access_token = access
            self._refresh_token = refresh
            self._last_refresh_at = self._clock()
            self._refresh_count += 1

    def get_access_token(self) -> str:
        """Return a usable access token, refreshing proactively if needed."""
        if not self._access_token:
            self.authenticate()
        left = self.access_token_expiry_seconds()
        if left is not None and left < REFRESH_THRESHOLD_SECONDS:
            self.refresh_access_token()
        if not self._access_token:
            raise TradeLockerAuthError("no access token available")
        return self._access_token

    # ── accounts (pre-account-selection) ──────────────────────────────────

    def get_all_accounts(self) -> list:
        """``/auth/jwt/all-accounts`` — read-only account discovery."""
        resp = self._authed_request(
            "GET", f"{self._base_url}/auth/jwt/all-accounts", include_acc_num=False
        )
        try:
            payload = resp.json()
        except ValueError as err:
            raise TradeLockerAuthError(f"all-accounts failed: {err}") from err
        accounts = payload.get("accounts") or []
        out = []
        for row in accounts:
            try:
                out.append(
                    TradeLockerAccount(
                        account_id=int(row["id"]),
                        acc_num=int(row["accNum"]),
                        name=str(row.get("name", "")),
                        raw=dict(row),
                    )
                )
            except (KeyError, TypeError, ValueError) as err:
                raise TradeLockerAuthError(
                    f"all-accounts row missing id/accNum: {err}"
                ) from err
        return out

    # ── internals ─────────────────────────────────────────────────────────

    def _authed_request(
        self, method: str, url: str, include_acc_num: bool = True
    ) -> HttpResponse:
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
        }
        if include_acc_num:
            # accNum is resolved by the client (auth has no account yet); the
            # caller sets it via headers if needed.
            pass
        dev_key = self.developer_api_key()
        if dev_key:
            headers["developer-api-key"] = dev_key
        req = HttpRequest(method=method, url=url, headers=headers)
        resp = self._raw_request(req)
        if resp.status == 401:
            # Token rejected → refresh once, retry once. 401 means the request
            # was NOT executed, so a single retry is safe.
            self.refresh_access_token()
            headers["Authorization"] = f"Bearer {self.get_access_token()}"
            resp = self._raw_request(HttpRequest(method=method, url=url, headers=headers))
        return resp

    def _raw_request(self, request: HttpRequest) -> HttpResponse:
        try:
            return self._transport.request(request)
        except TransportError:
            raise
