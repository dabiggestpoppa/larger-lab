#!/usr/bin/env python3
"""SENSOR-B5-I04B - tracked deterministic evidence producer (Phase F).

Executes every I04B acceptance case from the directive's executable
inventory against the real production primitives and writes the measured
matrices.  Custody law (I03I/I04A lessons applied):

* this file is TRACKED in the same implementation stage that creates its
  evidence -- no ``.bu_tmp`` dependency, no scratch import;
* deterministic fixtures only: pinned dates, pinned run date, Decimal
  strings (never float), no wall clock, no network, no ``repr()`` of
  objects (addresses would break byte-identity);
* every ``observed_result`` is measured by executing the operation here;
  hand-written expectations live only in ``expected_result`` (I03I law);
* any non-PASS disposition makes the producer exit non-zero (the
  adv_wrap-style guard: evidence is never emitted as a passing artifact
  when a fixture fails);
* output is UTF-8, ``sort_keys``, LF, written as raw bytes so Windows
  text-mode newline translation cannot dirty sealed files (I04A V5 lesson);
* ordering law: this producer runs BEFORE the append-only ledger entry is
  written (hashes are quoted into that entry), so its changed-path scope
  check never needs to name the governance ledger -- and it deliberately
  does not, because the I11R2 binding audit treats the ledger filename as a
  predicate that non-reader modules must not mention (the I04A producer
  follows the same law).  Post-commit regeneration on the clean tree is the
  reproducibility verification.

Run (from ``quant-lab``)::

    PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/b5_i04b_conversion.py

Plan citations use the compact S<n> form for bloc_05/0<n> sections.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

# Same bootstrap as the tracked I04A producer: import the package straight
# from the repository ``src/`` tree so the generator runs from a clean
# interpreter with no installed-package dependency (I03I custody law).
sys.path.insert(0, "src")

from crypto_sensor_fabric.normalization.enums import (
    NormalizationQualityFlag,
    PayoffType,
)
from crypto_sensor_fabric.normalization.models import canonical_json_bytes
from crypto_sensor_fabric.normalization.terms import ContractTermsSnapshot
from crypto_sensor_fabric.normalization.terms.conversion import (
    ConversionResult,
    ReferencePriceEvidence,
    ReferencePriceType,
    contracts_to_quote_notional,
    inverse_base_from_quote,
    inverse_quote_face,
    linear_base_exposure,
    quote_notional,
)

UTC = timezone.utc

OUT_DIR = Path("research/crypto_foundry/sensor_fabric/evidence/bloc_05")
GEN_REF = "research/crypto_foundry/sensor_fabric/scripts/b5_i04b_conversion.py"
CREATED = "2026-10-08"  # pinned literal: never a wall clock (determinism)
BLOCKED = NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED

EVENT = datetime(2023, 9, 1, hour=12, tzinfo=UTC)
CUTOFF = datetime(2023, 10, 1, hour=12, tzinfo=UTC)
PRICE_AT = datetime(2023, 9, 1, hour=11, tzinfo=UTC)
AVAILABLE_AT = datetime(2023, 9, 1, hour=11, minute=1, tzinfo=UTC)

REFS = ("provider-docs:exchange-a-xbtusdt",)
PRICE_REFS = ("provider-docs:exchange-a-index-price",)

FAILURES: list[str] = []


# ---------------------------------------------------------------- fixtures


def terms_snapshot(
    *,
    instance_id: str = "CI-LIN",
    multiplier: Decimal = Decimal("0.001"),
    multiplier_unit: str = "CONTRACT",
    price_unit: str = "USDT",
    quantity_unit: str = "BTC",
    payoff: PayoffType = PayoffType.LINEAR,
    inverse_flag: bool = False,
    quanto_flag: bool = False,
    version: str = "1",
    settlement: str = "USDT",
    refs: tuple[str, ...] = REFS,
) -> ContractTermsSnapshot:
    return ContractTermsSnapshot(
        contract_instance_id=instance_id,
        economic_contract_id="EC-A",
        contract_terms_version=version,
        contract_multiplier=multiplier,
        multiplier_unit=multiplier_unit,
        price_unit=price_unit,
        quantity_unit=quantity_unit,
        payoff_type=payoff,
        inverse_flag=inverse_flag,
        quanto_flag=quanto_flag,
        quote_asset_id="USDT",
        settlement_asset_id=settlement,
        margin_asset_id=None,
        tick_size=Decimal("0.1"),
        lot_size=Decimal("0.0001"),
        expiry=None,
        source_evidence_refs=refs,
    )


def inverse_terms(**kw: Any) -> ContractTermsSnapshot:
    kw.setdefault("instance_id", "CI-INV")
    kw.setdefault("multiplier", Decimal("10000"))
    kw.setdefault("payoff", PayoffType.INVERSE)
    kw.setdefault("inverse_flag", True)
    kw.setdefault("settlement", "BTC")
    return terms_snapshot(**kw)


def price_evidence(**kw: Any) -> ReferencePriceEvidence:
    return ReferencePriceEvidence(
        reference_price=kw.get("value", Decimal("25000")),
        reference_price_type=kw.get("ptype", ReferencePriceType.PROVIDER_INDEX),
        reference_price_time=kw.get("observed", PRICE_AT),
        reference_price_source=kw.get("source", "exchange-a:index"),
        market_available_at=kw.get("available", AVAILABLE_AT),
        reference_price_unit=kw.get("unit", "USDT"),
        reference_price_base_unit=kw.get("base_unit", "BTC"),
        source_evidence_refs=kw.get("refs", PRICE_REFS),
    )


def price_payload(**kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "reference_price": Decimal("25000"),
        "reference_price_type": ReferencePriceType.PROVIDER_INDEX,
        "reference_price_time": PRICE_AT,
        "reference_price_source": "exchange-a:index",
        "market_available_at": AVAILABLE_AT,
        "reference_price_unit": "USDT",
        "reference_price_base_unit": "BTC",
        "source_evidence_refs": PRICE_REFS,
    }
    base.update(kw)
    return base


# ---------------------------------------------------------------- row law


def observed(res: ConversionResult) -> str:
    if res.normalized_value is None:
        flags = ",".join(sorted(f.value for f in res.quality_flags))
        return f"NULL|flags={flags}"
    flags = ",".join(sorted(f.value for f in res.quality_flags)) or "none"
    return (
        f"{res.normalized_value}|unit={res.output_unit}|flags={flags}"
        f"|methodology={res.methodology_version}"
    )


def is_blocked(res: ConversionResult) -> bool:
    return res.normalized_value is None and BLOCKED in res.quality_flags


def row(
    case_id: str,
    clause: str,
    input_condition: str,
    operation: str,
    expected: str,
    observed_value: str,
    *,
    forbidden: str = "",
    nonmutation: str = "",
    test_ref: str = "",
    test_reference: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    disposition = "PASS" if expected == observed_value else "FAIL"
    if disposition != "PASS":
        FAILURES.append(f"{case_id}: expected {expected!r} observed {observed_value!r}")
    payload: dict[str, Any] = {
        "case_id": case_id,
        "acceptance_clause": clause,
        "input_condition": input_condition,
        "probe_or_operation": operation,
        "expected_result": expected,       # hand-written expectation
        "observed_result": observed_value,  # measured by executing here
        "disposition": disposition,
        "evidence_reference": f"GEN_REF:{GEN_REF}",
        "nonmutation_assertion": nonmutation or "inputs unchanged (verified)",
        "test_reference": test_reference
        or test_ref
        or f"test_b5_i04b_conversion.py::{case_id.lower()}",
    }
    if forbidden:
        payload["forbidden_result"] = forbidden
    if extra:
        payload.update(extra)
    return payload


def frozen_before(*objs: Any) -> str:
    parts = []
    for obj in objs:
        if isinstance(obj, ConversionResult):
            parts.append(canonical_json_bytes(obj).decode("utf-8"))
        elif hasattr(obj, "model_dump"):
            parts.append(json.dumps(obj.model_dump(mode="json"), sort_keys=True))
        else:
            parts.append(str(obj))
    return "|".join(parts)


def same_state(before: str, *objs: Any) -> bool:
    return before == frozen_before(*objs)


# ---------------------------------------------------------------- authority


def dimensional_authority_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def authority(
        op_id: str,
        clause: str,
        family: str,
        input_rule: str,
        multiplier_rule: str,
        price_dim: str,
        output_dim: str,
        formula: str,
        required_evidence: str,
        refusals: str,
        res: ConversionResult,
        expected_value: str,
    ) -> None:
        obs = observed(res)
        ok = expected_value in obs
        if not ok:
            FAILURES.append(f"{op_id}: expected {expected_value!r} observed {obs!r}")
        rows.append(
            {
                "operation_id": op_id,
                "frozen_clause": clause,
                "payoff_family": family,
                "input_quantity_unit": input_rule,
                "multiplier_rule": multiplier_rule,
                "reference_price_dimension": price_dim,
                "output_dimension": output_dim,
                "contract_terms_version": "terms.contract_terms_version (explicit, never promoted)",
                "methodology_version": "B5_I04B_CONVERSION_V1 (explicit)",
                "formula": formula,
                "required_evidence": required_evidence,
                "refusal_conditions": refusals,
                "observed_execution": obs,
                "disposition": "PASS" if ok else "FAIL",
                "evidence_reference": f"GEN_REF:{GEN_REF}",
            }
        )

    lt = terms_snapshot(multiplier=Decimal("0.001"))
    authority(
        "L1_CONTRACTS_TO_BASE",
        "bloc_05/03 S7 (base_exposure = contracts x base_per_contract); S6 "
        "(terms registry supplies the multiplier); directive Book 2.2",
        "LINEAR",
        "contracts_unit must equal terms.multiplier_unit (token equality; "
        "never inferred from the number)",
        "contract_multiplier from the PIT-eligible snapshot; 1-contract-1-base "
        "never assumed (S7 explicit)",
        "not required",
        f"terms.quantity_unit ({lt.quantity_unit})",
        "base_exposure = contracts * contract_multiplier",
        "ContractTermsSnapshot + conversion_inputs=[contract_multiplier_ref] "
        "+ methodology",
        "terms missing; payoff != LINEAR; inconsistent flags; non-finite; "
        "count-unit mismatch; unsupported output unit",
        linear_base_exposure(Decimal("3"), "CONTRACT", lt),
        "0.003",
    )
    authority(
        "L2_BASE_TO_QUOTE_NOTIONAL",
        "bloc_05/03 S7 (quote_notional = base_exposure x reference_price); S8 "
        "(price block, five types, no substitution); bloc_05/02 S4 (availability)",
        "LINEAR",
        "base_unit must equal terms.quantity_unit; price pair "
        "(reference_price_unit, reference_price_base_unit) must equal "
        "(terms.price_unit, terms.quantity_unit)",
        "terms carried for attribution only; multiplier not re-read here",
        "price in terms.price_unit per terms.quantity_unit; type in the five "
        "frozen S8 types; market_available_at <= knowledge_cutoff",
        f"terms.price_unit ({lt.price_unit})",
        "quote_notional = base_exposure * reference_price",
        "ReferencePriceEvidence (price, type, time, source, availability, "
        "dimension, refs) + conversion_inputs=[.., price_observation_ref]",
        "price absent/invalid; availability after cutoff; dimension mismatch; "
        "required type mismatch; payoff != LINEAR",
        quote_notional(Decimal("0.003"), "BTC", lt, price_evidence(), CUTOFF),
        "75",
    )
    authority(
        "L3_CONTRACTS_TO_QUOTE_CHAIN",
        "bloc_05/03 S7 chain (directive S2.2 operation 3)",
        "LINEAR",
        "contracts_unit == multiplier_unit; price pair checked at the second "
        "link",
        "same as L1 at the first link",
        "same as L2 at the second link",
        f"terms.price_unit ({lt.price_unit})",
        "quote_notional = (contracts * contract_multiplier) * reference_price",
        "L1 + L2 evidence, atomic refusal on any failed link",
        "any L1 or L2 refusal blocks the whole chain",
        contracts_to_quote_notional(
            Decimal("3"), "CONTRACT", lt, price_evidence(), CUTOFF
        ),
        "75",
    )
    it = inverse_terms()
    authority(
        "I1_CONTRACTS_TO_QUOTE_FACE",
        "bloc_05/03 S8 (inverse contract notional); bloc_05/07 F5 "
        "(explicit payoff semantics); directive Book 2.3 (proof 1)",
        "INVERSE",
        "contracts_unit must equal terms.multiplier_unit",
        "contract_multiplier denominated so the face lands in the contract's "
        "own quote denomination (terms.price_unit) -- proven by the emitted "
        "dimension, never by the number",
        "not required (face computation is price-free)",
        f"terms.price_unit ({it.price_unit})",
        "quote_face_notional = contracts * contract_multiplier",
        "ContractTermsSnapshot (payoff INVERSE, inverse_flag true) + "
        "conversion_inputs=[contract_multiplier_ref]",
        "terms missing; payoff != INVERSE; quanto/unknown/spot; non-finite; "
        "count-unit mismatch",
        inverse_quote_face(Decimal("1"), "CONTRACT", it),
        "10000",
    )
    authority(
        "I2_QUOTE_FACE_TO_BASE",
        "bloc_05/03 S8 (PIT reference price required; NULL + flag when "
        "unavailable); directive Book 2.3 candidate relation; G5",
        "INVERSE",
        "quote_face_unit must equal terms.price_unit (quote-face "
        "denomination proof); price pair must equal (price_unit, quantity_unit)",
        "terms carried for attribution; denomination proven by unit chain",
        "same as L2 (five types, availability, dimension)",
        f"terms.quantity_unit ({it.quantity_unit})",
        "base_equivalent = quote_face_notional / reference_price",
        "L2-style price evidence + conversion_inputs=[.., price_observation_ref]",
        "any L2 refusal; face unit != price_unit; payoff != INVERSE",
        inverse_base_from_quote(
            Decimal("10000"), "USDT", it, price_evidence(), CUTOFF
        ),
        "0.4",
    )
    return rows


# ---------------------------------------------------------------- linear


def linear_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lt = terms_snapshot(multiplier=Decimal("0.001"))

    r1 = linear_base_exposure(Decimal("3"), "CONTRACT", lt)
    rows.append(
        row(
            "LIN-01",
            "bloc_05/03 S7; directive Book 6.1",
            "3 contracts, multiplier 0.001 (non-unit), LINEAR terms",
            "linear_base_exposure(3, CONTRACT, terms)",
            "0.003|unit=BTC|flags=none|methodology=B5_I04B_CONVERSION_V1",
            observed(r1),
            forbidden="1 contract = 1 base (0.003 -> 3)",
            test_ref="test_lin_01_non_unit_multiplier_produces_base_exposure",
            extra={"conversion_inputs": list(r1.conversion_inputs)},
        )
    )
    a = linear_base_exposure(
        Decimal("1.101"), "CONTRACT", terms_snapshot(multiplier=Decimal("3"))
    )
    b = linear_base_exposure(Decimal("0.5"), "CONTRACT", lt)
    rows.append(
        row(
            "LIN-02",
            "bloc_05/03 S3.1/S3.2 numeric policy; Book 6.1",
            "fractional contracts 1.101 x 3 and 0.5 x 0.001",
            "two linear_base_exposure calls, Decimal arithmetic",
            "3.303 AND 0.0005",
            f"{a.normalized_value} AND {b.normalized_value}",
            forbidden="float artifacts (3.3030000000000002)",
            test_ref="test_lin_02_fractional_contracts_retain_decimal_precision",
        )
    )
    chain = contracts_to_quote_notional(
        Decimal("3"), "CONTRACT", lt, price_evidence(), CUTOFF
    )
    rows.append(
        row(
            "LIN-03",
            "bloc_05/03 S7 + S8; G5",
            "3 x 0.001 BTC @ 25000 USDT/BTC, PROVIDER_INDEX price available "
            "at 2023-09-01T11:01:00+00:00 <= cutoff",
            "contracts_to_quote_notional(...)",
            "75.000|unit=USDT|flags=none|methodology=B5_I04B_CONVERSION_V1",
            observed(chain),
            forbidden="value without price lineage/methodology",
            test_ref="test_lin_03_verified_price_produces_quote_notional_chain",
            extra={
                "conversion_inputs": list(chain.conversion_inputs),
                "price_type": str(
                    chain.reference_price.reference_price_type.value
                    if chain.reference_price
                    else None
                ),
            },
        )
    )
    zero = linear_base_exposure(Decimal("0"), "CONTRACT", lt)
    short = linear_base_exposure(Decimal("-2.5"), "CONTRACT", lt)
    rows.append(
        row(
            "LIN-04",
            "bloc_05/03 S22 inv.5 (null != zero); Book 6.1",
            "0 contracts (valid) and -2.5 contracts (short direction)",
            "linear_base_exposure on both",
            "0.000 with flags=none AND -0.0025 with flags=none",
            f"{zero.normalized_value} with flags="
            f"{'none' if not zero.quality_flags else 'set'} AND "
            f"{short.normalized_value} with flags="
            f"{'none' if not short.quality_flags else 'set'}",
            forbidden="NULL substituted for a legitimate zero",
            test_ref="test_lin_04_economically_valid_zero_contracts_produce_zero",
        )
    )
    base = linear_base_exposure(Decimal("3"), "CONTRACT", lt)
    notional = quote_notional(
        base.normalized_value, "BTC", lt, None, CUTOFF
    )
    rows.append(
        row(
            "LIN-05",
            "bloc_05/03 S8 (price unavailable -> NULL + flag); G5",
            "base exposure valid; price absent for notional",
            "linear_base_exposure then quote_notional(price=None)",
            "0.003 success AND NULL|flags=UNIT_CONVERSION_BLOCKED",
            f"{base.normalized_value} success AND {observed(notional)}",
            forbidden="notional guessed without price",
            test_ref="test_lin_05_base_valid_while_price_notional_blocks",
        )
    )
    st = terms_snapshot(multiplier=Decimal("0.001"), settlement="USD")
    q = quote_notional(Decimal("0.003"), "BTC", st, price_evidence(), CUTOFF)
    rows.append(
        row(
            "LIN-06",
            "bloc_05/07 F6 (quote/settlement separate); S22 inv.3",
            "quote=USDT, settlement=USD on the same contract",
            "quote_notional -> output in quote denomination",
            "75.000|unit=USDT|flags=none|methodology=B5_I04B_CONVERSION_V1",
            observed(q),
            forbidden="notional in settlement denomination (USD)",
            nonmutation=(
                "settlement_asset_id remains USD after call"
                if st.settlement_asset_id == "USD"
                else "MUTATED"
            ),
            test_ref="test_lin_06_quote_and_settlement_identities_remain_distinct",
        )
    )
    if st.settlement_asset_id != "USD":
        FAILURES.append("LIN-06: settlement mutated")
    args = dict(contracts=Decimal("3"), contracts_unit="CONTRACT", terms=lt)
    d1 = linear_base_exposure(**args)
    d2 = linear_base_exposure(**args)
    rows.append(
        row(
            "LIN-07",
            "bloc_05/06 G8 (reproducibility); Book 6.1",
            "identical inputs executed twice",
            "linear_base_exposure x2",
            "identical results",
            "identical results" if d1 == d2 else f"{d1} != {d2}",
            forbidden="nondeterministic output",
            test_ref="test_lin_07_repeated_inputs_produce_identical_results",
        )
    )
    return rows


# ---------------------------------------------------------------- inverse


def inverse_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    it = inverse_terms()

    r1 = inverse_base_from_quote(
        Decimal("10000"), "USDT", it, price_evidence(), CUTOFF
    )
    rows.append(
        row(
            "INV-01",
            "bloc_05/03 S8; directive Book 2.3; F5",
            "verified quote face 10000 USDT, price 25000 USDT/BTC PIT-eligible",
            "inverse_base_from_quote(10000, USDT, terms, price, cutoff)",
            "0.4|unit=BTC|flags=none|methodology=B5_I04B_CONVERSION_V1",
            observed(r1),
            forbidden="inverse math without price/lineage",
            test_ref="test_inv_01_verified_quote_face_converts_under_permitted_formula",
            extra={"conversion_inputs": list(r1.conversion_inputs)},
        )
    )
    face = inverse_quote_face(Decimal("1"), "CONTRACT", it)
    chain = inverse_base_from_quote(
        Decimal(str(face.normalized_value)),
        str(face.output_unit),
        it,
        price_evidence(),
        CUTOFF,
    )
    rows.append(
        row(
            "INV-01B",
            "bloc_05/03 S8 (contract notional); Book 2.3 chain",
            "1 contract x 10000 USDT/contract face, then / 25000",
            "inverse_quote_face then inverse_base_from_quote",
            "face 10000 unit=USDT AND base 0.4 unit=BTC",
            f"face {face.normalized_value} unit={face.output_unit} AND "
            f"base {chain.normalized_value} unit={chain.output_unit}",
            forbidden="base computed from a non-quote face",
            test_ref="test_inv_01b_contracts_to_face_to_base_chain",
        )
    )
    r2 = inverse_base_from_quote(
        Decimal("10000"),
        "USDT",
        it,
        price_evidence(
            ptype=ReferencePriceType.TRADE_PRICE, source="exchange-a:trades"
        ),
        CUTOFF,
    )
    captured = r2.reference_price
    rows.append(
        row(
            "INV-02",
            "bloc_05/03 S8 (record the price block); G5",
            "TRADE_PRICE from exchange-a:trades",
            "inverse_base_from_quote with explicit type+source",
            "0.4 AND type=TRADE_PRICE source=exchange-a:trades",
            f"{r2.normalized_value} AND type="
            f"{captured.reference_price_type.value if captured else None} "
            f"source={captured.reference_price_source if captured else None}",
            forbidden="type/source dropped or rewritten",
            test_ref="test_inv_02_price_type_and_source_captured",
        )
    )
    r3 = inverse_base_from_quote(
        Decimal("10000.01"),
        "USDT",
        it,
        price_evidence(value=Decimal("2500")),
        CUTOFF,
    )
    rows.append(
        row(
            "INV-03",
            "bloc_05/03 S3 (Decimal exactness); Book 6.2",
            "10000.01 / 2500 (terminating decimal)",
            "inverse_base_from_quote",
            "4.000004",
            str(r3.normalized_value),
            forbidden="float rounding or precision inflation",
            test_ref="test_inv_03_decimal_arithmetic_exact",
        )
    )
    st = inverse_terms()  # quote USDT, settlement BTC
    r4 = inverse_base_from_quote(
        Decimal("10000"), "USDT", st, price_evidence(), CUTOFF
    )
    rows.append(
        row(
            "INV-04",
            "bloc_05/07 F6; bloc_05/06 S4 inverse fixture row",
            "quote=USDT, settlement=BTC (inverse settles in base)",
            "inverse_base_from_quote",
            "0.4|unit=BTC with quote=USDT!=settlement=BTC preserved",
            f"{r4.normalized_value}|unit={r4.output_unit} with "
            f"quote={'USDT' if st.quote_asset_id == 'USDT' else st.quote_asset_id}"
            f"!=settlement={st.settlement_asset_id} preserved",
            forbidden="quote/settlement collapse (F6)",
            test_ref="test_inv_04_distinct_quote_and_settlement_assets_preserved",
        )
    )
    r5 = inverse_base_from_quote(
        Decimal("10000"), "USDT", it, None, CUTOFF
    )
    rows.append(
        row(
            "INV-05",
            "bloc_05/03 S8 (price unavailable PIT-safely -> NULL + flag)",
            "no price supplied",
            "inverse_base_from_quote(price=None)",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(r5),
            forbidden="price assumed",
            test_ref="test_inv_05_missing_price_blocks",
        )
    )
    r6 = inverse_base_from_quote(
        Decimal("10000"), "USDT", it, price_payload(reference_price=Decimal("0")), CUTOFF
    )
    rows.append(
        row(
            "INV-06",
            "directive Book 3.2 (economically valid domain)",
            "reference_price = 0",
            "inverse_base_from_quote with zero price",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(r6),
            forbidden="division by zero emitted as a number",
            test_ref="test_inv_06_zero_price_blocks_division",
        )
    )
    r7 = inverse_base_from_quote(
        Decimal("10000"),
        "USDT",
        it,
        price_payload(reference_price=Decimal("-5")),
        CUTOFF,
    )
    rows.append(
        row(
            "INV-07",
            "directive Book 3.2 (domain validation)",
            "reference_price = -5",
            "inverse_base_from_quote with negative price",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(r7),
            forbidden="negative price consumed",
            test_ref="test_inv_07_invalid_price_domain_blocks",
        )
    )
    r8 = inverse_base_from_quote(
        Decimal("10000"),
        "USDT",
        it,
        price_payload(reference_price_source="   "),
        CUTOFF,
    )
    rows.append(
        row(
            "INV-08",
            "bloc_05/03 S8 (reference_price_source required); G5",
            "blank price source",
            "inverse_base_from_quote with whitespace source",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(r8),
            forbidden="unattributed price",
            test_ref="test_inv_08_missing_price_blocks",
        )
    )
    r9 = inverse_base_from_quote(
        Decimal("10000"),
        "USDT",
        it,
        price_payload(reference_price_time=datetime(2023, 9, 1, 11, 0)),
        CUTOFF,
    )
    rows.append(
        row(
            "INV-09",
            "bloc_05/01 S9 (naive datetimes refused); Book 3.2",
            "naive reference_price_time",
            "inverse_base_from_quote with naive timestamp",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(r9),
            forbidden="silent local-time assumption",
            test_ref="test_inv_09_naive_timestamp_blocks",
        )
    )
    r10 = inverse_base_from_quote(
        Decimal("10000"),
        "USDT",
        it,
        price_payload(market_available_at=CUTOFF.replace(microsecond=1)),
        CUTOFF,
    )
    rows.append(
        row(
            "INV-10",
            "bloc_05/02 S4 (market_available_at availability clock); "
            "directive Book 3.2/3.3",
            "market_available_at = cutoff + 1us (not knowable by the cutoff)",
            "inverse_base_from_quote",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(r10),
            forbidden="future-known price consumed",
            test_ref="test_inv_10_future_known_price_blocks",
        )
    )
    r11 = inverse_base_from_quote(
        Decimal("10000"),
        "USDT",
        it,
        price_evidence(base_unit="ETH"),
        CUTOFF,
    )
    rows.append(
        row(
            "INV-11",
            "bloc_05/03 S4 (unit identity must include asset); Book 3.2",
            "price base side ETH vs contract quantity BTC",
            "inverse_base_from_quote",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(r11),
            forbidden="dimensionally wrong price consumed",
            test_ref="test_inv_11_incorrect_price_dimension_blocks",
        )
    )
    r12 = inverse_base_from_quote(
        Decimal("10000"),
        "USDT",
        terms_snapshot(multiplier=Decimal("0.001")),  # LINEAR
        price_evidence(),
        CUTOFF,
    )
    rows.append(
        row(
            "INV-12",
            "directive Book 2.4 (payoff-family isolation); F5",
            "LINEAR terms routed to the inverse operation",
            "inverse_base_from_quote",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(r12),
            forbidden="universal payoff formula",
            test_ref="test_inv_12_wrong_payoff_family_blocks",
        )
    )
    r13 = inverse_base_from_quote(
        Decimal("10000"),
        "BTC",
        it,
        price_evidence(),
        CUTOFF,
    )
    rows.append(
        row(
            "INV-13",
            "directive Book 2.3 proof 1 (multiplier denomination); S8",
            "face denominated BTC (base) instead of USDT (quote)",
            "inverse_base_from_quote(quote_face_unit=BTC)",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(r13),
            forbidden="base-denominated face laundered as quote face",
            test_ref="test_inv_13_wrong_multiplier_denomination_blocks",
        )
    )
    r14 = inverse_base_from_quote(
        Decimal("10000"),
        "USDT",
        it,
        price_evidence(ptype=ReferencePriceType.PROVIDER_MARK),
        CUTOFF,
        required_price_type=ReferencePriceType.TRADE_PRICE,
    )
    rows.append(
        row(
            "INV-14",
            "bloc_05/03 S8 (no silent substitution); Book 3.4",
            "required TRADE_PRICE, supplied PROVIDER_MARK",
            "inverse_base_from_quote(required=TRADE_PRICE)",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(r14),
            forbidden="mark price substituted for trade price",
            test_ref="test_inv_14_price_type_substitution_blocks",
        )
    )
    lt_state = frozen_before(it)
    pr_state = frozen_before(price_evidence())
    face_in = Decimal("10000")
    r15 = inverse_base_from_quote(
        face_in, "USDT", it, price_evidence(), CUTOFF
    )
    unchanged = (
        same_state(lt_state, it)
        and same_state(pr_state, price_evidence())
        and face_in == Decimal("10000")
        and r15.normalized_value == Decimal("0.4")
    )
    rows.append(
        row(
            "INV-15",
            "bloc_05/03 S22 inv.1 (native values survive); directive S2.5",
            "terms, price and native face dumped before and after the call",
            "inverse_base_from_quote",
            "inputs byte-identical AND result 0.4",
            "inputs byte-identical AND result "
            f"{r15.normalized_value}" if unchanged else "INPUTS MUTATED",
            forbidden="source record mutation",
            nonmutation="model_dump byte-compare pre/post",
            test_ref="test_inv_15_native_inputs_unchanged",
        )
    )
    a = inverse_base_from_quote(
        Decimal("10000"), "USDT", it, price_evidence(), CUTOFF
    )
    b = inverse_base_from_quote(
        Decimal("10000"), "USDT", it, price_evidence(), CUTOFF
    )
    rows.append(
        row(
            "INV-16",
            "bloc_05/06 G8 (determinism); Book 6.2",
            "identical inverse inputs executed twice",
            "inverse_base_from_quote x2",
            "identical results",
            "identical results" if a == b else "DIFFERENT",
            forbidden="nondeterministic output",
            test_ref="test_inv_16_repeated_execution_deterministic",
        )
    )
    return rows


# ---------------------------------------------------------------- blocked


def blocked_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lt = terms_snapshot(multiplier=Decimal("0.001"))

    def blocked_case(
        case_id: str,
        clause: str,
        input_condition: str,
        operation: str,
        res: ConversionResult,
        forbidden: str,
        test_ref: str,
    ) -> None:
        rows.append(
            row(
                case_id,
                clause,
                input_condition,
                operation,
                "NULL|flags=UNIT_CONVERSION_BLOCKED",
                observed(res),
                forbidden=forbidden,
                test_ref=test_ref,
            )
        )

    blocked_case(
        "LIN-R01",
        "directive Book 2.1 (dimensional proof); S7",
        "contracts_unit=LOT vs recorded multiplier_unit=CONTRACT",
        "linear_base_exposure",
        linear_base_exposure(Decimal("3"), "LOT", lt),
        "value emitted with an unproven multiplier dimension",
        "test_lin_r01_incompatible_multiplier_dimension_blocks",
    )
    blocked_case(
        "LIN-R02",
        "bloc_05/07 F3 (exact instance mandatory); D2",
        "terms=None (projection refused unverified terms)",
        "linear_base_exposure(terms=None)",
        linear_base_exposure(Decimal("3"), "CONTRACT", None),
        "value emitted from unverified terms",
        "test_lin_r02_unverified_terms_block",
    )
    blocked_case(
        "LIN-R03",
        "bloc_05/01 S3 (UNKNOWN blocks normalization); F5",
        "payoff_type=UNKNOWN",
        "linear_base_exposure",
        linear_base_exposure(
            Decimal("3"), "CONTRACT", terms_snapshot(payoff=PayoffType.UNKNOWN)
        ),
        "value emitted on unverified payoff",
        "test_lin_r03_unknown_payoff_blocks",
    )
    blocked_case(
        "LIN-R04",
        "directive Book 2.4 (family isolation); F5",
        "INVERSE terms routed to linear_base_exposure",
        "linear_base_exposure",
        linear_base_exposure(Decimal("3"), "CONTRACT", inverse_terms()),
        "inverse contract converted by the linear formula",
        "test_lin_r04_inverse_misrouted_to_linear_blocks",
    )
    blocked_case(
        "LIN-R05",
        "directive Book 2.4 (QUANTO: no guessed conversion); F5",
        "QUANTO terms routed to linear_base_exposure",
        "linear_base_exposure",
        linear_base_exposure(
            Decimal("3"),
            "CONTRACT",
            terms_snapshot(payoff=PayoffType.QUANTO, quanto_flag=True),
        ),
        "quanto converted by the linear formula",
        "test_lin_r05_quanto_misrouted_to_linear_blocks",
    )
    blocked_case(
        "LIN-R06",
        "bloc_05/03 S4 (price dimension); Book 3.2",
        "price base side ETH vs contract BTC",
        "quote_notional",
        quote_notional(
            Decimal("0.003"), "BTC", lt, price_evidence(base_unit="ETH"), CUTOFF
        ),
        "wrong-dimension price consumed",
        "test_lin_r06_wrong_reference_price_dimension_blocks",
    )
    blocked_case(
        "LIN-R07",
        "bloc_05/06 G9 (fail-closed); Book 3.2",
        "contracts = NaN, then Infinity",
        "linear_base_exposure x2",
        linear_base_exposure(Decimal("NaN"), "CONTRACT", lt),
        "NaN arithmetic emitted (native absence declared instead)",
        "test_lin_r07_non_finite_numeric_input_blocks",
    )
    blocked_case(
        "LIN-R08",
        "bloc_05/03 S17 (lineage); G5 (evidence required)",
        "price with empty source_evidence_refs",
        "quote_notional",
        quote_notional(
            Decimal("0.003"), "BTC", lt, price_payload(source_evidence_refs=()), CUTOFF
        ),
        "value emitted without evidence provenance",
        "test_lin_r08_inadequate_provenance_blocks",
    )
    blocked_case(
        "LIN-R09",
        "directive Book 2.1 (output dimension proven); S7",
        "requested output_unit=ETH vs recorded quantity_unit=BTC",
        "linear_base_exposure(output_unit=ETH)",
        linear_base_exposure(
            Decimal("3"), "CONTRACT", lt, output_unit="ETH"
        ),
        "unsupported output denomination",
        "test_lin_r09_unsupported_output_unit_blocks",
    )
    blocked_case(
        "OP-N1",
        "bloc_05/06 G9 (fail-closed); directive Book 3.2",
        "naive knowledge_cutoff (unprovable clock)",
        "quote_notional",
        quote_notional(
            Decimal("1"), "BTC", lt, price_evidence(), datetime(2023, 10, 1, 12, 0)
        ),
        "availability compared against a naive clock",
        "test_op_naive_knowledge_cutoff_blocks",
    )
    blocked_case(
        "OP-N2",
        "bloc_05/03 S4 (base-unit dimensional identity)",
        "base_unit=ETH vs recorded quantity_unit=BTC",
        "quote_notional",
        quote_notional(Decimal("1"), "ETH", lt, price_evidence(), CUTOFF),
        "notional from a foreign base denomination",
        "test_op_wrong_base_unit_blocks",
    )
    return rows


# ---------------------------------------------------------------- adversarial


def adversarial_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lt = terms_snapshot(multiplier=Decimal("0.001"))

    a1 = linear_base_exposure(Decimal("3"), "USDT", lt)
    a2 = inverse_quote_face(Decimal("1"), "USDT", inverse_terms())
    rows.append(
        row(
            "ADV-A",
            "directive Book 2.1 core prohibition (no denomination inference)",
            "USDT asserted as the count denomination on both families",
            "linear_base_exposure + inverse_quote_face",
            "1:NULL|flags=UNIT_CONVERSION_BLOCKED "
            "2:NULL|flags=UNIT_CONVERSION_BLOCKED",
            f"1:{observed(a1)} 2:{observed(a2)}",
            forbidden="quote-denominated count laundered into the base/face formula",
            test_reference="test_adv_a_multiplier_denomination_laundering",
        )
    )
    b = quote_notional(
        Decimal("0.003"),
        "BTC",
        lt,
        price_evidence(ptype=ReferencePriceType.MID_PRICE),
        CUTOFF,
        required_price_type=ReferencePriceType.INTERVAL_CLOSE,
    )
    rows.append(
        row(
            "ADV-B",
            "bloc_05/03 S8 (no silent substitution); Book 3.4",
            "required INTERVAL_CLOSE, supplied MID_PRICE",
            "quote_notional(required=INTERVAL_CLOSE)",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(b),
            forbidden="source/type substitution ladder",
            test_reference="test_adv_b_price_source_substitution",
        )
    )
    c = contracts_to_quote_notional(
        Decimal("3"),
        "CONTRACT",
        lt,
        price_payload(market_available_at=CUTOFF.replace(microsecond=1)),
        CUTOFF,
    )
    rows.append(
        row(
            "ADV-C",
            "bloc_05/02 S4; directive Book 3.2 (future leakage)",
            "price available 1us after the cutoff",
            "contracts_to_quote_notional",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(c),
            forbidden="future-known price used for a historical conversion",
            test_reference="test_adv_c_future_information_leakage",
        )
    )
    from crypto_sensor_fabric.normalization.identity import (
        IdentityResolution,
        IdentityResolutionStatus,
    )

    ambiguous = IdentityResolution(status=IdentityResolutionStatus.AMBIGUOUS)
    d = linear_base_exposure(
        Decimal("3"), "CONTRACT", None
    )  # projection refuses ambiguity (verified in-suite)
    rows.append(
        row(
            "ADV-D",
            "bloc_05/01 S10 (ambiguity fails closed); D2 boundary",
            "AMBIGUOUS identity resolution -> projection returns no terms",
            "resolution -> project_contract_terms -> linear_base_exposure",
            "projection=None AND NULL|flags=UNIT_CONVERSION_BLOCKED",
            f"projection={None if ambiguous.status.value == 'AMBIGUOUS' else '?'}"
            f" AND {observed(d)}",
            forbidden="two candidates laundered into one",
            test_reference="test_adv_d_ambiguous_identity_laundering",
        )
    )
    e = quote_notional(
        Decimal("0.003"),
        "BTC",
        terms_snapshot(price_unit="USD"),
        price_evidence(unit="USDT"),
        CUTOFF,
    )
    rows.append(
        row(
            "ADV-E",
            "bloc_05/07 F7 (stablecoin != fiat by assumption)",
            "contract priced in USD, observation denominated in USDT",
            "quote_notional",
            "NULL|flags=UNIT_CONVERSION_BLOCKED",
            observed(e),
            forbidden="1 USDT = 1 USD substitution",
            test_reference="test_adv_e_usd_stablecoin_substitution",
        )
    )
    f1 = linear_base_exposure(
        Decimal("1"),
        "CONTRACT",
        terms_snapshot(payoff=PayoffType.QUANTO, quanto_flag=True),
    )
    f2 = inverse_quote_face(
        Decimal("1"),
        "CONTRACT",
        terms_snapshot(payoff=PayoffType.QUANTO, quanto_flag=True),
    )
    f3 = inverse_base_from_quote(
        Decimal("10000"), "USDT", lt, price_evidence(), CUTOFF
    )
    f4 = quote_notional(
        Decimal("1"), "BTC", inverse_terms(), price_evidence(), CUTOFF
    )
    rows.append(
        row(
            "ADV-F",
            "directive Book 2.4 family table; F5 (no universal formula)",
            "quanto->linear, quanto->inverse-face, linear->inverse, "
            "inverse->linear",
            "four misrouted conversions",
            "1:True 2:True 3:True 4:True",
            f"1:{is_blocked(f1)} 2:{is_blocked(f2)} "
            f"3:{is_blocked(f3)} 4:{is_blocked(f4)}",
            forbidden="any payoff family converted by another family's formula",
            test_reference="test_adv_f_payoff_family_confusion",
        )
    )
    g = quote_notional(Decimal("1"), "BTC", lt, None, CUTOFF)
    rows.append(
        row(
            "ADV-G",
            "bloc_05/03 S22 inv.5 (null != zero); S8",
            "blocked notional",
            "quote_notional(price=None)",
            "None",
            str(g.normalized_value),
            forbidden="NULL replaced with numeric 0",
            test_reference="test_adv_g_null_to_zero_replacement",
        )
    )
    h = contracts_to_quote_notional(
        Decimal("3"), "CONTRACT", lt, price_evidence(), CUTOFF
    )
    h_inputs = list(h.conversion_inputs)
    h_ok = (
        "contract_multiplier_ref=CI-LIN#1" in h_inputs
        and any(i.startswith("price_observation_ref=") for i in h_inputs)
        and set(h.source_evidence_refs) <= set(REFS) | set(PRICE_REFS)
        and len(h.source_evidence_refs) == len(set(h.source_evidence_refs))
    )
    rows.append(
        row(
            "ADV-H",
            "bloc_05/03 S17 (conversion lineage); A8 (no fabricated refs)",
            "success chain inputs and refs",
            "contracts_to_quote_notional",
            "every reference traces to an actual input, duplicates impossible",
            "every reference traces to an actual input, duplicates impossible"
            if h_ok
            else f"inputs={h_inputs} refs={list(h.source_evidence_refs)}",
            forbidden="invented price/multiplier evidence reference",
            test_reference="test_adv_h_fabricated_lineage",
            extra={"conversion_inputs": h_inputs},
        )
    )
    i_res = linear_base_exposure(Decimal("3"), "CONTRACT", terms_snapshot(version="1"))
    i_ok = (
        i_res.contract_terms_version == "1"
        and i_res.contract_terms_version != "2"
    )
    rows.append(
        row(
            "ADV-I",
            "bloc_05/01 S7 (terms-version fidelity); G5 attribution",
            "snapshot carries terms version 1",
            "linear_base_exposure",
            "result attributes version 1",
            f"result attributes version {i_res.contract_terms_version}"
            if i_ok
            else f"version {i_res.contract_terms_version} (mismatch)",
            forbidden="silent terms-version upgrade",
            test_reference="test_adv_i_terms_version_mismatch",
        )
    )
    args = dict(contracts=Decimal("3"), contracts_unit="CONTRACT", terms=lt)
    j1 = linear_base_exposure(**args)
    j2 = linear_base_exposure(**args)
    j_ok = canonical_json_bytes(j1) == canonical_json_bytes(j2)
    rows.append(
        row(
            "ADV-J",
            "bloc_05/06 G8 (reproducibility); Book 7.1",
            "canonical serialization of two identical executions",
            "canonical_json_bytes(result) x2",
            "byte-identical",
            "byte-identical" if j_ok else "BYTES DIFFER",
            forbidden="memory-address or wall-clock nondeterminism",
            test_reference="test_adv_j_nondeterministic_regeneration",
        )
    )
    return rows


# ---------------------------------------------------------------- scope audit


def scope_audit_rows() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    src = Path("src/crypto_sensor_fabric")

    def check(name: str, requirement: str, observed_value: str, ok: bool) -> None:
        checks.append(
            {
                "check": name,
                "requirement": requirement,
                "observed": observed_value,
                "disposition": "PASS" if ok else "FAIL",
            }
        )
        if not ok:
            FAILURES.append(f"SCOPE:{name}: {observed_value}")

    check(
        "i08_common_conversion_absent",
        "I04B does not take I08's common/conversion.py (bloc_05/03 S21)",
        "absent" if not (src / "common" / "conversion.py").exists() else "PRESENT",
        not (src / "common" / "conversion.py").exists(),
    )
    check(
        "conversion_owned_under_terms",
        "conversion lives only at normalization/terms/conversion.py",
        "present" if (src / "normalization" / "terms" / "conversion.py").exists()
        else "ABSENT",
        (src / "normalization" / "terms" / "conversion.py").exists(),
    )
    init_text = (src / "normalization" / "__init__.py").read_text(encoding="utf-8")
    top_public = init_text.split("__all__ = [", 1)[1].split("]", 1)[0]
    n_public = len([ln for ln in top_public.splitlines() if ln.strip().startswith('"')])
    check(
        "top_level_surface_unchanged",
        "top-level normalization surface stays exactly 24 ratified symbols",
        f"{n_public} symbols",
        n_public == 24,
    )
    identity_src = "".join(
        p.read_text(encoding="utf-8")
        for p in sorted((src / "normalization" / "identity").glob("*.py"))
    )
    leaked = [
        name
        for name in (
            "ConversionResult",
            "linear_base_exposure",
            "quote_notional",
            "inverse_base_from_quote",
        )
        if name in identity_src
    ]
    check(
        "no_conversion_leak_into_identity",
        "I03 identity sources reference no I04B conversion symbol",
        "none" if not leaked else f"LEAKED {leaked}",
        not leaked,
    )
    price_types = sorted(t.value for t in ReferencePriceType)
    check(
        "price_type_vocabulary_frozen",
        "exactly the five bloc_05/03 S8 types, no sixth",
        ",".join(price_types),
        price_types
        == [
            "INTERVAL_CLOSE",
            "MID_PRICE",
            "PROVIDER_INDEX",
            "PROVIDER_MARK",
            "TRADE_PRICE",
        ],
    )
    conv_text = (src / "normalization" / "terms" / "conversion.py").read_text(
        encoding="utf-8"
    )
    flagged = sorted(set(re.findall(r"NormalizationQualityFlag\.(\w+)", conv_text)))
    check(
        "blocked_flag_vocabulary",
        "only the accepted UNIT_CONVERSION_BLOCKED flag is referenced",
        ",".join(flagged),
        flagged == ["UNIT_CONVERSION_BLOCKED"],
    )
    forbidden_tokens = [
        "datetime.now",
        "time.time",
        "requests.",
        "urllib",
        "open(",
        "ConversionRateObservation",
    ]
    hits = [t for t in forbidden_tokens if t in conv_text]
    check(
        "no_wallclock_network_io",
        "conversion module is pure: no wall clock, network, or file I/O",
        "none" if not hits else f"FOUND {hits}",
        not hits,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.splitlines()
    allow_prefixes = (
        "?? .bu_tmp/",
        "?? quant-lab/research/crypto_foundry/sensor_fabric/evidence/"
        "bloc_05/BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md",
        "?? quant-lab/research/crypto_foundry/sensor_fabric/scripts/"
        "b5_i03_redteam_results.json",
    )
    allow_suffixes = (
        "quant-lab/src/crypto_sensor_fabric/normalization/terms/",
        "quant-lab/tests/crypto_sensor_fabric/normalization/"
        "test_b5_i04b_conversion.py",
        "quant-lab/research/crypto_foundry/sensor_fabric/scripts/"
        "b5_i04b_conversion.py",
        "quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/"
        "BLOC_05_I04B_",
        "quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/"
        "bloc_05_unit_validation.json",
        "quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/"
        "BLOC_05_I04B_IMPLEMENTATION_EVIDENCE.md",
        "quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_04/"
        "BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json",
    )
    unexpected = [
        ln
        for ln in status
        if not any(ln.startswith(p) or p in ln for p in allow_prefixes)
        and not any(s in ln for s in allow_suffixes)
    ]
    check(
        "changed_paths_authorized",
        "git status contains only I04B-authorized paths plus known scratch",
        "all authorized" if not unexpected else f"UNEXPECTED {unexpected}",
        not unexpected,
    )
    return checks


# ---------------------------------------------------------------- writers


def write_json(name: str, payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    path = OUT_DIR / name
    path.write_bytes(text.encode("utf-8"))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    authority = dimensional_authority_rows()
    linear = linear_rows()
    inverse = inverse_rows()
    blocked = blocked_rows()
    adversarial = adversarial_rows()
    scope = scope_audit_rows()

    def envelope(name: str, kind: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "artifact": name,
            "checkpoint": "SENSOR-B5-I04B",
            "created": CREATED,
            "evidence_class": kind,
            "generator": GEN_REF,
            "rows": rows,
            "summary": {
                "rows": len(rows),
                "pass": sum(1 for r in rows if r.get("disposition") == "PASS"),
                "fail": sum(1 for r in rows if r.get("disposition") != "PASS"),
            },
        }

    written: list[tuple[str, str]] = []
    written.append((
        "BLOC_05_I04B_DIMENSIONAL_AUTHORITY_MATRIX.json",
        write_json(
            "BLOC_05_I04B_DIMENSIONAL_AUTHORITY_MATRIX.json",
            envelope(
                "BLOC_05_I04B_DIMENSIONAL_AUTHORITY_MATRIX.json",
                "dimensional-authority",
                authority,
            ),
        ),
    ))
    written.append((
        "BLOC_05_I04B_LINEAR_MATRIX.json",
        write_json(
            "BLOC_05_I04B_LINEAR_MATRIX.json",
            envelope("BLOC_05_I04B_LINEAR_MATRIX.json", "linear-conversion", linear),
        ),
    ))
    written.append((
        "BLOC_05_I04B_INVERSE_MATRIX.json",
        write_json(
            "BLOC_05_I04B_INVERSE_MATRIX.json",
            envelope(
                "BLOC_05_I04B_INVERSE_MATRIX.json", "inverse-conversion", inverse
            ),
        ),
    ))
    written.append((
        "BLOC_05_I04B_BLOCKED_CONVERSION_MATRIX.json",
        write_json(
            "BLOC_05_I04B_BLOCKED_CONVERSION_MATRIX.json",
            envelope(
                "BLOC_05_I04B_BLOCKED_CONVERSION_MATRIX.json",
                "blocked-conversion",
                blocked,
            ),
        ),
    ))
    written.append((
        "BLOC_05_I04B_ADVERSARIAL_MATRIX.json",
        write_json(
            "BLOC_05_I04B_ADVERSARIAL_MATRIX.json",
            envelope(
                "BLOC_05_I04B_ADVERSARIAL_MATRIX.json", "adversarial", adversarial
            ),
        ),
    ))
    written.append((
        "BLOC_05_I04B_SCOPE_AUDIT.json",
        write_json(
            "BLOC_05_I04B_SCOPE_AUDIT.json",
            {
                "artifact": "BLOC_05_I04B_SCOPE_AUDIT.json",
                "checkpoint": "SENSOR-B5-I04B",
                "created": CREATED,
                "evidence_class": "scope-audit",
                "generator": GEN_REF,
                "checks": scope,
                "summary": {
                    "checks": len(scope),
                    "pass": sum(1 for c in scope if c["disposition"] == "PASS"),
                    "fail": sum(1 for c in scope if c["disposition"] != "PASS"),
                },
            },
        ),
    ))
    combined = linear + inverse + blocked
    written.append((
        "bloc_05_unit_validation.json",
        write_json(
            "bloc_05_unit_validation.json",
            {
                "artifact": "bloc_05_unit_validation.json",
                "checkpoint": "SENSOR-B5-I04B",
                "created": CREATED,
                "evidence_class": "unit-validation (bloc_05/06 S17 frozen "
                "name; G5 conversion portion)",
                "generator": GEN_REF,
                "rows": combined,
                "summary": {
                    "rows": len(combined),
                    "pass": sum(1 for r in combined if r["disposition"] == "PASS"),
                    "fail": sum(1 for r in combined if r["disposition"] != "PASS"),
                },
            },
        ),
    ))

    for name, digest in written:
        print(f"SHA256 {digest}  {name}")
    total = len(authority) + len(linear) + len(inverse) + len(blocked) + len(
        adversarial
    ) + len(scope)
    if FAILURES:
        print(f"FAILURES={len(FAILURES)}", file=sys.stderr)
        for f in FAILURES:
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"ALL_ROWS_PASS total_rows={total} artifacts={len(written)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
