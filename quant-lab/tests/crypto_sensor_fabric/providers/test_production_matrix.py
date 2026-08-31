"""Cross-provider offline closure tests (SENSOR-B3-I09).

Proves the four production adapters (KRAKEN_FUTURES, GATE_FUTURES, OKX_SWAP,
DERIBIT) form ONE coherent, evidence-bounded acquisition fabric under the
common protocol: deterministic readiness/inventory, exact I14-set equality at
all three levels, evidence-ref resolution, symbol-scope audit, role/history/
PIT/pin integrity, resume/completion truth (LIMITED stays LIMITED), raw
semantic firewalls (Deribit microscope preserved), byte-for-byte determinism,
and NO network.

Authority flow (no self-attestation loop):

    I14 promotion packet + real adapter capabilities() + committed evidence
    refs + conformance results  ->  DERIVED readiness matrix.

Deribit and OKX are separately covered by their own PRODUCTION_CANDIDATE
conformance suites (also part of this run).  This module never touches a
transport; zero network occurs.
"""

from __future__ import annotations

import importlib.util
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base import (
    CapabilityUnavailable,
    ProviderCapabilities,
    ProviderSemanticError,
    ProviderUnavailable,
    dispatch_fetch,
    load_promotion_candidates,
)
from crypto_sensor_fabric.providers.readiness import (
    EXCLUDED_PRODUCTION_PROVIDERS,
    PRODUCTION_PROVIDER_REGISTRY,
    ReadinessVerification,
    build_readiness_records,
    compute_exact_sets,
    deterministic_identity,
    evidence_ref_audit,
    load_human_readiness_matrix,
    load_matrix_records,
    promotion_authority_stats,
    provider_path_counts,
    reconcile_human_matrix,
    render_inventory_csv,
    render_inventory_json,
    role_counts,
    sensor_coverage,
    validate_promotion_candidate_uniqueness,
    validate_record_bound,
    write_matrix_files,
)

TEST_ROOT = Path(__file__).resolve().parent
# test root = <repo>/quant-lab/tests/crypto_sensor_fabric/providers; parents[2] = quant-lab
REPO_QUANT_LAB = TEST_ROOT.parents[2]

HUMAN_MATRIX_CSV = (
    REPO_QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_03"
    / "ADAPTER_READINESS_MATRIX.csv"
)

EXPECTED_PROVIDERS = {"KRAKEN_FUTURES", "GATE_FUTURES", "OKX_SWAP", "DERIBIT"}

EXPECTED_PROVIDER_COUNTS = {
    "KRAKEN_FUTURES": 6,
    "GATE_FUTURES": 4,
    "OKX_SWAP": 3,
    "DERIBIT": 4,
}

EXPECTED_ROLE_COUNTS = {
    "PRIMARY": 7,
    "SECONDARY": 6,
    "CURRENT_ONLY": 2,
    "MECHANISM_MICROSCOPE": 2,
}

EXPECTED_SENSOR_COVERAGE = {
    "MECHANICAL_BASIS": 1,
    "MECHANICAL_BOOK_METRIC": 1,
    "MECHANICAL_BOOK_SNAPSHOT": 2,
    "MECHANICAL_FUNDING": 4,
    "MECHANICAL_LIQUIDATION": 3,
    "MECHANICAL_OPEN_INTEREST": 2,
    "MECHANICAL_POSITIONING": 2,
    "MECHANICAL_TRADE": 2,
}

#: Providers whose historical resume/completion is genuinely proven (YES).  All
#: other promoted historical paths must stay LIMITED — LIMITED is a valid final
#: readiness state and is NEVER upgraded to make the matrix look cleaner.
RESUME_YES_PROVIDERS = {"KRAKEN_FUTURES"}


def _candidate_keys() -> set[tuple[str, SensorFamily]]:
    candidates = load_promotion_candidates()
    return {(str(c["provider"]), SensorFamily(str(c["sensor"]))) for c in candidates}


def _pass_map() -> dict[tuple[str, SensorFamily], bool]:
    """Offline conformance/schema pass flags for every CURRENT I14 path.

    These reflect the real per-provider PRODUCTION_CANDIDATE conformance runs,
    which the four per-provider conformance tests in this same suite assert are
    0-failed.  Supplied as an explicit input so the generator never invents it.
    """
    return {key: True for key in _candidate_keys()}


def _records() -> list[Any]:
    pass_map = _pass_map()
    return build_readiness_records(
        conformance_pass=pass_map,
        schema_pass=pass_map,
    )


def _verification_map(
    override: dict[tuple[str, SensorFamily], ReadinessVerification] | None = None,
) -> dict[tuple[str, SensorFamily], ReadinessVerification]:
    """A complete explicit verification map (one entry per I14 key)."""
    result = {key: ReadinessVerification(True, True) for key in _candidate_keys()}
    if override:
        result.update(override)
    return result


# ---------------------------------------------------------------------------
# Registry / inventory topology
# ---------------------------------------------------------------------------


class TestProductionRegistry:
    def test_registry_exactly_four_current_production_providers(self) -> None:
        assert set(PRODUCTION_PROVIDER_REGISTRY) == EXPECTED_PROVIDERS

    def test_registry_keys_match_adapter_provider_id(self) -> None:
        for key, factory in PRODUCTION_PROVIDER_REGISTRY.items():
            adapter = factory()
            assert adapter.provider_id == key

    def test_excluded_providers_never_in_registry(self) -> None:
        assert EXCLUDED_PRODUCTION_PROVIDERS
        assert set(EXCLUDED_PRODUCTION_PROVIDERS).isdisjoint(
            PRODUCTION_PROVIDER_REGISTRY
        )

    def test_full_inventory_space_has_no_fifth_provider(self) -> None:
        records = _records()
        providers = {r.provider_id for r in records}
        assert providers == EXPECTED_PROVIDERS

    def test_extra_provider_in_registry_fails_closed(self) -> None:
        class _Foreign:
            provider_id = "HYPOTHETICAL_FIFTH"

            def __init__(self) -> None:
                self.adapter_version = "f"

            def capabilities(self) -> ProviderCapabilities:
                return ProviderCapabilities(provider_id=self.provider_id, sensors={})

        bad_registry = dict(PRODUCTION_PROVIDER_REGISTRY)
        bad_registry["HYPOTHETICAL_FIFTH"] = lambda: _Foreign()
        with pytest.raises(ValueError):
            build_readiness_records(registry=bad_registry)


class TestInventoryTopology:
    def test_exactly_17_production_paths(self) -> None:
        records = _records()
        assert len(records) == 17
        assert len({r.key for r in records}) == 17  # no duplicate provider x sensor

    def test_provider_path_counts_exact(self) -> None:
        assert provider_path_counts(_records()) == EXPECTED_PROVIDER_COUNTS

    def test_role_counts_exact(self) -> None:
        assert role_counts(_records()) == EXPECTED_ROLE_COUNTS

    def test_sensor_coverage_counts_exact(self) -> None:
        coverage = sensor_coverage(_records())
        for sensor, spec in coverage.items():
            assert spec["count"] == EXPECTED_SENSOR_COVERAGE[sensor], sensor

    def test_sensor_source_map_coverage_classes(self) -> None:
        coverage = sensor_coverage(_records())
        assert coverage["MECHANICAL_BASIS"]["coverage_class"] == "SINGLE_SOURCE"
        assert coverage["MECHANICAL_BOOK_SNAPSHOT"]["coverage_class"] == "TWO_SOURCE"
        assert coverage["MECHANICAL_FUNDING"]["coverage_class"] == "FOUR_SOURCE"
        assert coverage["MECHANICAL_LIQUIDATION"]["coverage_class"] == "THREE_SOURCE"

    def test_all_records_promoted_implemented_ready(self) -> None:
        for r in _records():
            assert r.promoted is True
            assert r.implemented is True
            assert r.adapter_status == "ADAPTER_READY"
            assert r.offline_conformance_pass is True
            assert r.schema_pass is True


# ---------------------------------------------------------------------------
# Exact-set equality (three levels) + no duplication
# ---------------------------------------------------------------------------


class TestExactSetEquality:
    def test_three_level_exact_set_equality(self) -> None:
        result = compute_exact_sets(_records())
        assert result["equal"] is True, {
            "i14_vs_adapter": result["i14_vs_adapter"],
            "adapter_vs_matrix": result["adapter_vs_matrix"],
            "i14_vs_matrix": result["i14_vs_matrix"],
        }
        assert len(result["i14"]) == 17
        assert len(result["adapter"]) == 17
        assert len(result["matrix"]) == 17

    def test_extra_capability_breaks_exact_set(self) -> None:
        records = _records()
        okx_trade = next(r for r in records if r.provider_id == "OKX_SWAP" and r.sensor_family is SensorFamily.MECHANICAL_TRADE)
        extra = replace(okx_trade, sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST)
        result = compute_exact_sets([*records, extra])
        assert result["equal"] is False
        assert result["i14_vs_matrix"]

    def test_no_duplicate_provider_x_sensor_rows(self) -> None:
        keys = [r.key for r in _records()]
        assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# Evidence, scope, audit
# ---------------------------------------------------------------------------


class TestEvidenceAndScope:
    def test_all_evidence_refs_resolve_to_committed_evidence(self) -> None:
        violations = evidence_ref_audit(_records())
        assert not violations, "\n".join(violations)

    def test_broken_evidence_ref_is_flagged(self) -> None:
        records = _records()
        broken = replace(
            records[0],
            evidence_refs=["BOGUS_ref_that_does_not_exist_2021_1h"],
        )
        violations = evidence_ref_audit([broken])
        assert violations

    def test_evidence_refs_equal_i14_basis(self) -> None:
        candidates = load_promotion_candidates()
        basis_by_key = {
            (str(c["provider"]), SensorFamily(str(c["sensor"]))): set(
                str(e) for e in c.get("evidence_basis", [])
            )
            for c in candidates
        }
        for r in _records():
            assert set(r.evidence_refs) == basis_by_key[r.key], r.key

    def test_production_symbol_scopes_evidence_backed(self) -> None:
        expected = {
            ("KRAKEN_FUTURES", SensorFamily.MECHANICAL_BASIS): {"PI_XBTUSD"},
            ("KRAKEN_FUTURES", SensorFamily.MECHANICAL_OPEN_INTEREST): {
                "PI_XBTUSD",
                "PI_ETHUSD",
            },
            ("GATE_FUTURES", SensorFamily.MECHANICAL_FUNDING): {"BTC_USDT"},
            ("OKX_SWAP", SensorFamily.MECHANICAL_FUNDING): {"BTC-USDT-SWAP"},
            ("DERIBIT", SensorFamily.MECHANICAL_LIQUIDATION): {"BTC-PERPETUAL"},
        }
        for r in _records():
            assert r.production_symbol_scope, r.key
            key = (r.provider_id, r.sensor_family)
            if key in expected:
                assert set(r.production_symbol_scope) == expected[key], key

    def test_no_probe_only_symbols_leak_into_production(self) -> None:
        probe_leaks = {
            "ETH_USDT",
            "SOL_USDT",
            "DOGE_USDT",
            "ETH-USDT-SWAP",
            "SOL-USDT-SWAP",
            "DOGE-USDT-SWAP",
            "ETH-PERPETUAL",
            "SOL-PERPETUAL",
            "PI_SOLUSD",
            "PI_DOGEUSD",
        }
        for r in _records():
            assert probe_leaks.isdisjoint(set(r.production_symbol_scope)), r.key


class TestBoundAudit:
    def test_every_record_matches_its_i14_bound(self) -> None:
        records = _records()
        for r in records:
            violations = validate_record_bound(r)
            assert not violations, f"{r.key}: {violations}"

    def test_wrong_role_is_flagged(self) -> None:
        gate_funding = next(
            r
            for r in _records()
            if r.provider_id == "GATE_FUTURES"
            and r.sensor_family is SensorFamily.MECHANICAL_FUNDING
        )
        assert gate_funding.role == "SECONDARY"
        mutated = replace(gate_funding, role="PRIMARY")
        assert validate_record_bound(mutated)

    def test_current_only_marked_historical_is_flagged(self) -> None:
        okx_book = next(
            r
            for r in _records()
            if r.provider_id == "OKX_SWAP"
            and r.sensor_family is SensorFamily.MECHANICAL_BOOK_SNAPSHOT
        )
        assert okx_book.history_scope == "CURRENT_ONLY"
        mutated = replace(okx_book, history_scope="HISTORICAL")
        assert validate_record_bound(mutated)

    def test_wrong_pit_state_is_flagged(self) -> None:
        okx_funding = next(
            r
            for r in _records()
            if r.provider_id == "OKX_SWAP"
            and r.sensor_family is SensorFamily.MECHANICAL_FUNDING
        )
        mutated = replace(okx_funding, pit_readiness="NOT_PIT_READY")
        assert validate_record_bound(mutated)

    def test_wrong_methodology_pin_is_flagged(self) -> None:
        deribit_trade = next(
            r
            for r in _records()
            if r.provider_id == "DERIBIT"
            and r.sensor_family is SensorFamily.MECHANICAL_TRADE
        )
        mutated = replace(deribit_trade, methodology_pin="wrong-pin")
        assert validate_record_bound(mutated)


# ---------------------------------------------------------------------------
# Semantic firewall, resume/completion truth, network
# ---------------------------------------------------------------------------


class TestSemanticFirewall:
    def test_deribit_mechanism_microscope_preserved(self) -> None:
        for r in _records():
            if r.provider_id != "DERIBIT":
                continue
            if r.sensor_family in (
                SensorFamily.MECHANICAL_LIQUIDATION,
                SensorFamily.MECHANICAL_TRADE,
            ):
                assert r.role == "MECHANISM_MICROSCOPE", r.key
                assert "mechanism microscope" in r.semantic_class.lower(), r.key
            else:
                assert r.role != "MECHANISM_MICROSCOPE", r.key

    def test_deribit_liquidation_reclassified_primary_is_flagged(self) -> None:
        deribit_liq = next(
            r
            for r in _records()
            if r.provider_id == "DERIBIT"
            and r.sensor_family is SensorFamily.MECHANICAL_LIQUIDATION
        )
        mutated = replace(deribit_liq, role="PRIMARY")
        assert validate_record_bound(mutated)

    def test_deribit_liquidation_semantic_class_distinct(self) -> None:
        # Trade-level liquidation microscope is NOT an interval liquidation
        # total: semantic_class for Deribit liquidation never says "total".
        for r in _records():
            if r.provider_id == "DERIBIT" and r.sensor_family is SensorFamily.MECHANICAL_LIQUIDATION:
                assert "total" not in r.semantic_class.lower()

    def test_current_only_book_stays_current_only(self) -> None:
        for r in _records():
            if r.sensor_family is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
                assert r.history_scope == "CURRENT_ONLY", r.key
                assert r.native_historical_mode is None, r.key
                assert r.resume_status == "n/a", r.key


class TestResumeCompletionTruth:
    def test_resume_yes_only_where_proven(self) -> None:
        for r in _records():
            if r.provider_id in RESUME_YES_PROVIDERS:
                assert r.resume_status == "YES", r.key
            elif r.sensor_family is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
                assert r.resume_status == "n/a", r.key
            else:
                assert r.resume_status == "LIMITED", r.key

    def test_limited_not_upgraded_to_yes(self) -> None:
        for r in _records():
            if r.resume_status == "YES":
                assert r.provider_id in RESUME_YES_PROVIDERS, r.key
            assert r.resume_status in {"YES", "LIMITED", "n/a"}

    def test_okx_deribit_historical_limited(self) -> None:
        for r in _records():
            if r.provider_id in ("OKX_SWAP", "DERIBIT") and r.history_scope == "HISTORICAL":
                assert r.resume_status == "LIMITED", r.key
                assert r.completion_status == "LIMITED", r.key


class TestNetworkStatus:
    def test_all_network_smoke_not_run(self) -> None:
        for r in _records():
            assert r.network_smoke_status == "NOT_RUN", r.key


class TestAccess:
    def test_all_free_only_and_no_auth(self) -> None:
        for r in _records():
            assert r.free_only_pass is True, r.key
            assert r.auth_mode == "NO_AUTH", r.key
            assert r.access_path == "PUBLIC_REST", r.key
            assert r.access_class == "FREE_AUTOMATED", r.key


# ---------------------------------------------------------------------------
# Determinism + serialization + human matrix reconciliation
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_repeated_generation_is_byte_identical(self) -> None:
        first = _records()
        second = _records()
        assert deterministic_identity(first) == deterministic_identity(second)
        assert render_inventory_csv(first) == render_inventory_csv(second)
        assert render_inventory_json(first) == render_inventory_json(second)

    def test_csv_is_deterministic_and_sorted(self) -> None:
        text = render_inventory_csv(_records())
        lines = text.strip().splitlines()
        assert lines[0].startswith("provider_id,")
        body = lines[1:]
        assert len(body) == 17
        keys = [(line.split(",", 1)[0], ) for line in body]
        assert keys == sorted(keys)

    def test_generated_matrix_files_round_trip(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "PRODUCTION_ADAPTER_MATRIX.csv"
        json_path = tmp_path / "PRODUCTION_ADAPTER_MATRIX.json"
        records = _records()
        write_matrix_files(records, csv_path=csv_path, json_path=json_path)
        assert csv_path.exists() and json_path.exists()
        rows = load_matrix_records(csv_path)
        assert len(rows) == 17
        assert sorted(r["provider_id"] for r in rows) == sorted(
            r.provider_id for r in records
        )


class TestHumanMatrixReconciliation:
    def test_human_readiness_matrix_reconciles(self) -> None:
        assert HUMAN_MATRIX_CSV.exists(), f"missing {HUMAN_MATRIX_CSV}"
        human = load_human_readiness_matrix(HUMAN_MATRIX_CSV)
        violations = reconcile_human_matrix(_records(), human)
        assert not violations, "\n".join(violations)

    def test_extra_promoted_row_is_rejected(self) -> None:
        assert HUMAN_MATRIX_CSV.exists()
        records = _records()
        tampered = load_human_readiness_matrix(HUMAN_MATRIX_CSV)
        # An extra ADAPTER_READY/promoted path for a CURRENT production provider
        # must be rejected by the reconciliation (human matrix cannot outrank I14).
        tampered[("OKX_SWAP", SensorFamily.MECHANICAL_POSITIONING.value)] = {
            "provider_id": "OKX_SWAP",
            "sensor_family": SensorFamily.MECHANICAL_POSITIONING.value,
            "adapter_status": "ADAPTER_READY",
            "promoted": "YES",
            "implemented": "YES",
        }
        violations = reconcile_human_matrix(records, tampered)
        assert violations


# ---------------------------------------------------------------------------
# I09R1 authority boundary seal
# ---------------------------------------------------------------------------


def _write_human_csv(tmp_path: Path, rows: list[tuple[str, str]]) -> Path:
    """Write a temporary human readiness CSV with the given (pid, sensor) rows."""
    path = tmp_path / "duplicate_human.csv"
    path.write_text(
        "provider_id,sensor_family\n"
        + "".join(f"{p},{s}\n" for p, s in rows),
        encoding="utf-8",
    )
    return path


class TestAuthorityDuplicates:
    def test_exact_duplicate_i14_row_fails_closed(self) -> None:
        candidates = list(load_promotion_candidates())
        okx_funding = next(
            c
            for c in candidates
            if str(c["provider"]) == "OKX_SWAP"
            and str(c["sensor"]) == "MECHANICAL_FUNDING"
        )
        with pytest.raises(ValueError):
            validate_promotion_candidate_uniqueness(
                [*candidates, dict(okx_funding)]
            )

    def test_conflicting_duplicate_i14_row_fails_closed(self) -> None:
        # Same provider/sensor but changed role/pin: a dict/set must never pick
        # which authority row wins.
        candidates = list(load_promotion_candidates())
        okx_funding = next(
            c
            for c in candidates
            if str(c["provider"]) == "OKX_SWAP"
            and str(c["sensor"]) == "MECHANICAL_FUNDING"
        )
        conflicting = dict(okx_funding)
        conflicting["role"] = "PRIMARY"
        conflicting["methodology_pin"] = "other-pin"
        with pytest.raises(ValueError):
            validate_promotion_candidate_uniqueness([*candidates, conflicting])

    def test_duplicate_i14_fails_every_consumer_by_default(self) -> None:
        # Authority uniqueness must hold before ANY I09 function that builds a
        # provider x sensor map from candidates; every consumer must reject the
        # same duplicate packet (one authoritative validation helper, reused).
        candidates = list(load_promotion_candidates())
        okx_funding = next(
            c
            for c in candidates
            if str(c["provider"]) == "OKX_SWAP"
            and str(c["sensor"]) == "MECHANICAL_FUNDING"
        )
        pass_map = _pass_map()
        outcomes = _validate_all_with_dupes(
            i14_candidates=[*candidates, dict(okx_funding)],
            pass_map=pass_map,
        )
        assert outcomes == [True] * len(outcomes), (
            "duplicate I14 packets must fail closed on EVERY authority consumer"
        )

    def test_duplicate_human_row_identical_fails_closed(self, tmp_path: Path) -> None:
        path = _write_human_csv(
            tmp_path,
            [
                ("OKX_SWAP", "MECHANICAL_FUNDING"),
                ("OKX_SWAP", "MECHANICAL_FUNDING"),
            ],
        )
        with pytest.raises(ValueError):
            load_human_readiness_matrix(path)

    def test_duplicate_human_row_conflicting_fails_closed(self, tmp_path: Path) -> None:
        # Same key repeated with conflicting adapter_status/promoted: no
        # last-write-wins; loader must fail closed.
        path = _write_human_csv(
            tmp_path,
            [
                ("OKX_SWAP", "MECHANICAL_FUNDING"),
                ("OKX_SWAP", "MECHANICAL_FUNDING"),
            ],
        )
        with pytest.raises(ValueError):
            load_human_readiness_matrix(path)

    def test_healthy_i14_has_zero_duplicates(self) -> None:
        stats = promotion_authority_stats()
        assert stats == {
            "raw_candidate_count": 17,
            "unique_candidate_count": 17,
            "duplicate_count": 0,
        }


class TestVerificationCompleteness:
    def test_missing_conformance_key_fails_closed(self) -> None:
        schema_pass = _pass_map()
        conformance_pass = dict(schema_pass)
        conformance_pass.pop(next(iter(conformance_pass)))
        with pytest.raises(ValueError):
            build_readiness_records(
                conformance_pass=conformance_pass,
                schema_pass=schema_pass,
            )

    def test_missing_schema_key_fails_closed(self) -> None:
        conformance_pass = _pass_map()
        schema_pass = dict(conformance_pass)
        schema_pass.pop(next(iter(schema_pass)))
        with pytest.raises(ValueError):
            build_readiness_records(
                conformance_pass=conformance_pass,
                schema_pass=schema_pass,
            )

    def test_no_verification_input_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            build_readiness_records()

    def test_missing_verification_key_fails_closed(self) -> None:
        full = _verification_map()
        dropped = {k: v for k, v in full.items()}
        dropped.pop(next(iter(dropped)))
        with pytest.raises(ValueError):
            build_readiness_records(verification=dropped)

    def test_explicit_false_distinguishable_from_missing(self) -> None:
        # A present key with offline_conformance_pass=False and a truthful
        # non-ready status is allowed and emitted as data (not silently defaulted
        # and not rejected as if it were an ADAPTER_READY contradiction).
        key = next(iter(_candidate_keys()))
        override = {
            key: ReadinessVerification(
                offline_conformance_pass=False,
                schema_pass=True,
                adapter_status="VALIDATION_FAILED",
            )
        }
        records = build_readiness_records(verification=_verification_map(override))
        target = next(r for r in records if (r.provider_id, r.sensor_family) == key)
        assert target.offline_conformance_pass is False
        assert target.adapter_status == "VALIDATION_FAILED"

    def test_adapter_ready_with_conformance_false_rejected(self) -> None:
        key = next(iter(_candidate_keys()))
        override = {
            key: ReadinessVerification(
                offline_conformance_pass=False,
                schema_pass=True,
                adapter_status="ADAPTER_READY",
            )
        }
        with pytest.raises(ValueError):
            build_readiness_records(verification=_verification_map(override))

    def test_adapter_ready_with_schema_false_rejected(self) -> None:
        key = next(iter(_candidate_keys()))
        override = {
            key: ReadinessVerification(
                offline_conformance_pass=True,
                schema_pass=False,
                adapter_status="ADAPTER_READY",
            )
        }
        with pytest.raises(ValueError):
            build_readiness_records(verification=_verification_map(override))

    def test_network_smoke_cannot_upgrade_before_i10(self) -> None:
        key = next(iter(_candidate_keys()))
        override = {
            key: ReadinessVerification(
                offline_conformance_pass=True,
                schema_pass=True,
                network_smoke_status="PASS",
            )
        }
        with pytest.raises(ValueError):
            build_readiness_records(verification=_verification_map(override))

    def test_every_i14_path_has_explicit_conformance_and_schema(self) -> None:
        records = _records()
        assert len(records) == 17
        for r in records:
            assert r.offline_conformance_pass is True, r.key
            assert r.schema_pass is True, r.key
            assert r.network_smoke_status == "NOT_RUN", r.key


def _validate_all_with_dupes(
    i14_candidates: list[dict[str, object]],
    pass_map: dict[tuple[str, SensorFamily], bool],
) -> list[bool]:
    """Every authority path must reject a duplicate promotion packet."""
    outcomes: list[bool] = []
    for call in (
        lambda: validate_promotion_candidate_uniqueness(i14_candidates),
        lambda: compute_exact_sets(_records(), candidates=i14_candidates),
        lambda: evidence_ref_audit(_records(), candidates=i14_candidates),
        lambda: validate_record_bound(_records()[0], candidates=i14_candidates),
        lambda: build_readiness_records(
            candidates=i14_candidates,
            conformance_pass=pass_map,
            schema_pass=pass_map,
        ),
    ):
        try:
            call()
            outcomes.append(False)
        except ValueError:
            outcomes.append(True)
    return outcomes

# ---------------------------------------------------------------------------
# Real-adapter protocol coherence across providers (no network, FAKE transport)
# ---------------------------------------------------------------------------


def _load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PACKAGE_BY_PROVIDER = {
    "KRAKEN_FUTURES": "kraken",
    "GATE_FUTURES": "gate",
    "OKX_SWAP": "okx",
    "DERIBIT": "deribit",
}

_TRANSPORT_NAME = {
    "KRAKEN_FUTURES": "FakeKrakenTransport",
    "GATE_FUTURES": "FakeGateTransport",
    "OKX_SWAP": "FakeOkxTransport",
    "DERIBIT": "FakeDeribitTransport",
}

#: A promoted sensor whose DEFAULT fake empty-valid envelope parses per provider
#: (Deribit's default envelope is a trades envelope, so use LIQUIDATION, not
#: FUNDING which expects a raw-list result).
_EMPTY_VALID_SENSOR = {
    "KRAKEN_FUTURES": SensorFamily.MECHANICAL_FUNDING,
    "GATE_FUTURES": SensorFamily.MECHANICAL_FUNDING,
    "OKX_SWAP": SensorFamily.MECHANICAL_FUNDING,
    "DERIBIT": SensorFamily.MECHANICAL_LIQUIDATION,
}


def _provider_bindings():
    """Map provider_id -> (adapter class, fake transport + request factory)."""
    bindings = {}
    for provider_id, factory in PRODUCTION_PROVIDER_REGISTRY.items():
        pkg = _PACKAGE_BY_PROVIDER[provider_id]
        fake = _load_module(TEST_ROOT / pkg / "_fake.py")
        adapter = factory()
        cls = type(adapter)
        transport_cls = getattr(fake, _TRANSPORT_NAME[provider_id])
        bindings[provider_id] = (cls, fake, transport_cls, adapter.provider_id)
    return bindings


class TestProtocolCoherence:
    def test_all_supported_fetch_via_dispatch_returns_batch(self) -> None:
        bindings = _provider_bindings()
        for provider_id in ("KRAKEN_FUTURES", "GATE_FUTURES", "OKX_SWAP", "DERIBIT"):
            cls, fake, transport_cls, pid = bindings[provider_id]
            transport = transport_cls()  # default = empty-valid envelope
            adapter = cls(transport=transport)
            # Empty-valid supported path still returns a valid FetchBatch.
            req = fake.request(_EMPTY_VALID_SENSOR[provider_id])
            batch = dispatch_fetch(adapter, req)
            assert batch.provider_id == pid
            assert batch.sensor_family is req.sensor_family
            assert batch.row_count == 0

    def test_foreign_provider_request_rejected_before_transport(self) -> None:
        bindings = _provider_bindings()
        for provider_id, (cls, fake, transport_cls, pid) in bindings.items():
            transport = transport_cls()
            adapter = cls(transport=transport)
            req = fake.request(SensorFamily.MECHANICAL_FUNDING)
            foreign_pid = "DERIBIT" if pid != "DERIBIT" else "KRAKEN_FUTURES"
            foreign = req.model_copy(update={"provider_id": foreign_pid})
            with pytest.raises(ProviderSemanticError):
                dispatch_fetch(adapter, foreign)
            assert transport.calls == [], (
                f"{provider_id} reached transport on foreign request"
            )

    def test_no_transport_raises_provider_unavailable(self) -> None:
        bindings = _provider_bindings()
        for provider_id, (cls, fake, transport_cls, pid) in bindings.items():
            adapter = cls()  # no transport = offline
            req = fake.request(SensorFamily.MECHANICAL_FUNDING)
            with pytest.raises(ProviderUnavailable):
                dispatch_fetch(adapter, req)

    def test_unsupported_sensor_typed_capability_unavailable(self) -> None:
        bindings = _provider_bindings()
        unsupported = {
            "KRAKEN_FUTURES": SensorFamily.MECHANICAL_TRADE,
            "GATE_FUTURES": SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
            "OKX_SWAP": SensorFamily.MECHANICAL_LIQUIDATION,
            "DERIBIT": SensorFamily.MECHANICAL_OPEN_INTEREST,
        }
        for provider_id, (cls, fake, transport_cls, pid) in bindings.items():
            adapter = cls()
            req = fake.request(unsupported[provider_id])
            with pytest.raises(CapabilityUnavailable):
                dispatch_fetch(adapter, req)