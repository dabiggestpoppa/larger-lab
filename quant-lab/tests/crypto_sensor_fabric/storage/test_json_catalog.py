"""SENSOR-B4-I05R1A — durable atomic JSON catalog primitive tests.

Covers the R1A durability contract (I05R1 §4-§10, §46):

- durable publication order (canonical catalog-commit operation sequence);
- idempotent reuse for identical content;
- typed conflict for same logical ID + differing content;
- corruption NEVER disappears (bad JSON / non-object / missing logical id /
  masquerading filename all fail closed);
- safe physical keys: raw logical IDs never touch the filesystem namespace;
- crash matrix at every injected fault boundary;
- concurrent writer adoption only on byte-identical content.
"""

from __future__ import annotations

import json
import os

import pytest

from crypto_sensor_fabric.storage.atomic import (
    OP_ATOMIC_PUBLISH,
    OP_PARENT_DIR_FSYNC,
    ListOpRecorder,
    is_canonical_durable_order,
)
from crypto_sensor_fabric.storage.json_catalog import (
    CATALOG_OP_DIR_FSYNC,
    CATALOG_OP_FILE_FSYNC,
    CATALOG_OP_PUBLISH,
    CATALOG_OP_STAGE_WRITE,
    CATALOG_OP_SUCCESS,
    CATALOG_OP_VERIFY,
    CatalogFaultHook,
    CatalogFaultPoint,
    DurableJsonCatalog,
    FaultError,
    JsonCatalogConflict,
    JsonCatalogCorrupt,
    JsonCatalogInvalidIdentity,
    canonical_json_bytes,
    catalog_physical_key,
    is_canonical_catalog_commit_order,
)


@pytest.fixture()
def catalog_root(tmp_path):
    root = tmp_path / "catalog"
    root.mkdir()
    return root


def _make(catalog_root, **kwargs) -> DurableJsonCatalog:
    return DurableJsonCatalog(
        catalog_root, logical_id_field=kwargs.pop("logical_id_field", "id"), **kwargs
    )


# ---------------------------------------------------------------------------
# Safe physical keys (§8/§10)
# ---------------------------------------------------------------------------


class TestCatalogPhysicalKey:
    def test_full_hex_sha256_suffix(self) -> None:
        key = catalog_physical_key("proj-1")
        assert len(key) == 64 + len(".json")
        assert key.endswith(".json")
        hexpart = key[: -len(".json")]
        assert hexpart == hexpart.lower()
        int(hexpart, 16)  # pure hex

    def test_deterministic(self) -> None:
        assert catalog_physical_key("a/b") == catalog_physical_key("a/b")

    def test_distinct_ids_distinct_keys(self) -> None:
        assert catalog_physical_key("a/b") != catalog_physical_key("a_b")

    def test_traversal_identity_never_escapes(self, catalog_root) -> None:
        cat = _make(catalog_root)
        evil = "../../evil"
        cat.commit(evil, {"id": evil, "v": 1})
        # The only files under the root are 64-hex names; nothing escaped.
        names = [p.name for p in catalog_root.glob("**/*") if p.is_file()]
        assert names == [catalog_physical_key(evil)]
        assert not (catalog_root.parent / "evil.json").exists()

    def test_empty_identity_rejected(self) -> None:
        with pytest.raises(JsonCatalogInvalidIdentity):
            catalog_physical_key("")

    def test_nul_identity_rejected(self) -> None:
        with pytest.raises(JsonCatalogInvalidIdentity):
            catalog_physical_key("a\x00b")


# ---------------------------------------------------------------------------
# Durable publication + idempotence + conflict (§5/§6/§21)
# ---------------------------------------------------------------------------


class TestDurableCommit:
    def test_commit_roundtrip(self, catalog_root) -> None:
        cat = _make(catalog_root)
        payload = {"id": "lineage-1", "entries": [1, 2, 3]}
        committed = cat.commit("lineage-1", payload)
        assert committed == payload
        assert cat.get("lineage-1") == payload
        assert cat.has("lineage-1")

    def test_canonical_commit_order(self, catalog_root) -> None:
        ops = ListOpRecorder()
        cat = _make(catalog_root, ops=ops)
        cat.commit("x", {"id": "x"})
        tags = ops.ops
        assert is_canonical_catalog_commit_order(tags)
        # Frozen durability milestone order (I05R1 §5): staged write -> file
        # fsync -> verify -> no-clobber atomic publish -> parent-dir fsync ->
        # catalog dir fsync -> success.  The publication-internal tags
        # (device_check, final_link, final_parent_fsync, staging_cleanup) sit
        # between atomic_publish and the caller's dir-fsync/success.
        milestones = [
            CATALOG_OP_STAGE_WRITE,
            CATALOG_OP_FILE_FSYNC,
            CATALOG_OP_VERIFY,
            CATALOG_OP_PUBLISH,
            OP_ATOMIC_PUBLISH,
            OP_PARENT_DIR_FSYNC,
            CATALOG_OP_DIR_FSYNC,
            CATALOG_OP_SUCCESS,
        ]
        positions = [tags.index(m) for m in milestones]
        assert positions == sorted(positions)

    def test_persisted_bytes_are_canonical(self, catalog_root) -> None:
        cat = _make(catalog_root)
        payload = {"id": "x", "b": 2, "a": 1}
        cat.commit("x", payload)
        path = catalog_root / catalog_physical_key("x")
        assert path.read_bytes() == canonical_json_bytes(payload)

    def test_idempotent_same_content(self, catalog_root) -> None:
        cat = _make(catalog_root)
        p1 = {"id": "x", "v": 1}
        p2 = {"v": 1, "id": "x"}  # key order must not matter
        cat.commit("x", p1)
        assert cat.commit("x", p2)["id"] == "x"

    def test_conflict_different_content(self, catalog_root) -> None:
        cat = _make(catalog_root)
        cat.commit("x", {"id": "x", "v": 1})
        with pytest.raises(JsonCatalogConflict):
            cat.commit("x", {"id": "x", "v": 2})

    def test_conflict_preserves_original(self, catalog_root) -> None:
        cat = _make(catalog_root)
        cat.commit("x", {"id": "x", "v": 1})
        with pytest.raises(JsonCatalogConflict):
            cat.commit("x", {"id": "x", "v": 2})
        assert cat.get("x") == {"id": "x", "v": 1}

    def test_payload_id_binding_enforced(self, catalog_root) -> None:
        cat = _make(catalog_root)
        with pytest.raises(JsonCatalogInvalidIdentity):
            cat.commit("x", {"id": "y"})


# ---------------------------------------------------------------------------
# Corruption fail-closed (§7/§9)
# ---------------------------------------------------------------------------


class TestCorruptionFailClosed:
    def _commit_one(self, catalog_root) -> None:
        cat = _make(catalog_root)
        cat.commit("x", {"id": "x", "v": 1})

    def test_invalid_json_fails_closed(self, catalog_root) -> None:
        self._commit_one(catalog_root)
        (catalog_root / catalog_physical_key("x")).write_text("{not json", encoding="utf-8")
        with pytest.raises(JsonCatalogCorrupt):
            _make(catalog_root)

    def test_non_object_json_fails_closed(self, catalog_root) -> None:
        self._commit_one(catalog_root)
        (catalog_root / catalog_physical_key("x")).write_text("[1,2]", encoding="utf-8")
        with pytest.raises(JsonCatalogCorrupt):
            _make(catalog_root)

    def test_missing_logical_id_fails_closed(self, catalog_root) -> None:
        self._commit_one(catalog_root)
        (catalog_root / catalog_physical_key("x")).write_text('{"v": 1}', encoding="utf-8")
        with pytest.raises(JsonCatalogCorrupt):
            _make(catalog_root)

    def test_masquerading_filename_fails_closed(self, catalog_root) -> None:
        self._commit_one(catalog_root)
        src = catalog_root / catalog_physical_key("x")
        dst = catalog_root / catalog_physical_key("y")
        os.replace(src, dst)
        with pytest.raises(JsonCatalogCorrupt):
            _make(catalog_root)  # stored id "x" does not bind to y's filename

    def test_corrupt_entry_never_silently_disappears(self, catalog_root) -> None:
        self._commit_one(catalog_root)
        good = _make(catalog_root)
        good.commit("y", {"id": "y"})
        (catalog_root / catalog_physical_key("x")).write_text("{", encoding="utf-8")
        with pytest.raises(JsonCatalogCorrupt):
            _make(catalog_root)  # NOT a silent skip of x

    # Windows chmod only toggles the read-only attribute; POSIX permission
    # enforcement (and therefore this unreadable-fragment case) is POSIX-only.
    @pytest.mark.skipif(os.name == "nt", reason="POSIX permission semantics")
    def test_unreadable_fragment_fails_closed(self, catalog_root) -> None:
        self._commit_one(catalog_root)
        path = catalog_root / catalog_physical_key("x")
        os.chmod(path, 0o000)  # unreadable
        try:
            with pytest.raises(JsonCatalogCorrupt):
                _make(catalog_root)
        finally:
            os.chmod(path, 0o644)


# ---------------------------------------------------------------------------
# Crash matrix (§46)
# ---------------------------------------------------------------------------


class TestCatalogCrashMatrix:
    def _points(self) -> list[CatalogFaultPoint]:
        return [
            CatalogFaultPoint.BEFORE_STAGED_WRITE,
            CatalogFaultPoint.AFTER_WRITE_BEFORE_FSYNC,
            CatalogFaultPoint.AFTER_FSYNC_BEFORE_VERIFY,
            CatalogFaultPoint.AFTER_VERIFY_BEFORE_PUBLISH,
            CatalogFaultPoint.AFTER_PUBLISH_BEFORE_DIR_FSYNC,
            CatalogFaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN,
        ]

    # Fault points BEFORE publication: nothing final may exist.
    PRE_PUBLISH_POINTS = [
        CatalogFaultPoint.BEFORE_STAGED_WRITE,
        CatalogFaultPoint.AFTER_WRITE_BEFORE_FSYNC,
        CatalogFaultPoint.AFTER_FSYNC_BEFORE_VERIFY,
        CatalogFaultPoint.AFTER_VERIFY_BEFORE_PUBLISH,
    ]

    # Fault points AFTER publication (I03 crash doctrine): the final object
    # exists as PRESERVED CRASH EVIDENCE — publication happened, durability
    # was not yet proven in the crashing process.  No success was claimed
    # (the commit raised), and the fragment is never deleted automatically.
    POST_PUBLISH_POINTS = [
        CatalogFaultPoint.AFTER_PUBLISH_BEFORE_DIR_FSYNC,
        CatalogFaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN,
    ]

    def test_every_fault_point_fails_before_success(self, catalog_root) -> None:
        for point in self._points():
            sub = catalog_root / point.name
            sub.mkdir()
            hook = CatalogFaultHook(point)
            cat = _make(sub, fault_hooks=hook)
            with pytest.raises(FaultError):
                cat.commit("x", {"id": "x", "v": 1})
            # Nothing may be claimed as committed in the crashing process.
            assert not cat.has("x")
            final = sub / catalog_physical_key("x")
            if point in self.PRE_PUBLISH_POINTS:
                assert not final.exists()
            else:
                assert final.exists()  # preserved crash evidence

    def test_success_after_full_sequence(self, catalog_root) -> None:
        cat = _make(catalog_root, fault_hooks=CatalogFaultHook())  # no faults
        cat.commit("x", {"id": "x", "v": 1})
        assert cat.has("x")
        assert (catalog_root / catalog_physical_key("x")).exists()

    def test_no_fault_leftover_staging_poisons_later_commit(self, catalog_root) -> None:
        hook = CatalogFaultHook(CatalogFaultPoint.AFTER_VERIFY_BEFORE_PUBLISH)
        cat = _make(catalog_root, fault_hooks=hook)
        with pytest.raises(FaultError):
            cat.commit("x", {"id": "x", "v": 1})
        # Retry without fault: commit succeeds despite leftover staging.
        cat2 = _make(catalog_root)
        cat2.commit("x", {"id": "x", "v": 1})
        assert cat2.has("x")


# ---------------------------------------------------------------------------
# Concurrency (§47 at the primitive level)
# ---------------------------------------------------------------------------


class TestConcurrentAdoption:
    def test_adopt_existing_identical_file(self, catalog_root) -> None:
        # First writer commits durably...
        writer1 = _make(catalog_root)
        writer1.commit("x", {"id": "x", "v": 1})
        # ...second writer (separate instance) commits the same payload.
        writer2 = _make(catalog_root)
        assert writer2.commit("x", {"id": "x", "v": 1})["id"] == "x"

    def test_conflict_with_existing_differing_file(self, catalog_root) -> None:
        writer1 = _make(catalog_root)
        writer1.commit("x", {"id": "x", "v": 1})
        # Simulate a divergent fragment that binds correctly to "x".
        (catalog_root / catalog_physical_key("x")).write_text(
            json.dumps({"id": "x", "v": 2}, sort_keys=True), encoding="utf-8"
        )
        fresh = _make(catalog_root)
        with pytest.raises(JsonCatalogConflict):
            fresh.commit("x", {"id": "x", "v": 3})

    def test_uncached_existing_identical_file_adopted(self, catalog_root) -> None:
        cat = _make(catalog_root)
        payload = {"id": "z", "v": 9}
        final = catalog_root / catalog_physical_key("z")
        final.write_bytes(canonical_json_bytes(payload))
        # New instance loads it; commit is idempotent.
        fresh = _make(catalog_root)
        assert fresh.commit("z", payload) == payload
