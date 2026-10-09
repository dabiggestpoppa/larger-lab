"""SENSOR-B5-I04B - pure linear/inverse contract conversion primitives.

The I04B conversion surface: dimensionally-guarded, fail-closed, deterministic
Decimal arithmetic over an accepted :class:`~crypto_sensor_fabric.normalization.terms.snapshot.ContractTermsSnapshot`
plus caller-supplied reference-price evidence.

Economic-truth invariant (I04B directive S0.2)::

    Verified Identity -> PIT-Valid Terms -> Dimensional Compatibility ->
    Permitted Formula -> Eligible Price Evidence -> Versioned Lineage ->
    Derived Value

Any missing link yields ``normalized_value = None`` with
``UNIT_CONVERSION_BLOCKED`` (bloc_05/03 S8, G5, G9).  Native inputs are
never mutated; blocked results never claim consumed inputs or price (Book 4.3).

Dimensional authority (Book 2.1, clause-backed matrix generated into
``evidence/bloc_05/BLOC_05_I04B_DIMENSIONAL_AUTHORITY_MATRIX.json``):
every dimension check is a token EQUALITY against the contract's own
recorded terms -- count denomination ``contracts_unit == multiplier_unit``,
price dimension ``(price_unit, quantity_unit)``, outputs
``quantity_unit`` (S7 base exposure) or ``price_unit`` (S8 quote/face).
Multiplier meaning is never inferred from its number and never assumed to
be 1-contract-1-base (bloc_05/03 S7 explicit).

Reference-price truth (directive Book 3): the five frozen S8 types only;
no substitution ladder; observation time alone never proves availability --
the frozen ``market_available_at`` clock (bloc_05/02 S4: "when could a
market participant using the documented public feed have known this?") must
fall at or before the requested knowledge cutoff.  Caller-supplied PIT price
precondition: the observation carries independently established availability
plus source and evidence references; the engine verifies it mechanically.

Ownership: I04B-specific module beside the I04A terms package.  NOT I08's
``normalization/common/conversion.py`` (bloc_05/03 S21), NOT I03 identity,
NOT I05 time, NOT a T1 envelope (Book 4.2: I04-owned pure intermediate
result; the top-level normalization surface stays the ratified 24 symbols).

Plan citations use the compact S<n> form for bloc_05/0<n> sections.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Mapping

from pydantic import ConfigDict, Field, ValidationError, model_validator

from ..enums import BLOCKING_QUALITY_FLAGS, NormalizationQualityFlag, PayoffType
from ..identity.models import SemanticToken, UtcDatetime
from ..models import NormalizationModelBase, OpaqueIdentifier, RegistryVersion
from .snapshot import ContractTermsSnapshot

__all__ = [
    "METHODOLOGY_VERSION",
    "ConversionResult",
    "ReferencePriceEvidence",
    "ReferencePriceType",
    "contracts_to_quote_notional",
    "inverse_base_from_quote",
    "inverse_quote_face",
    "linear_base_exposure",
    "quote_notional",
]

#: Explicit methodology attribution for every result (bloc_05/03 S22 inv.7,
#: G5 "every derived amount has methodology + input lineage").
METHODOLOGY_VERSION = "B5_I04B_CONVERSION_V1"

_BLOCK = NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED


class ReferencePriceType(StrEnum):
    """The five frozen reference-price semantics (bloc_05/03 S8).

    Exact frozen vocabulary; "no silent substitution between them" and no
    sixth type may ever appear (directive Book 3.1).
    """

    PROVIDER_MARK = "PROVIDER_MARK"
    PROVIDER_INDEX = "PROVIDER_INDEX"
    TRADE_PRICE = "TRADE_PRICE"
    MID_PRICE = "MID_PRICE"
    INTERVAL_CLOSE = "INTERVAL_CLOSE"


def _require_nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value


def _require_unique_members(values: tuple[str, ...]) -> tuple[str, ...]:
    if any(not v.strip() for v in values):
        raise ValueError("evidence references must be non-blank")
    if len(set(values)) != len(values):
        raise ValueError("evidence references must be duplicate-free")
    return values


def _require_price_domain(value: Decimal) -> Decimal:
    """Book 3.2: finite, economically valid domain (a reference price is a
    positive finite amount; zero would divide by zero, negatives are not a
    price in this contract)."""
    if not value.is_finite():
        raise ValueError("reference_price must be finite")
    if value <= 0:
        raise ValueError("reference_price must be positive")
    return value


class ReferencePriceEvidence(NormalizationModelBase):
    """Caller-supplied PIT reference-price observation (directive Book 3).

    Carries the frozen S8 block (``reference_price``, ``reference_price_type``,
    ``reference_price_time``, ``reference_price_source``) plus the fields the
    mandated validations require, each at its frozen meaning: the S4 unit
    identity of the price dimension (bloc_05/03 S4 "unit identity must
    include asset"), the bloc_05/02 S4 ``market_available_at`` availability
    clock, and S17 lineage evidence references.  Immutable; the engine never
    fetches, derives, or substitutes a price.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_price: Decimal
    reference_price_type: ReferencePriceType
    reference_price_time: UtcDatetime
    reference_price_source: str
    market_available_at: UtcDatetime
    reference_price_unit: SemanticToken
    reference_price_base_unit: SemanticToken
    source_evidence_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _price_laws(self) -> ReferencePriceEvidence:
        _require_price_domain(self.reference_price)
        _require_nonblank(self.reference_price_source)
        _require_unique_members(self.source_evidence_refs)
        return self


class ConversionResult(NormalizationModelBase):
    """I04-owned pure conversion result (Book 4.2 intermediate result).

    Impossible combinations fail validation (bloc_05/06 S3 property laws):
    a NULL value is always flagged ``UNIT_CONVERSION_BLOCKED``; a blocked
    result never claims consumed inputs or price; a value always carries
    explicit unit, versions, methodology and lineage (G5/P13/P14) with no
    blocking flag (P08).  ``normalized_value is None`` is NULL, never zero
    (bloc_05/03 S22 inv.5).  ``native_quantity`` is finite-or-absent: a
    non-finite caller input (NaN/Infinity) has no lawful representation, so
    a blocked result declares its native quantity absent (None) rather than
    storing junk or inventing a number -- the caller's original input object
    is never mutated either way (P09).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    native_quantity: Decimal | None
    native_unit: SemanticToken
    normalized_value: Decimal | None
    output_unit: SemanticToken | None = None
    quality_flags: tuple[NormalizationQualityFlag, ...] = ()
    contract_instance_id: OpaqueIdentifier | None = None
    contract_terms_version: RegistryVersion | None = None
    methodology_version: str
    conversion_inputs: tuple[str, ...] = ()
    source_evidence_refs: tuple[str, ...] = ()
    reference_price: ReferencePriceEvidence | None = None

    @model_validator(mode="after")
    def _result_laws(self) -> ConversionResult:
        flags = set(self.quality_flags)
        flagged = _BLOCK in flags
        if self.normalized_value is None:
            if not flagged:
                raise ValueError(
                    "a NULL normalized_value must carry UNIT_CONVERSION_BLOCKED "
                    "(bloc_05/03 S8: blocked conversion = NULL + flag)"
                )
            if self.conversion_inputs:
                raise ValueError(
                    "a blocked result must not claim consumed conversion inputs"
                )
            if self.reference_price is not None:
                raise ValueError(
                    "a blocked result must not represent a price as consumed"
                )
            return self
        # value present: success laws
        if flags & set(BLOCKING_QUALITY_FLAGS):
            raise ValueError(
                "a derived value must not carry a blocking quality flag "
                "(Book 4.3 success invariants)"
            )
        if self.native_quantity is None:
            raise ValueError(
                "a derived value requires its preserved native quantity (P09)"
            )
        if self.output_unit is None:
            raise ValueError("a derived value requires an explicit output unit")
        if self.contract_instance_id is None or self.contract_terms_version is None:
            raise ValueError(
                "a derived value requires contract instance + terms version (P13/P14)"
            )
        if not self.methodology_version:
            raise ValueError("a derived value requires a methodology version")
        if not self.conversion_inputs:
            raise ValueError("a derived value requires conversion input lineage")
        if not self.source_evidence_refs:
            raise ValueError("a derived value requires source evidence references")
        return self


# ---------------------------------------------------------------- helpers


def _finite(value: Decimal) -> bool:
    return value.is_finite()


def _block(
    native_quantity: Decimal,
    native_unit: str,
    terms: ContractTermsSnapshot | None,
    output_unit: str | None = None,
) -> ConversionResult:
    """Typed refusal: NULL + UNIT_CONVERSION_BLOCKED, nothing consumed.

    A non-finite native input cannot be stored (pydantic ``finite_number``),
    so absence is declared as None instead of fabricating a value.
    """
    return ConversionResult(
        native_quantity=native_quantity if native_quantity.is_finite() else None,
        native_unit=native_unit,
        normalized_value=None,
        output_unit=output_unit,
        quality_flags=(_BLOCK,),
        contract_instance_id=terms.contract_instance_id if terms else None,
        contract_terms_version=terms.contract_terms_version if terms else None,
        methodology_version=METHODOLOGY_VERSION,
        conversion_inputs=(),
        source_evidence_refs=(),
        reference_price=None,
    )


def _multiplier_ref(terms: ContractTermsSnapshot) -> str:
    return (
        "contract_multiplier_ref="
        f"{terms.contract_instance_id}#{terms.contract_terms_version}"
    )


def _price_ref(price: ReferencePriceEvidence) -> str:
    return (
        "price_observation_ref="
        f"{price.reference_price_source}@{price.reference_price_time.isoformat()}"
    )


def _merge_refs(
    terms: ContractTermsSnapshot, price: ReferencePriceEvidence | None
) -> tuple[str, ...]:
    """Order-preserving, duplicate-free union of actual input evidence
    (A8 law: references are passed through, never synthesized)."""
    out: list[str] = []
    for ref in (*terms.source_evidence_refs, *((price.source_evidence_refs if price else ()))):
        if ref not in out:
            out.append(ref)
    return tuple(out)


def _family_ok(terms: ContractTermsSnapshot | None, family: PayoffType) -> bool:
    """Payoff-family isolation (Book 2.4, bloc_05/07 F5): the requested
    family must be exactly the recorded, structurally consistent one.
    QUANTO/UNKNOWN/SPOT and inconsistent flags are refused -- no universal
    formula exists."""
    if terms is None:
        return False
    if terms.quanto_flag or terms.payoff_type is PayoffType.QUANTO:
        return False
    if family is PayoffType.LINEAR:
        return terms.payoff_type is PayoffType.LINEAR and not terms.inverse_flag
    if family is PayoffType.INVERSE:
        return terms.payoff_type is PayoffType.INVERSE and terms.inverse_flag
    return False


def _validated_price(
    price: ReferencePriceEvidence | Mapping[str, Any] | None,
    terms: ContractTermsSnapshot | None,
    knowledge_cutoff: datetime,
    required_price_type: ReferencePriceType | None,
) -> ReferencePriceEvidence | None:
    """Book 3 validation chain: presence, model validity (numeric domain,
    UTC, source, provenance), availability under the cutoff, dimension
    compatibility with the contract's recorded terms, and required type
    (no silent substitution).  Returns None for any failure."""
    if price is None or terms is None:
        return None
    if not isinstance(knowledge_cutoff, datetime) or knowledge_cutoff.tzinfo is None:
        return None  # G9 fail-closed: availability vs an unprovable clock
    if isinstance(price, Mapping):
        try:
            evidence = ReferencePriceEvidence.model_validate(dict(price))
        except ValidationError:
            return None
    else:
        evidence = price
    if evidence.market_available_at > knowledge_cutoff:
        return None  # bloc_05/02 S4: not knowable by the cutoff
    if evidence.reference_price_time > knowledge_cutoff:
        return None  # observation after the cutoff cannot inform it
    if evidence.reference_price_unit != terms.price_unit:
        return None  # S4/S7 quote-side dimension mismatch
    if evidence.reference_price_base_unit != terms.quantity_unit:
        return None  # S4 base-side dimension mismatch
    if required_price_type is not None and evidence.reference_price_type is not required_price_type:
        return None  # S8: no silent substitution
    return evidence


def _success(
    *,
    native_quantity: Decimal,
    native_unit: str,
    value: Decimal,
    output_unit: str,
    terms: ContractTermsSnapshot,
    inputs: tuple[str, ...],
    price: ReferencePriceEvidence | None,
) -> ConversionResult:
    return ConversionResult(
        native_quantity=native_quantity,
        native_unit=native_unit,
        normalized_value=value,
        output_unit=output_unit,
        quality_flags=(),
        contract_instance_id=terms.contract_instance_id,
        contract_terms_version=terms.contract_terms_version,
        methodology_version=METHODOLOGY_VERSION,
        conversion_inputs=inputs,
        source_evidence_refs=_merge_refs(terms, price),
        reference_price=price,
    )


# ---------------------------------------------------------------- linear
# bloc_05/03 S7: base_exposure = contracts x base_per_contract;
# quote_notional = base_exposure x reference_price.


def linear_base_exposure(
    contracts: Decimal,
    contracts_unit: str,
    terms: ContractTermsSnapshot | None,
    output_unit: str | None = None,
) -> ConversionResult:
    """Contracts -> base exposure for a verified LINEAR contract (S7)."""
    if terms is None:
        return _block(contracts, contracts_unit, None)
    target = terms.quantity_unit
    if output_unit is not None and output_unit != target:
        return _block(contracts, contracts_unit, terms, target)  # LIN-R09
    if not _family_ok(terms, PayoffType.LINEAR):
        return _block(contracts, contracts_unit, terms, target)
    if not _finite(contracts) or not _finite(terms.contract_multiplier):
        return _block(contracts, contracts_unit, terms, target)
    if contracts_unit != terms.multiplier_unit:
        return _block(contracts, contracts_unit, terms, target)  # LIN-R01
    value = contracts * terms.contract_multiplier
    return _success(
        native_quantity=contracts,
        native_unit=contracts_unit,
        value=value,
        output_unit=target,
        terms=terms,
        inputs=(_multiplier_ref(terms),),
        price=None,
    )


def quote_notional(
    base_exposure: Decimal,
    base_unit: str,
    terms: ContractTermsSnapshot | None,
    price: ReferencePriceEvidence | Mapping[str, Any] | None,
    knowledge_cutoff: datetime,
    required_price_type: ReferencePriceType | None = None,
) -> ConversionResult:
    """Base exposure -> quote notional with an eligible PIT price (S7/S8)."""
    if terms is None:
        return _block(base_exposure, base_unit, None)
    target = terms.price_unit
    if not _family_ok(terms, PayoffType.LINEAR):
        return _block(base_exposure, base_unit, terms, target)
    if not _finite(base_exposure) or not _finite(terms.contract_multiplier):
        return _block(base_exposure, base_unit, terms, target)
    if base_unit != terms.quantity_unit:
        return _block(base_exposure, base_unit, terms, target)
    evidence = _validated_price(price, terms, knowledge_cutoff, required_price_type)
    if evidence is None:
        return _block(base_exposure, base_unit, terms, target)
    value = base_exposure * evidence.reference_price
    return _success(
        native_quantity=base_exposure,
        native_unit=base_unit,
        value=value,
        output_unit=target,
        terms=terms,
        inputs=(_multiplier_ref(terms), _price_ref(evidence)),
        price=evidence,
    )


def contracts_to_quote_notional(
    contracts: Decimal,
    contracts_unit: str,
    terms: ContractTermsSnapshot | None,
    price: ReferencePriceEvidence | Mapping[str, Any] | None,
    knowledge_cutoff: datetime,
    required_price_type: ReferencePriceType | None = None,
) -> ConversionResult:
    """Complete supported chain: contracts -> base -> quote notional
    (directive S2.2 operation 3); blocks atomically on any failed link."""
    base = linear_base_exposure(contracts, contracts_unit, terms)
    if base.normalized_value is None or terms is None:
        return _block(
            contracts,
            contracts_unit,
            terms,
            terms.price_unit if terms else None,
        )
    notional = quote_notional(
        base_exposure=base.normalized_value,
        base_unit=terms.quantity_unit,
        terms=terms,
        price=price,
        knowledge_cutoff=knowledge_cutoff,
        required_price_type=required_price_type,
    )
    if notional.normalized_value is None:
        return _block(contracts, contracts_unit, terms, terms.price_unit)
    return _success(
        native_quantity=contracts,
        native_unit=contracts_unit,
        value=notional.normalized_value,
        output_unit=terms.price_unit,
        terms=terms,
        inputs=(_multiplier_ref(terms), _price_ref(notional.reference_price)),  # type: ignore[arg-type]
        price=notional.reference_price,
    )


# ---------------------------------------------------------------- inverse
# bloc_05/03 S8 + directive Book 2.3: quote-denominated face, then
# base_equivalent = quote_face_notional / reference_price.


def inverse_quote_face(
    contracts: Decimal,
    contracts_unit: str,
    terms: ContractTermsSnapshot | None,
) -> ConversionResult:
    """Contracts -> quote-denominated contract face for a verified INVERSE
    contract; no price involved.  Face denomination is the contract's own
    quote unit (S8 inverse notional, F5)."""
    if terms is None:
        return _block(contracts, contracts_unit, None)
    target = terms.price_unit
    if not _family_ok(terms, PayoffType.INVERSE):
        return _block(contracts, contracts_unit, terms, target)
    if not _finite(contracts) or not _finite(terms.contract_multiplier):
        return _block(contracts, contracts_unit, terms, target)
    if contracts_unit != terms.multiplier_unit:
        return _block(contracts, contracts_unit, terms, target)
    value = contracts * terms.contract_multiplier
    return _success(
        native_quantity=contracts,
        native_unit=contracts_unit,
        value=value,
        output_unit=target,
        terms=terms,
        inputs=(_multiplier_ref(terms),),
        price=None,
    )


def inverse_base_from_quote(
    quote_face_notional: Decimal,
    quote_face_unit: str,
    terms: ContractTermsSnapshot | None,
    price: ReferencePriceEvidence | Mapping[str, Any] | None,
    knowledge_cutoff: datetime,
    required_price_type: ReferencePriceType | None = None,
) -> ConversionResult:
    """Verified quote face -> base equivalent: face / reference_price
    (Book 2.3 candidate relation, admitted only with every proof held:
    quote-face denomination, quote/base relationship, price dimension,
    INVERSE classification, PIT-valid terms, price evidence)."""
    if terms is None:
        return _block(quote_face_notional, quote_face_unit, None)
    target = terms.quantity_unit
    if not _family_ok(terms, PayoffType.INVERSE):
        return _block(quote_face_notional, quote_face_unit, terms, target)
    if not _finite(quote_face_notional) or not _finite(terms.contract_multiplier):
        return _block(quote_face_notional, quote_face_unit, terms, target)
    if quote_face_unit != terms.price_unit:
        return _block(quote_face_notional, quote_face_unit, terms, target)  # INV-13
    evidence = _validated_price(price, terms, knowledge_cutoff, required_price_type)
    if evidence is None:
        return _block(quote_face_notional, quote_face_unit, terms, target)
    value = quote_face_notional / evidence.reference_price
    return _success(
        native_quantity=quote_face_notional,
        native_unit=quote_face_unit,
        value=value,
        output_unit=target,
        terms=terms,
        inputs=(_multiplier_ref(terms), _price_ref(evidence)),
        price=evidence,
    )
