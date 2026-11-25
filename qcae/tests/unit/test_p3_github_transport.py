"""P3-T02-C01 — GitHub transport: injectable, no default live network.

Covers the transport ABC contract and the deterministic fake used to exercise
the adapter offline. No subclass in this module performs network I/O.
"""

from __future__ import annotations

import pytest

from qcae.discovery.github.transport import (
    FakeGitHubTransport,
    GitHubResponse,
    GitHubTransport,
)


class TestGitHubResponseShape:
    def test_response_carries_status_headers_body(self) -> None:
        response = GitHubResponse(status_code=200, headers={"x": "1"}, body={"items": []})
        assert response.status_code == 200
        assert response.headers == {"x": "1"}
        assert response.body == {"items": []}


class TestGitHubTransportABC:
    def test_abc_cannot_be_instantiated_directly(self) -> None:
        with pytest.raises(TypeError):
            GitHubTransport()  # type: ignore[abstract-class-instantiated]


class TestFakeGitHubTransport:
    def test_unknown_query_returns_empty_successful_page(self) -> None:
        transport = FakeGitHubTransport()
        response = transport.repository_search(q="anything", per_page=10, page=1)
        assert response.status_code == 200
        assert response.body == {"items": [], "total_count": 0}

    def test_preseeded_response_is_returned_per_kind_query_page(self) -> None:
        seeded = GitHubResponse(
            status_code=200, headers={}, body={"items": [{"full_name": "owner/repo"}]}
        )
        transport = FakeGitHubTransport(
            responses={("repository", "causal ordering", 1): seeded}
        )
        response = transport.repository_search(q="causal ordering", per_page=10, page=1)
        assert response is seeded
        # A different page or kind is not seeded -> empty page, not the seeded one.
        other = transport.repository_search(q="causal ordering", per_page=10, page=2)
        assert other.body == {"items": [], "total_count": 0}
        code = transport.code_search(q="causal ordering", per_page=10, page=1)
        assert code.body == {"items": [], "total_count": 0}

    def test_call_counts_are_recorded_for_budget_assertions(self) -> None:
        transport = FakeGitHubTransport()
        transport.repository_search(q="q", per_page=5, page=1)
        transport.repository_search(q="q", per_page=5, page=2)
        transport.code_search(q="q", per_page=5, page=1)
        assert transport.repository_calls == [("q", 5, 1), ("q", 5, 2)]
        assert transport.code_calls == [("q", 5, 1)]

    def test_no_default_live_network_operation(self) -> None:
        # The module exports no live transport; only the injectable ABC and the
        # in-memory fake. Instantiating the fake performs zero network I/O.
        transport = FakeGitHubTransport()
        assert isinstance(transport, GitHubTransport)
        transport.repository_search(q="q", per_page=5, page=1)
        # No host, session, or credential is retained by the fake.
        assert not hasattr(transport, "session")
        assert not hasattr(transport, "base_url")
