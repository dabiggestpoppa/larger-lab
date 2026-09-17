"""One-OCE boundary declarations and cross-block scenarios F0–F11."""

from __future__ import annotations

import json

import pytest

from foundry.cross_block import SCENARIOS, cross_block_report, run_all
from foundry.oce_boundary import (
    DECLARED_ONLY,
    assert_boundary_complete,
    boundary_fingerprint,
    boundary_registry,
    declaration_payload,
    module_surface,
    scan_declared_doubles,
    scan_undeclared_doubles,
)


def test_every_local_fixture_is_declared_and_replaceable() -> None:
    assert scan_undeclared_doubles() == ()
    assert_boundary_complete()
    entries = boundary_registry()
    assert len(entries) >= 8
    for entry in entries:
        assert entry.noncanonical is True
        assert entry.canonical_oce_target
        assert entry.replacement_condition
        assert entry.retirement_evidence
        assert entry.module  # either a module that declares it, or declaration-only


def test_declared_generic_services_are_not_implemented_locally() -> None:
    declared_fixtures = {entry.fixture for entry in boundary_registry()}
    # These are *declarations only*: identity/authority/artifacts are owned by OCE
    # and the Foundry builds no local implementation of them.
    assert {"FoundryLocalIdentity", "FoundryLocalAuthorityProjection", "FoundryLocalArtifactStore"} <= declared_fixtures
    assert set(DECLARED_ONLY) == {"identity", "authority", "artifacts"}
    implemented = {
        location
        for locations in scan_declared_doubles().values()
        for location in locations
    }
    for declared_only in ("FoundryLocalIdentity", "FoundryLocalAuthorityProjection", "FoundryLocalArtifactStore"):
        assert not any(declared_only in location for location in implemented)


def test_boundary_payload_is_serialisable_and_fingerprinted() -> None:
    payload = declaration_payload()
    assert payload["marker"] == "NONCANONICAL_OCE_TEST_DOUBLES"
    json.dumps(payload)
    assert payload["boundary_fingerprint"] == boundary_fingerprint()
    assert payload["boundary_fingerprint"].startswith("sha256:")


def test_module_surface_covers_every_block() -> None:
    surface = module_surface()
    assert "foundry.constitution" in surface
    assert "foundry.resources" in surface
    assert "foundry.data" in surface
    assert "foundry.refinery" in surface
    assert "foundry.evaluation" in surface
    assert "foundry.cross_block" in surface
    assert "ComputeRequest" in surface["foundry.resources"]
    assert "DatasetRefinery" in surface["foundry.refinery"]


def test_boundary_declaration_file_matches_runtime_registry() -> None:
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "fixtures" / "noncanonical_declarations.json"
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["boundary_fingerprint"] == boundary_fingerprint()


@pytest.mark.parametrize("scenario_id", sorted(SCENARIOS))
def test_each_cross_block_scenario_holds(scenario_id: str) -> None:
    result = SCENARIOS[scenario_id]()
    assert result.scenario_id == scenario_id
    assert result.status == "HELD", json.dumps(result.to_dict(), indent=2)
    assert result.observed


def test_cross_block_report_is_green_and_fingerprinted() -> None:
    report = cross_block_report()
    assert report["verdict"] == "PASS"
    assert report["scenarios_total"] == 12
    assert report["scenarios_failed"] == []
    assert report["report_fingerprint"].startswith("sha256:")


def test_cross_block_results_are_deterministic() -> None:
    first = run_all()
    second = run_all()
    assert [r.to_dict() for r in first] == [r.to_dict() for r in second]


def test_cross_block_receipt_matches_the_runtime_report() -> None:
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "receipts" / "cross-block-scenarios.json"
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    live = cross_block_report()
    assert on_disk["verdict"] == live["verdict"]
    assert on_disk["scenarios_held"] == live["scenarios_held"]
    assert on_disk["report_fingerprint"] == live["report_fingerprint"]


def test_no_scenario_invented_a_provider_or_paid_path() -> None:
    for result in run_all():
        payload = json.dumps(result.to_dict())
        assert "paid_compute_consumed\": true" not in payload
        assert "LIVE" not in payload or "LIVE_LAUNCH_NOT_AUTHORIZED" in payload


def test_every_scenario_reports_what_it_refused() -> None:
    refusals = {
        result.scenario_id: {r["code"] for r in result.refusals}
        for result in run_all()
        if result.refusals
    }
    assert refusals["F2"] == {
        "RIGHTS_BLOCKED",
        "ROLE_TRANSITION_NOOP",
        "SECRET_BEARING_SOURCE_TRAIN_ROLE_REFUSED",
    }
    assert refusals["F6"] == {"CEREBUS_FAMILY_WITHHELD"}
    assert refusals["F8"] == {
        "SEALED_ACCESS_BUILDER_REFUSED",
        "SEALED_ACCESS_TOKEN_REQUIRED",
        "SEALED_REGISTRATION_ROLE_REFUSED",
    }
    assert "BUDGET_EXCEEDED" in refusals["F11"]
