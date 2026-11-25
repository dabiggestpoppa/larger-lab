"""GitHub transport for repository/code discovery — P3-T02 C01.

The transport owns the provider's network surface: request building, pagination,
rate-limit header reading, and raw response return. It is injectable so the
adapter can be tested with a fake transport and never performs live network I/O
by default.

Canon 2.2.12/2.2.13: pagination is explicit, pages inspected are tracked, and a
partial search is labeled partial rather than represented as exhaustive.
Book III 5.6: egress is a controlled boundary — no default live-network
operation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GitHubResponse:
    """Raw provider response; the adapter interprets it, never the transport."""

    status_code: int
    headers: dict
    body: object


class GitHubTransport(ABC):
    """Injectable GitHub transport.

    Substitutions (a fake for tests/offline qualification, a live client for
    production) implement the two search surfaces. The base type performs no
    network I/O and holds no credentials.

    No subclass here performs live network calls: shipping a default live
    transport would let composition accidentally egress to github.com. A live
    transport is an explicit, separate integration decision (P3-T03+).
    """

    @abstractmethod
    def repository_search(self, *, q: str, per_page: int, page: int) -> GitHubResponse:
        """Search repositories; return the raw provider response."""

    @abstractmethod
    def code_search(self, *, q: str, per_page: int, page: int) -> GitHubResponse:
        """Search code; return the raw provider response."""

    def rate_limit_remaining(self, response: GitHubResponse) -> Optional[int]:
        """Read remaining allowance from response headers when available."""
        raw = (
            response.headers.get("X-RateLimit-Remaining")
            or response.headers.get("x-ratelimit-remaining")
        )
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def rate_limit_reset(self, response: GitHubResponse) -> Optional[int]:
        """Read the reset epoch from response headers when available."""
        raw = (
            response.headers.get("X-RateLimit-Reset")
            or response.headers.get("x-ratelimit-reset")
        )
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None


class FakeGitHubTransport(GitHubTransport):
    """Deterministic in-memory transport for tests and offline qualification.

    Pre-seeded responses are returned per (search kind, query, page); call
    counts are recorded so tests can assert source-call budget exhaustion and
    pagination behavior. Unknown queries return an empty successful page.
    """

    def __init__(self, responses=None) -> None:
        self._responses: dict = dict(responses or {})
        self.repository_calls: list = []
        self.code_calls: list = []

    def repository_search(self, *, q: str, per_page: int, page: int) -> GitHubResponse:
        self.repository_calls.append((q, per_page, page))
        response = self._responses.get(("repository", q, page))
        if response is None:
            response = GitHubResponse(status_code=200, headers={}, body={"items": [], "total_count": 0})
        return response

    def code_search(self, *, q: str, per_page: int, page: int) -> GitHubResponse:
        self.code_calls.append((q, per_page, page))
        response = self._responses.get(("code", q, page))
        if response is None:
            response = GitHubResponse(status_code=200, headers={}, body={"items": [], "total_count": 0})
        return response
