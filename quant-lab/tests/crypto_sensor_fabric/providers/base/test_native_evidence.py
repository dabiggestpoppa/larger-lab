"""SENSOR-B3-I05 — provider-native acquisition-mode evidence seam (base layer).

The common framework lets a PRODUCTION adapter set an exact `historical_mode` /
`pagination_mode` ONLY when a valid `ProviderNativeCapabilityEvidence` grant
resolves to committed Bloc 2 (I14) evidence.  Missing refinement evidence => the
exact field stays UNKNOWN or conformance FAILS CLOSED — never inferred.

Adversarial rules tested at unit level here:

- native evidence id pointing outside the I14 evidence_basis        -> FAIL
- native evidence on the WRONG provider                             -> FAIL
- native evidence on the WRONG sensor                               -> FAIL
- native evidence broadening a CURRENT_ONLY scope                   -> FAIL
- native evidence switching a non-archive bound to archive          -> FAIL
- missing / non-resolving grant on `apply_native_evidence`          -> raises
- valid Kraken evidence-backed native mode                          -> PASS

Conformance-level enforcement (q0_native_mode_evidence: exact native mode without
a grant FAILS) is exercised through the real Kraken adapter in the Kraken test
suite.  All fixtures are valid typed models (enum members), never raw strings.
"""

from __future__ import annotations

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base import (
    apply_native_evidence,
    capabilities_from_promotion,
    load_promotion_candidates,
    native_evidence_violations,
)
from crypto_sensor_fabric.providers.base.enums import (
    HistoryScope,
    HistoricalMode,
    PaginationMode,
)
from crypto_sensor_fabric.providers.base.native import ProviderNativeCapabilityEvidence

FUNDING_EVIDENCE = "kraken_futures_funding_pi_xbtusd_RECENT_CONTROL_1h"


def _cands(provider: str) -> list[dict]:
    return [c for c in load_promotion_candidates() if c.get("provider") == provider]


def _fund_bound():
    caps = capabilities_from_promotion("KRAKEN_FUTURES", _cands("KRAKEN_FUTURES"))
    return caps.capability_for(SensorFamily.MECHANICAL_FUNDING)


def _grant(**overrides) -> ProviderNativeCapabilityEvidence:
    base = dict(
        provider_id="KRAKEN_FUTURES",
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        historical_mode=HistoricalMode.REST_RANGE,
        pagination_mode=PaginationMode.TIME_RANGE,
        endpoint_family="kraken-market-analytics/funding",
        start_param="since",
        start_unit="epoch_seconds",
        end_param="to",
        end_unit="epoch_seconds",
        interval_param="interval",
        interval_mechanics="seconds; supported {60,...}",
        completion_rule="result.more == false -> complete",
        resume_mechanic="result.more true -> re-issue since at oldest bucket",
        evidence_ids=(FUNDING_EVIDENCE,),
        methodology_pin="kraken_futures-funding",
        access_path="PUBLIC_REST",
        verification_head=None,
    )
    base.update(overrides)
    return ProviderNativeCapabilityEvidence(**base)


class TestNativeEvidenceUnit:
    def test_valid_grant_has_no_violations(self) -> None:
        assert native_evidence_violations("KRAKEN_FUTURES", _grant(), _fund_bound()) == []

    def test_wrong_provider_fails(self) -> None:
        vio = native_evidence_violations(
            "KRAKEN_FUTURES", _grant(provider_id="GATE_FUTURES"), _fund_bound()
        )
        assert any("provider" in v for v in vio)

    def test_wrong_sensor_fails(self) -> None:
        g = _grant(sensor_family=SensorFamily.MECHANICAL_BASIS)
        vio = native_evidence_violations("KRAKEN_FUTURES", g, _fund_bound())
        assert any("sensor" in v for v in vio)

    def test_evidence_id_not_resolving_fails(self) -> None:
        g = _grant(evidence_ids=("unrelated-evidence-id",))
        vio = native_evidence_violations("KRAKEN_FUTURES", g, _fund_bound())
        assert any("not in the I14 evidence_basis" in v for v in vio)

    def test_methodology_change_fails(self) -> None:
        g = _grant(methodology_pin="another-methodology")
        vio = native_evidence_violations("KRAKEN_FUTURES", g, _fund_bound())
        assert any("methodology" in v for v in vio)

    def test_archive_switch_on_non_archive_bound_fails(self) -> None:
        g = _grant(historical_mode=HistoricalMode.BULK_ARCHIVE_MONTHLY)
        vio = native_evidence_violations("KRAKEN_FUTURES", g, _fund_bound())
        assert any("archive" in v for v in vio)

    def test_access_path_change_fails(self) -> None:
        g = _grant(access_path="PUBLIC_ARCHIVE")
        vio = native_evidence_violations("KRAKEN_FUTURES", g, _fund_bound())
        assert any("access_path" in v for v in vio)

    def test_current_only_scope_cannot_get_native_history(self) -> None:
        okx = capabilities_from_promotion("OKX_SWAP", _cands("OKX_SWAP"))
        book = okx.capability_for(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
        assert book.history_scope is HistoryScope.CURRENT_ONLY
        g = ProviderNativeCapabilityEvidence(
            provider_id="OKX_SWAP",
            sensor_family=SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
            historical_mode=HistoricalMode.REST_RANGE,
            pagination_mode=PaginationMode.TIME_RANGE,
            endpoint_family="okx-books",
            start_param="",
            start_unit="",
            end_param="",
            end_unit="",
            evidence_ids=(
                "okx_swap_book_snapshot_btc-usdt-swap_RECENT_CONTROL_book_snapshot",
            ),
            methodology_pin="okx_swap-book_snapshot",
            access_path="PUBLIC_REST",
        )
        vio = native_evidence_violations("OKX_SWAP", g, book)
        assert any("CURRENT_ONLY" in v for v in vio)


class TestApplyNativeEvidence:
    def test_valid_refines_mode_and_preserves_bounds(self) -> None:
        bound = _fund_bound()
        refined = apply_native_evidence(bound, _grant(), provider_id="KRAKEN_FUTURES")
        assert refined.historical_mode is HistoricalMode.REST_RANGE
        assert refined.pagination_mode is PaginationMode.TIME_RANGE
        assert refined.history_scope is HistoryScope.HISTORICAL
        assert refined.methodology_pin == "kraken_futures-funding"
        assert refined.allowed_role == bound.allowed_role
        assert refined.verified_history_start == bound.verified_history_start
        assert refined.live_mode == bound.live_mode
        assert refined.archive_mode == bound.archive_mode

    def test_wrong_provider_raises(self) -> None:
        with pytest.raises(ValueError):
            apply_native_evidence(
                _fund_bound(),
                _grant(provider_id="GATE_FUTURES"),
                provider_id="KRAKEN_FUTURES",
            )

    def test_archive_switch_raises(self) -> None:
        with pytest.raises(ValueError):
            apply_native_evidence(
                _fund_bound(),
                _grant(historical_mode=HistoricalMode.BULK_ARCHIVE_MONTHLY),
                provider_id="KRAKEN_FUTURES",
            )

    def test_unresolving_evidence_raises(self) -> None:
        with pytest.raises(ValueError):
            apply_native_evidence(
                _fund_bound(),
                _grant(evidence_ids=("not-a-real-id",)),
                provider_id="KRAKEN_FUTURES",
            )

    def test_current_only_apply_raises(self) -> None:
        okx = capabilities_from_promotion("OKX_SWAP", _cands("OKX_SWAP"))
        book = okx.capability_for(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
        with pytest.raises(ValueError):
            apply_native_evidence(
                book,
                ProviderNativeCapabilityEvidence(
                    provider_id="OKX_SWAP",
                    sensor_family=SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
                    historical_mode=HistoricalMode.REST_RANGE,
                    pagination_mode=PaginationMode.TIME_RANGE,
                    endpoint_family="okx-books",
                    start_param="",
                    start_unit="",
                    end_param="",
                    end_unit="",
                    evidence_ids=(
                        "okx_swap_book_snapshot_btc-usdt-swap_RECENT_CONTROL_book_snapshot",
                    ),
                    methodology_pin="okx_swap-book_snapshot",
                    access_path="PUBLIC_REST",
                ),
                provider_id="OKX_SWAP",
            )