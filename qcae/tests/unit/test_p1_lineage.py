"""P1-C04 — lineage + contradiction persistence evidence (§10, tests 26–28)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.ports.lineage import LineageEdge, LineageEdgeType
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.persistence.sqlite_lineage_store import (
    SqliteLineageRepository,
    LINEAGE_DDL,
)


@pytest.fixture()
def repo():
    conn = open_metadata_db(":memory:")
    conn.executescript(LINEAGE_DDL)
    yield SqliteLineageRepository(conn)
    conn.close()


def _edge(src="ev-1", et=LineageEdgeType.SUPPORTS, dst="atom-x", **over) -> LineageEdge:
    defaults = dict(
        src_id=src,
        src_kind="evidence",
        edge_type=et,
        dst_id=dst,
        dst_kind="candidate",
        created_at="2026-09-12T00:00:00Z",
        rationale="",
    )
    defaults.update(over)
    return LineageEdge(**defaults)


class TestEdgePersistence:
    def test_supports_edge_round_trip(self, repo) -> None:
        repo.add(_edge())
        repo.add(_edge(et=LineageEdgeType.DERIVED_FROM, dst="ev-0", dst_kind="evidence"))
        out = repo.edges_from("ev-1")
        assert {e.edge_type for e in out} == {
            LineageEdgeType.SUPPORTS,
            LineageEdgeType.DERIVED_FROM,
        }

    def test_edges_to_reverse_lookup(self, repo) -> None:
        repo.add(_edge(dst="ev-9", dst_kind="evidence"))
        hits = repo.edges_to("ev-9")
        assert len(hits) == 1 and hits[0].src_id == "ev-1"

    def test_duplicate_edge_idempotent(self, repo) -> None:
        repo.add(_edge())
        repo.add(_edge())  # same src/type/dst/kind: no-op, not error
        assert len(repo.edges_from("ev-1")) == 1

    def test_all_book_iv_edge_types_accepted(self, repo) -> None:
        for i, et in enumerate(LineageEdgeType):
            repo.add(_edge(src=f"ev-{i}", dst=f"t-{i}", dst_kind="candidate", et=et))
        assert len(repo.all_edges()) == len(LineageEdgeType)


class TestContradictionPreservation:
    def test_contradictory_claims_coexist(self, repo) -> None:
        """Neither side is deleted or demoted; both remain queryable."""
        repo.add(_edge(src="ev-a", et=LineageEdgeType.SUPPORTS, dst="claim-x", dst_kind="evidence"))
        repo.add(_edge(src="ev-b", et=LineageEdgeType.CONTRADICTS, dst="claim-x", dst_kind="evidence"))
        pro = repo.edges_to("claim-x")
        contra = repo.contradictions_of("claim-x")
        assert {e.src_id for e in pro} == {"ev-a", "ev-b"}
        assert {e.src_id for e in contra} == {"ev-b"}

    def test_contradiction_visible_in_both_directions(self, repo) -> None:
        repo.add(_edge(src="ev-b", et=LineageEdgeType.CONTRADICTS, dst="claim-x", dst_kind="evidence"))
        assert repo.contradictions_of("claim-x")
        assert repo.contradictions_of("ev-b")

    def test_no_silent_resolution(self, repo) -> None:
        """There is no API to delete or 'winnow' a contradiction edge."""
        assert not hasattr(repo, "delete")
        assert not hasattr(repo, "resolve")


class TestEndpointValidation:
    def test_illegal_kind_rejected(self, repo) -> None:
        with pytest.raises(QcaeValidationError, match="kinds"):
            repo.add(_edge(src_kind="vibes"))

    def test_self_edge_rejected(self, repo) -> None:
        with pytest.raises(QcaeValidationError, match="itself"):
            repo.add(_edge(src="ev-1", dst="ev-1", dst_kind="evidence"))

    def test_supersession_chain_query(self, repo) -> None:
        repo.add(_edge(src="ev-2", et=LineageEdgeType.SUPERSEDES, dst="ev-1", dst_kind="evidence"))
        repo.add(_edge(src="ev-3", et=LineageEdgeType.SUPERSEDES, dst="ev-2", dst_kind="evidence"))
        chain = repo.supersession_chain("ev-2")
        assert {e.src_id for e in chain} == {"ev-2", "ev-3"}
