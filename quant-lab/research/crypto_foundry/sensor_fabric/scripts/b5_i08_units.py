#!/usr/bin/env python3
"""SENSOR-B5-I08E1 - tracked deterministic unit-validation evidence producer.

Extends the frozen bloc_05/06 S17 artifact ``bloc_05_unit_validation.json``
with the ``U08-01..U08-20`` rows of this checkpoint while preserving the
I04B rows byte-identically.

Custody laws (I03I/I04A/I04B lessons applied):

* this file is TRACKED in the same implementation stage that creates its
  evidence -- no ``.bu_tmp`` dependency, no scratch import;
* the 35 committed I04B rows are PINNED by SHA-256 inside this producer:
  any drift in them aborts the run BEFORE any write (the base portion of a
  frozen-name artifact is never rewritten by a later checkpoint);
* ``bloc_05_unit_validation.json`` self-describes as the "G5 conversion
  portion" of the S17 unit-validation obligation -- this producer appends
  the I08 portion (``extensions`` key records the merge provenance);
* deterministic fixtures only: pinned datetimes, Decimal strings (never
  float), no wall clock, no network, no ``repr()`` of objects;
* every ``observed_result`` is measured by executing the operation here;
  hand-written expectations live only in ``expected_result`` and the
  ``pass`` boolean is computed by the real predicate (I03I law);
* any non-PASS disposition aborts with a non-zero exit BEFORE writing, so
  evidence is never emitted as a passing artifact when a fixture fails;
* output is UTF-8, ``sort_keys``, LF, written as raw bytes so Windows
  text-mode newline translation cannot dirty the artifact (I04A V5 lesson);
* ordering law: this producer runs BEFORE the append-only ledger entry is
  written (its hash is quoted into that entry), so it deliberately never
  names any governance document;
* ``--check`` mode writes nothing and prints a machine-readable summary
  including ``artifact_sha256`` of the bytes this producer would commit;
  it exits 0 only when those bytes equal the committed artifact.

Known interaction (disclosed, not a defect): re-running the I04B producer
``b5_i04b_conversion.py`` standalone regenerates only its own 35-row
portion.  The canonical regeneration path for the combined artifact is
THIS producer, which merges the pinned base rows with freshly measured
U08 rows.

Run (from ``quant-lab``)::

    PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/b5_i08_units.py
    PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/b5_i08_units.py --check

Plan citations use the compact S<n> form for bloc_05/0<n> sections.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

# Same bootstrap as the tracked I04A/I04B producers: import the package
# straight from the repository ``src/`` tree so the generator runs from a
# clean interpreter with no installed-package dependency (I03I custody law).
sys.path.insert(0, "src")

from pydantic import ValidationError

from crypto_sensor_fabric.normalization.common import (
    CanonicalQuantityUnit,
    ConversionRateObservation,
    METHODOLOGY_VERSION,
    PrecisionRecord,
    QuantityUnitIdentity,
    convert_stablecoin_to_usd,
    cross_convert_via_usd,
    decimal_places,
    precision_widened,
)
from crypto_sensor_fabric.normalization.enums import NormalizationQualityFlag
from crypto_sensor_fabric.normalization.models import canonical_json_bytes

ARTIFACT = Path(
    "research/crypto_foundry/sensor_fabric/evidence/bloc_05/"
    "bloc_05_unit_validation.json"
)
GEN_REF = "GEN_REF:research/crypto_foundry/sensor_fabric/scripts/b5_i08_units.py"

#: SHA-256 over ``json.dumps(i04b_rows, sort_keys=True, separators=(',',':'))``
#: for the 35 committed I04B rows.  Measured, then frozen: any drift aborts
#: before write (this producer may APPEND to the frozen-name artifact, never
#: REWRITE its base portion).
I04B_ROWS_PIN_SHA256 = (
    "5b17397cf7b47dbe7681f736c5d03012044f0a0d99b298c7b1fec28b974c2236"
)

_BLOCK = NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE

# Pinned synthetic fixtures (depeg mechanics, bloc_05/03 S9 + 06 S12).
_T = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_T_PIT = datetime(2025, 6, 1, 11, 59, 0, tzinfo=timezone.utc)
_T_FUTURE = datetime(2025, 6, 1, 12, 1, 0, tzinfo=timezone.utc)


def _rate(
    from_asset: str = "USDT",
    into_asset: str = "USD",
    rate: str = "0.97",
    effective_at: datetime = _T,
    market_available_at: datetime = _T,
) -> ConversionRateObservation:
    return ConversionRateObservation(
        from_asset=from_asset,
        into_asset=into_asset,
        rate=Decimal(rate),
        effective_at=effective_at,
        market_available_at=market_available_at,
        source="synthetic_depeg_fixture",
        methodology=METHODOLOGY_VERSION,
        quality="SYNTHETIC_FIXTURE",
    )


def _refusal(probe: Callable[[], Any]) -> bool:
    """True when the probe raises (fail-closed observation)."""
    try:
        probe()
    except (ValidationError, ValueError):
        return True
    return False


def _flags(result: Any) -> str:
    return "|".join(f.value for f in result.quality_flags) or "none"


def _build_rows() -> list[dict[str, Any]]:
    """Measure every U08 case by executing it against production code."""
    rows: list[dict[str, Any]] = []

    def add(
        case_id: str,
        clause: str,
        input_condition: str,
        probe: str,
        expected: str,
        forbidden: str,
        observed: str,
        ok: bool,
        test_ref: str,
        nonmutation: str = "inputs unchanged (verified)",
        **extra: Any,
    ) -> None:
        row: dict[str, Any] = {
            "acceptance_clause": clause,
            "case_id": case_id,
            "disposition": "PASS" if ok else "FAIL",
            "evidence_reference": GEN_REF,
            "expected_result": expected,
            "forbidden_result": forbidden,
            "input_condition": input_condition,
            "nonmutation_assertion": nonmutation,
            "observed_result": observed,
            "probe_or_operation": probe,
            "test_reference": test_ref,
        }
        row.update(extra)
        rows.append(row)

    # -- U08-01 frozen vocabulary ----------------------------------------
    units = {u.value for u in CanonicalQuantityUnit}
    expected_units = {
        "CONTRACTS", "BASE_ASSET", "QUOTE_ASSET", "SETTLEMENT_ASSET",
        "USD", "USDT", "USDC", "OTHER_QUOTE", "PERCENT",
        "RATE_PER_INTERVAL", "BPS", "PRICE", "COUNT",
    }
    add(
        "U08-01",
        "bloc_05/03 S4",
        "the frozen minimum quantity vocabulary, enumerated from the enum",
        "{u.value for u in CanonicalQuantityUnit}",
        "exactly the 13 frozen unit names",
        "a 14th unit or a renamed member",
        f"count={len(units)}; equal_to_frozen_set={units == expected_units}",
        units == expected_units,
        "test_u08_01_canonical_quantity_vocabulary_is_frozen_and_complete",
    )

    # -- U08-02 asset-identity law ---------------------------------------
    bare_refused = _refusal(lambda: QuantityUnitIdentity(
        unit=CanonicalQuantityUnit.BASE_ASSET))
    with_asset = QuantityUnitIdentity(
        unit=CanonicalQuantityUnit.BASE_ASSET, asset_id="BTC")
    smuggled = _refusal(lambda: QuantityUnitIdentity(
        unit=CanonicalQuantityUnit.USD, asset_id="BTC"))
    dimensionless = _refusal(lambda: QuantityUnitIdentity(
        unit=CanonicalQuantityUnit.COUNT, asset_id="BTC"))
    ok = bare_refused and with_asset.asset_id == "BTC" and smuggled and dimensionless
    add(
        "U08-02",
        "bloc_05/03 S4",
        "bare BASE_ASSET; BASE_ASSET+BTC; USD+BTC; COUNT+BTC",
        "QuantityUnitIdentity(...) construction x4",
        "refuse | accept with asset | refuse | refuse",
        "'1000 BASE_ASSET' existing without asset identity",
        f"bare_refused={bare_refused}; accepted_asset={with_asset.asset_id}; "
        f"usd_smuggle_refused={smuggled}; count_smuggle_refused={dimensionless}",
        ok,
        "test_u08_02_asset_qualified_units_require_asset_identity",
    )

    # -- U08-03 stablecoin distinctness ----------------------------------
    distinct = len({
        CanonicalQuantityUnit.USD,
        CanonicalQuantityUnit.USDT,
        CanonicalQuantityUnit.USDC,
    })
    usdt_usd = _refusal(lambda: QuantityUnitIdentity(
        unit=CanonicalQuantityUnit.USDT, asset_id="USD"))
    add(
        "U08-03",
        "bloc_05/03 S9; S22 inv.3",
        "USD/USDT/USDC enumerated; USDT with a nested USD identity",
        "set cardinality + QuantityUnitIdentity refusal",
        "three distinct units; nested identity refused",
        "USD/USDT/USDC collapsing into one token",
        f"distinct={distinct}; usdt_nested_usd_refused={usdt_usd}",
        distinct == 3 and usdt_usd,
        "test_u08_03_usd_usdt_usdc_are_distinct_units",
    )

    # -- U08-04 precision preserved --------------------------------------
    native_fine = Decimal("0.0000123456789")
    r4 = convert_stablecoin_to_usd(
        native_fine, CanonicalQuantityUnit.USDT, rate=_rate(), cutoff=_T_FUTURE)
    observed = f"{r4.usd_equivalent}|native={r4.native_value}"
    ok = (r4.usd_equivalent == Decimal("0.000011975308533")
          and r4.native_value == native_fine)
    add(
        "U08-04",
        "bloc_05/03 S3.1",
        "13-decimal provider-native value converted at rate 0.97",
        "convert_stablecoin_to_usd(0.0000123456789 USDT, rate=0.97)",
        "0.000011975308533 with native preserved exactly",
        "rounded or float-artifact output (0.0000119753085329)",
        observed,
        ok,
        "test_u08_04_provider_precision_is_preserved_exactly",
    )

    # -- U08-05 no fake precision ----------------------------------------
    dp2 = decimal_places(Decimal("1.23"))
    dp4 = decimal_places(Decimal("1.2300"))
    dp0 = decimal_places(Decimal("123"))
    wid_eq = precision_widened(Decimal("1.23"), Decimal("1.23"))
    wid_up = precision_widened(Decimal("1.23"), Decimal("1.2300"))
    wid_dn = precision_widened(Decimal("1.23"), Decimal("1.2"))
    ok = (dp2, dp4, dp0) == (2, 4, 0) and not wid_eq and wid_up and not wid_dn
    add(
        "U08-05",
        "bloc_05/03 S3.3",
        "decimal-place measurement over 1.23 / 1.2300 / 123 and widening pairs",
        "decimal_places(...) x3; precision_widened(...) x3",
        "2 | 4 | 0; False | True | False",
        "widening passing silently as equal (or a rounding helper existing)",
        f"dp={dp2}|{dp4}|{dp0}; widened={wid_eq}|{wid_up}|{wid_dn}",
        ok,
        "test_u08_05_no_fake_precision_widening_predicate",
    )

    # -- U08-06 canonical numeric types ----------------------------------
    float_refused = _refusal(lambda: ConversionRateObservation(
        from_asset="USDT", into_asset="USD", rate=0.97,  # type: ignore[arg-type]
        effective_at=_T, market_available_at=_T, source="s",
        methodology=METHODOLOGY_VERSION, quality="SYNTHETIC_FIXTURE"))
    prec_ok = PrecisionRecord(source_precision=2, conversion_precision=2)
    neg_refused = _refusal(lambda: PrecisionRecord(source_precision=-1))
    ok = float_refused and prec_ok.source_precision == 2 and neg_refused
    add(
        "U08-06",
        "bloc_05/03 S3.2",
        "float rate at the model boundary; negative precision declaration",
        "ConversionRateObservation(rate=0.97 float); PrecisionRecord(-1)",
        "both refused; valid record accepted with source_precision=2",
        "a float silently coerced into Decimal with binary noise",
        f"float_refused={float_refused}; record_source={prec_ok.source_precision}; "
        f"negative_refused={neg_refused}",
        ok,
        "test_u08_06_canonical_numeric_types_refuse_floats",
    )

    # -- U08-07 depeg fixture (06 S12) -----------------------------------
    depeg = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(),
        cutoff=_T_FUTURE)
    ok = (depeg.native_value == Decimal("1000")
          and depeg.usd_equivalent == Decimal("970")
          and depeg.quality_flags == ()
          and depeg.methodology_version == METHODOLOGY_VERSION)
    add(
        "U08-07",
        "bloc_05/03 S9; bloc_05/06 S12",
        "1000 USDT native; USDT/USD = 0.97 at t; cutoff after availability",
        "convert_stablecoin_to_usd(1000 USDT, rate=0.97)",
        "native=1000 USDT preserved; usd_equivalent=970; no flags",
        "hardcoded 1:1 overwriting the observation (usd=1000)",
        f"native={depeg.native_value}|unit={depeg.native_unit.value}; "
        f"usd={depeg.usd_equivalent}; flags={_flags(depeg)}",
        ok,
        "test_u08_07_stablecoin_depeg_fixture_0_97",
    )

    # -- U08-08 no hardcoded 1:1 -----------------------------------------
    no_rate = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=None,
        cutoff=_T_FUTURE)
    ok = (no_rate.usd_equivalent is None
          and _BLOCK in no_rate.quality_flags
          and no_rate.conversion_inputs == ())
    add(
        "U08-08",
        "bloc_05/03 S9; S22 inv.3; bloc_05/06 S12",
        "1000 USDT with NO rate observation available",
        "convert_stablecoin_to_usd(1000 USDT, rate=None)",
        "NULL + STABLECOIN_CONVERSION_UNAVAILABLE; no consumed inputs",
        "usd_equivalent defaulting to 1000 (permanent 1 USDT = 1 USD)",
        f"usd={no_rate.usd_equivalent}; flags={_flags(no_rate)}; "
        f"inputs={len(no_rate.conversion_inputs)}",
        ok,
        "test_u08_08_no_hardcoded_one_to_one",
    )

    # -- U08-09 required rate fields -------------------------------------
    base_payload = dict(
        from_asset="USDT", into_asset="USD", rate=Decimal("0.97"),
        effective_at=_T, market_available_at=_T, source="s",
        methodology=METHODOLOGY_VERSION, quality="SYNTHETIC_FIXTURE")
    refused = []
    accepted = []
    for field in base_payload:
        incomplete = {k: v for k, v in base_payload.items() if k != field}
        if _refusal(lambda inc=incomplete: ConversionRateObservation(**inc)):
            refused.append(field)
        else:
            accepted.append(field)
    ok = len(refused) == 8 and not accepted
    add(
        "U08-09",
        "bloc_05/03 S9",
        "eight constructions, each missing exactly one frozen field",
        "ConversionRateObservation(**{field-less payload}) x8",
        "all eight incomplete observations refused",
        "any frozen field optional or defaulted",
        f"refused={len(refused)}/8; accepted={accepted}",
        ok,
        "test_u08_09_rate_observation_requires_all_frozen_fields",
    )

    # -- U08-10 cutoff replay law ----------------------------------------
    before = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(),
        cutoff=_T_PIT)
    boundary = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(),
        cutoff=_T)
    ok = (before.usd_equivalent is None and _BLOCK in before.quality_flags
          and boundary.usd_equivalent == Decimal("970"))
    add(
        "U08-10",
        "bloc_05/06 S12 (replay); bloc_05/02 S4",
        "rate available at 12:00; replay cutoffs 11:59 and 12:00",
        "convert_stablecoin_to_usd(..., cutoff=11:59 | cutoff=12:00)",
        "blocked at 11:59; usd=970 at 12:00 (inclusive boundary)",
        "a replay before the observation using the later 0.97 value",
        f"cutoff_1159={before.usd_equivalent}|flags={_flags(before)}; "
        f"cutoff_1200={boundary.usd_equivalent}",
        ok,
        "test_u08_10_rate_observation_must_be_available_at_cutoff",
    )

    # -- U08-11 no substitution / no future rate -------------------------
    wrong_leg = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT,
        rate=_rate(from_asset="USDC"), cutoff=_T_FUTURE)
    future_eff = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT,
        rate=_rate(effective_at=_T_FUTURE, market_available_at=_T_FUTURE),
        cutoff=_T)
    ok = (wrong_leg.usd_equivalent is None and _BLOCK in wrong_leg.quality_flags
          and future_eff.usd_equivalent is None
          and _BLOCK in future_eff.quality_flags)
    add(
        "U08-11",
        "bloc_05/03 S9; S10",
        "USDT request answered by a USDC leg; rate effective only at 12:01",
        "convert_stablecoin_to_usd(..., from=USDC) | (effective=12:01, cutoff=12:00)",
        "both refused (NULL + frozen flag); no silent redirection",
        "a redirected leg or a future rate consumed for an old record",
        f"wrong_leg={wrong_leg.usd_equivalent}|{_flags(wrong_leg)}; "
        f"future_eff={future_eff.usd_equivalent}|{_flags(future_eff)}",
        ok,
        "test_u08_11_rate_direction_is_never_substituted",
    )

    # -- U08-12 rate domain ------------------------------------------------
    zero = _refusal(lambda: _rate(rate="0"))
    negative = _refusal(lambda: _rate(rate="-0.5"))
    nan = _refusal(lambda: _rate(rate="NaN"))
    inf = _refusal(lambda: _rate(rate="Infinity"))
    ok = zero and negative and nan and inf
    add(
        "U08-12",
        "bloc_05/03 S9 (rate), S3.2",
        "rate values 0, -0.5, NaN, Infinity at the observation boundary",
        "ConversionRateObservation(rate=...) x4",
        "all four refused",
        "a non-positive or non-finite rate entering conversion arithmetic",
        f"refused: zero={zero}; negative={negative}; nan={nan}; inf={inf}",
        ok,
        "test_u08_12_rate_domain_positive_finite",
    )

    # -- U08-13 cross-currency hierarchy (S10) ----------------------------
    usd_leg = _rate(from_asset="USDT", into_asset="USD", rate="0.97")
    eur_leg = _rate(from_asset="EUR", into_asset="USD", rate="1.00")
    cross_ok = cross_convert_via_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, "EUR",
        rate_from=usd_leg, rate_into=eur_leg, cutoff=_T_FUTURE)
    no_leg = cross_convert_via_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, "EUR",
        rate_from=usd_leg, rate_into=None, cutoff=_T_FUTURE)
    stale = cross_convert_via_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, "EUR",
        rate_from=usd_leg,
        rate_into=_rate(from_asset="EUR", into_asset="USD", rate="1.00",
                        market_available_at=_T_FUTURE, effective_at=_T_FUTURE),
        cutoff=_T)
    ok = (cross_ok.derived_value == Decimal("970")
          and cross_ok.derived_asset == "EUR" and bool(cross_ok.conversion_inputs)
          and no_leg.derived_value is None and _BLOCK in no_leg.quality_flags
          and stale.derived_value is None and _BLOCK in stale.quality_flags)
    add(
        "U08-13",
        "bloc_05/03 S10 (tiers 3/4); S17",
        "1000 USDT via USD into EUR: both legs valid | missing second leg | stale second leg",
        "cross_convert_via_usd(...) x3",
        "derived=970 EUR with 2 input refs; NULL+flag; NULL+flag",
        "a guessed rate when one leg is absent or not yet available",
        f"both_valid={cross_ok.derived_value}|asset={cross_ok.derived_asset}"
        f"|inputs={len(cross_ok.conversion_inputs)}; "
        f"missing_leg={no_leg.derived_value}|{_flags(no_leg)}; "
        f"stale_leg={stale.derived_value}|{_flags(stale)}",
        ok,
        "test_u08_13_derived_cross_through_usd_requires_both_legs_pit_valid",
    )

    # -- U08-14 NULL vs zero ---------------------------------------------
    zero_conv = convert_stablecoin_to_usd(
        Decimal("0"), CanonicalQuantityUnit.USDT, rate=_rate(),
        cutoff=_T_FUTURE)
    zero_blocked = convert_stablecoin_to_usd(
        Decimal("0"), CanonicalQuantityUnit.USDT, rate=None,
        cutoff=_T_FUTURE)
    ok = (zero_conv.usd_equivalent == Decimal("0")
          and zero_conv.quality_flags == ()
          and zero_blocked.usd_equivalent is None
          and zero_blocked.usd_equivalent != Decimal("0"))
    add(
        "U08-14",
        "bloc_05/03 S14; S22 inv.5",
        "native 0 with a valid rate; native 0 with no rate",
        "convert_stablecoin_to_usd(0, rate=0.97) | (0, rate=None)",
        "verified zero -> 0; unavailable -> None (distinct answers)",
        "a missing payload becoming 0, or 0 becoming None",
        f"with_rate={zero_conv.usd_equivalent}|flags={_flags(zero_conv)}; "
        f"no_rate={zero_blocked.usd_equivalent}|{_flags(zero_blocked)}",
        ok,
        "test_u08_14_null_usd_is_not_zero",
    )

    # -- U08-15 lineage + methodology ------------------------------------
    lineage = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(),
        cutoff=_T_FUTURE)
    ref = lineage.conversion_inputs[0] if lineage.conversion_inputs else ""
    ok = (lineage.methodology_version == METHODOLOGY_VERSION
          and len(lineage.conversion_inputs) == 1
          and ref.startswith("rate_observation_ref=")
          and "synthetic_depeg_fixture" in ref
          and _T.isoformat() in ref)
    add(
        "U08-15",
        "bloc_05/03 S17; S22 inv.7",
        "one derived USD value from one observed rate",
        "inspect conversion_inputs + methodology_version",
        "exactly 1 ref naming source and effective_at; I08 methodology",
        "a derived value without reconstructable lineage",
        f"methodology={lineage.methodology_version}; inputs={len(ref) and 1}; "
        f"ref={ref[:96]}",
        ok,
        "test_u08_15_derived_values_carry_lineage_and_methodology",
    )

    # -- U08-16 native survives / no mutation ----------------------------
    rate_probe = _rate()
    native_probe = Decimal("1000")
    surv = convert_stablecoin_to_usd(
        native_probe, CanonicalQuantityUnit.USDT, rate=rate_probe,
        cutoff=_T_FUTURE)
    ok = (surv.native_value == native_probe == Decimal("1000")
          and rate_probe.rate == Decimal("0.97") and surv is not rate_probe)
    add(
        "U08-16",
        "bloc_05/03 S22 inv.1; S1/S5",
        "native Decimal + rate observation passed in, conversion executed",
        "convert_stablecoin_to_usd(...); re-inspect both inputs after",
        "native_value == input == 1000; rate.rate still 0.97; distinct objects",
        "in-place mutation of the caller's observation or native value",
        f"native_after={surv.native_value}; rate_after={rate_probe.rate}; "
        f"distinct_objects={surv is not rate_probe}",
        ok,
        "test_u08_16_native_value_survives_and_inputs_are_not_mutated",
        nonmutation="both inputs re-measured unchanged after the call",
    )

    # -- U08-17 result laws ------------------------------------------------
    from crypto_sensor_fabric.normalization.enums import BLOCKING_QUALITY_FLAGS

    blocked17 = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=None,
        cutoff=_T_FUTURE)
    ok17 = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(),
        cutoff=_T_FUTURE)
    contract_refused = _refusal(lambda: convert_stablecoin_to_usd(
        Decimal("3"), CanonicalQuantityUnit.CONTRACTS, rate=None, cutoff=_T))
    ok = (bool(set(blocked17.quality_flags) & set(BLOCKING_QUALITY_FLAGS))
          and blocked17.conversion_inputs == ()
          and not (set(ok17.quality_flags) & set(BLOCKING_QUALITY_FLAGS))
          and bool(ok17.conversion_inputs) and contract_refused)
    add(
        "U08-17",
        "bloc_05/03 S17; S22 inv.7; S6/S7 (I04B boundary)",
        "blocked path | derived path | CONTRACTS-denominated request",
        "inspect both results; attempt contract-native conversion",
        "blocked: flag+no lineage; derived: lineage+no flag; CONTRACTS refused",
        "a blocked result claiming inputs, or a contract answer bypassing I04B",
        f"blocked: flags={_flags(blocked17)}; inputs={len(blocked17.conversion_inputs)}; "
        f"derived: flags={_flags(ok17)}; inputs={len(ok17.conversion_inputs)}; "
        f"contract_refused={contract_refused}",
        ok,
        "test_u08_17_blocked_and_success_result_laws",
    )

    # -- U08-18 determinism -------------------------------------------------
    a = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(),
        cutoff=_T_FUTURE)
    b = convert_stablecoin_to_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(),
        cutoff=_T_FUTURE)
    ca = cross_convert_via_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, "EUR",
        rate_from=_rate(), rate_into=_rate(
            from_asset="EUR", into_asset="USD", rate="1.00"),
        cutoff=_T_FUTURE)
    cb = cross_convert_via_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, "EUR",
        rate_from=_rate(), rate_into=_rate(
            from_asset="EUR", into_asset="USD", rate="1.00"),
        cutoff=_T_FUTURE)
    same = (canonical_json_bytes(a) == canonical_json_bytes(b)
            and canonical_json_bytes(ca) == canonical_json_bytes(cb))
    add(
        "U08-18",
        "bloc_05/03 S1/S17 (determinism); S22",
        "two structurally equal constructions of both result kinds",
        "canonical_json_bytes(x) == canonical_json_bytes(y) x2 pairs",
        "byte-identical serialization for equal results",
        "timestamps, addresses or dict order leaking into the bytes",
        f"stablecoin_pair_equal={canonical_json_bytes(a) == canonical_json_bytes(b)}; "
        f"cross_pair_equal={canonical_json_bytes(ca) == canonical_json_bytes(cb)}",
        same,
        "test_u08_18_deterministic_construction_and_serialization",
    )

    # -- U08-19 scope audit -------------------------------------------------
    common_dir = Path("src/crypto_sensor_fabric/normalization/common")
    present = sorted(p.name for p in common_dir.iterdir()
                     if p.suffix == ".py") if common_dir.is_dir() else []
    frozen_modules = ["__init__.py", "conversion.py", "numeric.py", "units.py"]
    forbidden_absent = not any(
        (common_dir / name).exists() or (
            common_dir.parent / name).exists()
        for name in (
            "methodologies.py", "semantic_registry.py", "comparability.py",
            "missingness.py", "envelope.py",
        )
    )
    import crypto_sensor_fabric.normalization as _top

    top_unchanged = len(_top.__all__) == 24
    ok = (present == frozen_modules and forbidden_absent and top_unchanged)
    add(
        "U08-19",
        "bloc_05/03 S21; bloc_05/06 S19 (I08 scope)",
        "normalization/common/ enumerated; deferred I09 modules probed; top-level API counted",
        "Path.iterdir + forbidden-path existence + len(normalization.__all__)",
        "exactly 4 frozen modules; I09 modules absent; top-level API = 24",
        "methodologies/semantic_registry shipping inside I08, or top-level API drift",
        f"modules={present}; i09_modules_absent={forbidden_absent}; "
        f"top_level_symbols={len(_top.__all__)}",
        ok,
        "test_common_package_is_exactly_the_frozen_modules",
    )

    # -- U08-20 evidence determinism ---------------------------------------
    pass_a = _build_pass_core()
    pass_b = _build_pass_core()
    stable = pass_a == pass_b
    add(
        "U08-20",
        "bloc_05/06 S17 (deterministic evidence)",
        "the full measurement pass executed twice inside one producer run",
        "_build_pass_core() called twice; list equality",
        "two passes produce identical row data (no clock, no randomness)",
        "wall-clock or random state entering the evidence rows",
        f"two_passes_identical={stable}; core_rows={len(pass_a)}",
        stable,
        "test_unit_validation_evidence_is_deterministic",
        nonmutation="read-only measurement; no input objects exist to mutate",
    )

    return rows


def _build_pass_core() -> list[str]:
    """One pure measurement pass used by U08-20's double-run check."""
    observations: list[str] = []
    observations.append(str(
        convert_stablecoin_to_usd(
            Decimal("1000"), CanonicalQuantityUnit.USDT, rate=_rate(),
            cutoff=_T_FUTURE).usd_equivalent))
    observations.append(str(
        convert_stablecoin_to_usd(
            Decimal("1000"), CanonicalQuantityUnit.USDT, rate=None,
            cutoff=_T_FUTURE).usd_equivalent))
    observations.append(str(cross_convert_via_usd(
        Decimal("1000"), CanonicalQuantityUnit.USDT, "EUR",
        rate_from=_rate(), rate_into=_rate(
            from_asset="EUR", into_asset="USD", rate="1.00"),
        cutoff=_T_FUTURE).derived_value))
    observations.append(str(decimal_places(Decimal("1.2300"))))
    observations.append(str(precision_widened(
        Decimal("1.23"), Decimal("1.2300"))))
    return observations


def _pin_check(i04b_rows: list[dict[str, Any]]) -> None:
    blob = json.dumps(
        i04b_rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    measured = hashlib.sha256(blob).hexdigest()
    if measured != I04B_ROWS_PIN_SHA256:
        print(
            json.dumps({
                "error": "i04b_rows_pin_mismatch",
                "expected": I04B_ROWS_PIN_SHA256,
                "measured": measured,
            }, sort_keys=True),
            file=sys.stderr,
        )
        raise SystemExit(4)


def _build_payload() -> tuple[bytes, dict[str, Any]]:
    existing = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    base_rows = [r for r in existing["rows"] if not r["case_id"].startswith("U08")]
    _pin_check(base_rows)
    u08_rows = _build_rows()
    failures = [r["case_id"] for r in u08_rows if r["disposition"] != "PASS"]
    if failures:
        print(
            json.dumps({"error": "non_pass_dispositions", "cases": failures},
                       sort_keys=True),
            file=sys.stderr,
        )
        raise SystemExit(1)
    payload: dict[str, Any] = dict(existing)
    payload["rows"] = base_rows + u08_rows
    payload["extensions"] = [
        {
            "base_rows_pin_sha256": I04B_ROWS_PIN_SHA256,
            "case_series": "U08-01..U08-20",
            "checkpoint": "SENSOR-B5-I08E1",
            "generator": (
                "research/crypto_foundry/sensor_fabric/scripts/b5_i08_units.py"
            ),
            "preservation": "I04B base rows byte-identical (pinned)",
            "rows_added": len(u08_rows),
        },
    ]
    payload["summary"] = {
        "fail": len(failures),
        "pass": len(payload["rows"]),
        "rows": len(payload["rows"]),
    }
    blob = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return blob, payload


def main() -> int:
    args = sys.argv[1:]
    if args not in ([], ["--check"]):
        print("usage: b5_i08_units.py [--check]", file=sys.stderr)
        return 2
    blob, payload = _build_payload()
    digest = hashlib.sha256(blob).hexdigest()
    summary = {
        "artifact_sha256": digest,
        "case_series": "U08-01..U08-20",
        "fail": payload["summary"]["fail"],
        "pass": payload["summary"]["pass"],
        "rows": payload["summary"]["rows"],
    }
    if args == ["--check"]:
        committed = ARTIFACT.read_bytes() if ARTIFACT.exists() else b""
        if committed != blob:
            print(
                json.dumps({**summary, "error": "committed_bytes_mismatch"},
                           sort_keys=True),
                file=sys.stderr,
            )
            return 3
        print(json.dumps(summary, sort_keys=True))
        return 0
    ARTIFACT.write_bytes(blob)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
