"""P1-R1-C02 — RepositoryRegistry substrate evidence (spec §12 items 16–21)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.registry import (
    RepositoryRecord,
    RepositorySourceKind,
    RepositoryStatus,
)
from qcae.infrastructure.persistence.sqlite_repository_registry import (
    REPOSITORY_REGISTRY_DDL,
    SqliteRepositoryRegistry,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db


@pytest.fixture()
def reg():
    conn = open_metadata_db(":memory:")
    conn.executescript(REPOSITORY_REGISTRY_DDL)
    yield SqliteRepositoryRegistry(conn), conn
    conn.close()


def _repo(rid="repo-001", **over) -> RepositoryRecord:
    defaults = dict(
        repository_id=rid,
        source_kind=RepositorySourceKind.GIT,
        canonical_locator="git+https://example.com/owner/impl-a",
        revision="abc123",
        display_name="impl-a",
        provenance="manual-entry",
        first_seen_at="2026-09-12T00:00:00Z",
        last_observed_at="2026-09-12T00:00:00Z",
    )
    defaults.update(over)
    return RepositoryRecord(**defaults)


class TestRepositoryRecord:
    def test_round_trip(self) -> None:
        r = _repo()
        assert RepositoryRecord.from_dict(r.to_dict()) == r

    def test_provider_neutral_kinds_representable(self) -> None:
        """GitHub URL, package coordinate, local path, paper implementation —
        all representable without GitHub being the ontology."""
        variants = [
            _repo("repo-gh", canonical_locator="git+https://github.com/owner/x", revision="d1"),
            _repo("repo-pkg", source_kind=RepositorySourceKind.PACKAGE,
                  canonical_locator="pkg:pypi/quantlib@1.32", revision="1.32"),
            _repo("repo-local", source_kind=RepositorySourceKind.LOCAL_PATH,
                  canonical_locator="file:///C:/work/checkout", revision="working-tree"),
            _repo("repo-paper", source_kind=RepositorySourceKind.PAPER_IMPL,
                  canonical_locator="paper:arXiv:2401.00001", revision="v1"),
        ]
        for r in variants:
            r.validate()
            assert RepositoryRecord.from_dict(r.to_dict()) == r

    def test_invalid_locator_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="canonical_locator"):
            _repo(canonical_locator="").validate()

    def test_invalid_revision_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="revision"):
            _repo(revision="").validate()

    def test_self_supersession_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="supersede itself"):
            _repo(supersedes_record="repo-001").validate()

    def test_unknown_source_kind_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="source_kind"):
            _repo(source_kind="GITHUB_HUB").validate()


class TestRepositoryRegistry:
    def test_add_and_get_by_id(self, reg) -> None:
        registry, _ = reg
        registry.add(_repo())
        loaded = registry.get("repo-001")
        assert loaded is not None
        assert loaded.canonical_locator == "git+https://example.com/owner/impl-a"

    def test_get_by_canonical_locator(self, reg) -> None:
        registry, _ = reg
        registry.add(_repo())
        hit = registry.get_by_locator(
            RepositorySourceKind.GIT, "git+https://example.com/owner/impl-a")
        assert hit is not None and hit.repository_id == "repo-001"

    def test_multiple_revisions_coexist(self, reg) -> None:
        """A new observation is a new record; latest does not delete prior."""
        registry, _ = reg
        registry.add(_repo("repo-r1", revision="abc123"))
        registry.add(_repo("repo-r2", revision="def456",
                           last_observed_at="2026-09-13T00:00:00Z"))
        revs = registry.list_revisions(
            RepositorySourceKind.GIT, "git+https://example.com/owner/impl-a")
        assert {r.revision for r in revs} == {"abc123", "def456"}
        assert registry.get("repo-r1") is not None  # prior revision retained

    def test_pinned_revision_lookup(self, reg) -> None:
        registry, _ = reg
        registry.add(_repo("repo-r1", revision="abc123"))
        registry.add(_repo("repo-r2", revision="def456"))
        hit = registry.get_by_locator(
            RepositorySourceKind.GIT, "git+https://example.com/owner/impl-a",
            revision="def456")
        assert hit is not None and hit.repository_id == "repo-r2"

    def test_source_kind_filter(self, reg) -> None:
        registry, _ = reg
        registry.add(_repo("repo-git", source_kind=RepositorySourceKind.GIT))
        registry.add(_repo("repo-pkg", source_kind=RepositorySourceKind.PACKAGE,
                           canonical_locator="pkg:pypi/x@1.0", revision="1.0"))
        kinds = {r.source_kind for r in registry.list_by_source_kind(RepositorySourceKind.PACKAGE)}
        assert kinds == {RepositorySourceKind.PACKAGE}

    def test_identity_key_reuse_with_different_content_rejected(self, reg) -> None:
        registry, _ = reg
        registry.add(_repo("repo-001"))
        with pytest.raises(QcaeValidationError, match="conflicts"):
            registry.add(_repo("repo-001", display_name="different record"))

    def test_identical_readd_idempotent(self, reg) -> None:
        registry, _ = reg
        registry.add(_repo("repo-001"))
        registry.add(_repo("repo-001"))  # identical content: no-op
        assert registry.count() == 1

    def test_tampered_row_detected(self, reg) -> None:
        registry, conn = reg
        registry.add(_repo())
        conn.commit()
        conn.execute(
            "UPDATE repository_record SET payload_json = json_set(payload_json,"
            " '$.canonical_locator', 'git+https://evil.example/forged')"
            " WHERE repository_id='repo-001'")
        conn.commit()
        with pytest.raises(QcaeValidationError, match="integrity"):
            registry.get("repo-001")

    def test_restart_persistence(self, tmp_path) -> None:
        db = tmp_path / "repo.db"
        c1 = open_metadata_db(db)
        c1.executescript(REPOSITORY_REGISTRY_DDL)
        SqliteRepositoryRegistry(c1).add(_repo())
        c1.commit()
        c1.close()
        c2 = open_metadata_db(db)
        loaded = SqliteRepositoryRegistry(c2).get("repo-001")
        assert loaded is not None and loaded.revision == "abc123"
        c2.close()
