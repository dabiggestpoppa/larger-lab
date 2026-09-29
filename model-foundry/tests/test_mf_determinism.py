"""Replay stability: fingerprints must describe the substrate, not the clock.

A substrate that claims content-addressed science cannot have digests that move
when nothing scientific changed. These tests exist because the source-registry
digest originally included the wall-clock time of each registry entry, which made
the same registry fingerprint differently on every run.
"""

from __future__ import annotations

from foundry.cli import evidence_payload
from foundry.core import Receipt, VersionedRegistry
from foundry.data import SourceRegistry
from foundry.enums import SourceRole
from foundry.evaluation import freeze_protocol
from foundry.fixtures import build_registry, load_protocol, load_rights_evidence


def test_receipt_fingerprint_ignores_wall_clock() -> None:
    first = Receipt(kind="k", subject="s", payload={"a": 1})
    first.recorded_utc = "2026-01-01T00:00:00+00:00"
    second = Receipt(kind="k", subject="s", payload={"a": 1})
    second.recorded_utc = "2027-06-06T12:34:56+00:00"
    assert first.to_dict()["receipt_fingerprint"] == second.to_dict()["receipt_fingerprint"]
    assert first.to_dict()["recorded_utc"] != second.to_dict()["recorded_utc"]


def test_registry_digest_is_reproducible_for_identical_content() -> None:
    assert build_registry().digest() == build_registry().digest()
    digests = {_independent_registry().digest() for _ in range(3)}
    assert len(digests) == 1


def _independent_registry() -> SourceRegistry:
    """Rebuild the fixture registry through a different code path than the loader."""

    source = build_registry()
    registry = SourceRegistry(rights_evidence=load_rights_evidence())
    for source_id in source.source_ids():
        registry.register(
            record=source.get(source_id),
            actor="fixture.loader",
            reason="deterministic fixture load",
        )
    return registry


def test_registry_digest_changes_when_content_changes() -> None:
    baseline = build_registry().digest()
    changed = build_registry()
    changed.transition_role(
        "SRC_NEWS_ALPHA",
        SourceRole.DEV,
        actor="operator",
        reason="hold out for development evaluation",
    )
    assert changed.digest() != baseline
    assert build_registry().digest() == baseline


def test_versioned_entry_digest_payload_excludes_recorded_time() -> None:
    registry = VersionedRegistry("test_registry", build_registry().double)
    registry.put("k", {"v": 1}, actor="a", reason="r")
    entry = registry.history("k")[0]
    payload = entry.digest_payload()
    assert "recorded_utc" not in payload
    assert payload["version"] == 1
    assert entry.to_dict()["recorded_utc"]  # still recorded for humans


def test_freeze_replay_on_a_fixed_clock_is_byte_identical() -> None:
    protocol = load_protocol()
    first = freeze_protocol(
        protocol,
        registrar="test",
        freeze_reason="replay",
        candidate_outcomes_observed=False,
        actor_is_builder=False,
        now_iso="2026-01-03T00:00:00Z",
    )
    second = freeze_protocol(
        protocol,
        registrar="test",
        freeze_reason="replay",
        candidate_outcomes_observed=False,
        actor_is_builder=False,
        now_iso="2026-01-03T00:00:00Z",
    )
    assert first.to_dict() == second.to_dict()
    assert first.protocol.fingerprint == second.protocol.fingerprint


def test_evidence_package_fingerprint_is_replay_stable() -> None:
    first = evidence_payload()
    second = evidence_payload()
    assert first["evidence_fingerprint"] == second["evidence_fingerprint"]
    assert first["evidence_fingerprint"].startswith("sha256:")
    assert first["verdict"] == "PASS"
    assert first["receipt_timestamps_excluded"] is True
    # The wall clock must not reappear anywhere the fingerprint covers.
    assert "recorded_utc" not in _all_keys(first)


def _all_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key))
            keys |= _all_keys(item)
    elif isinstance(value, list):
        for item in value:
            keys |= _all_keys(item)
    return keys
