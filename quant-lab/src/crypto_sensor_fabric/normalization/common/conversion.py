"""SENSOR-B5-I08E1 - stablecoin/fiat + cross-currency conversion (bloc_05/03 S9/S10).

The I08 conversion surface: deterministic, fail-closed Decimal arithmetic
that derives an OPTIONAL USD (or cross-asset) equivalent from a preserved
native quote notional, using only caller-supplied PIT rate evidence.

Frozen laws encoded here:

* **S9 native truth** -- ``native_value``/``native_unit`` are preserved
  verbatim on every result; the USD equivalent is an optional derived field
  that never overwrites them.  ``USDT``, ``USDC`` and ``USD`` are distinct
  (S22 inv.3): there is NO permanent ``1 USDT = 1 USD`` -- without a
  PIT-safe rate observation the derived value is NULL with the frozen
  blocking flag ``STABLECOIN_CONVERSION_UNAVAILABLE``, never a defaulted 1:1
  (06 §12 depeg fixture: 1000 USDT at 0.97 stays 1000 USDT native, becomes
  970 USD under the registered PIT conversion).
* **S9 rate evidence** -- ``ConversionRateObservation`` carries exactly the
  frozen field set (from_asset, into_asset, rate, effective_at,
  market_available_at, source, methodology, quality); all eight are
  required.  The rate must be positive and finite (same domain law as I04B
  reference prices); floats are refused at the boundary (S3.2).
* **S9/06 §12 replay law** -- a rate may be consumed only when both its
  ``effective_at`` and ``market_available_at`` fall at or before the
  caller-supplied knowledge cutoff.  A replay at a time before the conversion
  observation exists cannot use the later depeg value; never a future rate
  while normalizing old records (S10).
* **S9 no substitution** -- the observation's ``from_asset`` must equal the
  native unit and ``into_asset`` must be USD.  A USDT request answered by a
  USDC leg is refused (blocked), never silently redirected (the S8 "no
  silent substitution" principle applied to rate legs).
* **S10 cross-currency hierarchy** -- ``cross_convert_via_usd`` implements
  tier 3, the documented derived cross through USD: BOTH legs must be
  PIT-valid at the cutoff or the answer is tier 4, no conversion (NULL +
  flag).  Tiers 1/2 (direct venue / independent feed) are caller evidence
  slots; tier selection beyond the mechanical PIT check is I09/provider
  evidence territory and is NOT fabricated here.
* **S14/S22 inv.5** -- NULL is not zero: a verified economic 0 converts to
  0; an unavailable conversion is ``None``.  The two are structurally
  distinguishable in the result model.
* **S17/S22 inv.7** -- every derived value carries machine-readable
  conversion lineage (a rate-observation reference) and an explicit
  methodology version; a blocked result claims NO consumed inputs.

Ownership: I08's ``normalization/common/conversion.py`` (bloc_05/03 §21).
NOT I04B's ``normalization/terms/conversion.py`` (linear/inverse contract
primitives -- operator-accepted, untouched, and never re-implemented here;
a CONTRACTS-denominated request is refused with ``ValueError`` because
contract-multiplier conversion belongs to that I04B surface).

Offline: no network, no wall clock -- every cutoff is caller-supplied.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import (
    AfterValidator,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from ..enums import BLOCKING_QUALITY_FLAGS, NormalizationQualityFlag
from ..identity.models import _reject_blank, _require_unpadded
from ..models import NormalizationModelBase
from .numeric import PrecisionRecord
from .units import CanonicalQuantityUnit

__all__ = [
    "METHODOLOGY_VERSION",
    "ConversionRateObservation",
    "CrossCurrencyResult",
    "StablecoinConversionResult",
    "convert_stablecoin_to_usd",
    "cross_convert_via_usd",
]

#: Explicit methodology attribution for every I08 derived value
#: (S22 inv.7; same attribution pattern as I04B's METHODOLOGY_VERSION).
METHODOLOGY_VERSION = "B5_I08_UNITS_V1"

_BLOCK = NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE

_OpaqueToken = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"\S"),
    AfterValidator(_reject_blank),
    AfterValidator(_require_unpadded),
]

#: Units whose USD equivalent this surface may derive (S9: quote notional).
_USD_CONVERTIBLE = frozenset(
    {
        CanonicalQuantityUnit.USD,
        CanonicalQuantityUnit.USDT,
        CanonicalQuantityUnit.USDC,
        CanonicalQuantityUnit.OTHER_QUOTE,
    }
)

#: A native-denominated quantity that is not a quote notional: contract
#: conversion is I04B's linear/inverse surface, not this one.
_CONTRACT_UNITS = frozenset(
    {
        CanonicalQuantityUnit.CONTRACTS,
        CanonicalQuantityUnit.BASE_ASSET,
        CanonicalQuantityUnit.QUOTE_ASSET,
        CanonicalQuantityUnit.SETTLEMENT_ASSET,
    }
)


def _require_utc_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware UTC (bloc_05/02 §18)")


def _require_finite_rate(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("rate must be finite (bloc_05/03 §9)")
    if value <= 0:
        raise ValueError("rate must be positive (bloc_05/03 §9)")
    return value


def _rate_ref(rate: "ConversionRateObservation") -> str:
    return (
        "rate_observation_ref="
        f"{rate.from_asset}->{rate.into_asset}"
        f"@{rate.effective_at.isoformat()}"
        f"#{rate.source}"
    )


def _leg_is_pit_valid(rate: "ConversionRateObservation", cutoff: datetime) -> bool:
    return rate.effective_at <= cutoff and rate.market_available_at <= cutoff


def _leg_matches(rate: "ConversionRateObservation", from_unit: str) -> bool:
    return rate.from_asset == from_unit and rate.into_asset == "USD"


class ConversionRateObservation(NormalizationModelBase):
    """PIT-safe stablecoin/fiat rate observation (bloc_05/03 §9).

    The exact frozen §9 field set -- all eight fields REQUIRED, because the
    frozen contract lists them as what a ``ConversionRateObservation`` IS;
    an observation missing its availability clock could not be replayed
    safely and one missing its methodology could not be reconstructed.

    Immutable (``frozen=True``): rate evidence is evidence; changing it
    means publishing a new observation, not editing history.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    from_asset: _OpaqueToken
    into_asset: _OpaqueToken
    rate: Decimal
    effective_at: datetime
    market_available_at: datetime
    source: _OpaqueToken
    methodology: _OpaqueToken
    quality: _OpaqueToken

    @field_validator("rate", mode="before")
    @classmethod
    def _refuse_float_and_domain(cls, value: object) -> object:
        """S3.2: the boundary is Decimal; S9: positive and finite.

        ``mode="before"`` so a float never enters silently (pydantic would
        otherwise coerce 0.97 into a Decimal with binary noise -- exactly
        the fake precision §3.3 forbids).
        """
        if isinstance(value, float):
            raise ValueError("rate must be a Decimal, not a float (bloc_05/03 §3.2)")
        if isinstance(value, Decimal):
            _require_finite_rate(value)
        return value

    @model_validator(mode="after")
    def _clocks_utc_and_rate_domain(self) -> ConversionRateObservation:
        _require_utc_aware(self.effective_at, "effective_at")
        _require_utc_aware(self.market_available_at, "market_available_at")
        # Domain re-checked after coercion: a string "NaN"/"0" reaches the
        # model as a Decimal, and the before-hook above only sees raw input.
        _require_finite_rate(self.rate)
        return self


class StablecoinConversionResult(NormalizationModelBase):
    """Native-preserving optional USD equivalent (bloc_05/03 §9/S17/S22).

    Impossible combinations fail validation, mirroring the I04B result laws:

    * ``usd_equivalent is None`` ALWAYS carries the frozen blocking flag
      and claims no conversion inputs (NULL, never zero -- S22 inv.5);
    * a derived value carries lineage + methodology and NO blocking flag;
    * ``native_value``/``native_unit`` survive on both paths (S22 inv.1).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    native_value: Decimal
    native_unit: CanonicalQuantityUnit
    usd_equivalent: Decimal | None
    quality_flags: tuple[NormalizationQualityFlag, ...] = ()
    conversion_inputs: tuple[str, ...] = ()
    methodology_version: str
    precision: PrecisionRecord | None = None

    @model_validator(mode="after")
    def _result_laws(self) -> StablecoinConversionResult:
        flags = set(self.quality_flags)
        if len(flags) != len(self.quality_flags):
            raise ValueError("quality_flags contains duplicates")
        if self.usd_equivalent is None:
            if _BLOCK not in flags:
                raise ValueError(
                    "a NULL usd_equivalent must carry "
                    "STABLECOIN_CONVERSION_UNAVAILABLE (bloc_05/03 §9)"
                )
            if flags - {_BLOCK}:
                raise ValueError(
                    "a blocked stablecoin conversion carries exactly the "
                    "one frozen blocking flag"
                )
            if self.conversion_inputs:
                raise ValueError(
                    "a blocked result must not claim consumed conversion inputs"
                )
            return self
        if not self.usd_equivalent.is_finite():
            raise ValueError("usd_equivalent must be finite when present")
        if flags & set(BLOCKING_QUALITY_FLAGS):
            raise ValueError(
                "a derived value must not carry a blocking quality flag (S17)"
            )
        if not self.conversion_inputs:
            raise ValueError(
                "a derived value requires conversion input lineage (S17, S22 inv.7)"
            )
        if self.methodology_version != METHODOLOGY_VERSION:
            raise ValueError("a derived value requires the I08 methodology version")
        return self


class CrossCurrencyResult(NormalizationModelBase):
    """S10 tier-3 derived cross through USD, native preserved (S10/S14/S22).

    Same fail-closed shape as :class:`StablecoinConversionResult`, with the
    target asset instead of the implicit USD: ``derived_value is None`` is
    tier 4 (no conversion), always flagged, never zero, never a guess.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    native_value: Decimal
    native_unit: CanonicalQuantityUnit
    derived_asset: _OpaqueToken
    derived_value: Decimal | None
    quality_flags: tuple[NormalizationQualityFlag, ...] = ()
    conversion_inputs: tuple[str, ...] = ()
    methodology_version: str

    @model_validator(mode="after")
    def _result_laws(self) -> CrossCurrencyResult:
        flags = set(self.quality_flags)
        if self.derived_value is None:
            if flags != {_BLOCK}:
                raise ValueError(
                    "a NULL derived value must carry exactly "
                    "STABLECOIN_CONVERSION_UNAVAILABLE (bloc_05/03 §10 tier 4)"
                )
            if self.conversion_inputs:
                raise ValueError(
                    "a blocked cross-conversion must not claim consumed inputs"
                )
            return self
        if not self.derived_value.is_finite():
            raise ValueError("derived_value must be finite when present")
        if flags & set(BLOCKING_QUALITY_FLAGS):
            raise ValueError("a derived cross value must not be flagged blocked")
        if not self.conversion_inputs:
            raise ValueError(
                "a derived cross value requires conversion input lineage (S17)"
            )
        return self


def convert_stablecoin_to_usd(
    native_value: Decimal,
    native_unit: CanonicalQuantityUnit,
    rate: ConversionRateObservation | None,
    cutoff: datetime,
) -> StablecoinConversionResult:
    """Derive the optional USD equivalent of a quote notional (bloc_05/03 §9).

    Fail-closed, in order:

    1. contract-denominated natives (CONTRACTS/BASE/QUOTE/SETTLEMENT) are
       refused with ``ValueError`` -- that is I04B's contract-multiplier
       surface, and answering here would bypass its dimensional authority;
    2. non-finite native input is refused (no lawful representation);
    3. cutoff must be UTC-aware;
    4. no rate observation -> NULL + blocking flag (S9: no permanent 1:1);
    5. wrong leg direction (from/into mismatch) -> NULL + blocking flag
       (no silent substitution);
    6. either clock after the cutoff -> NULL + blocking flag (S10/06 §12
       replay law: a replay before the observation exists cannot use it);
    7. otherwise exact ``native_value * rate`` with lineage + methodology.

    ``native_unit`` unchanged on every path; inputs never mutated.
    """
    if native_unit in _CONTRACT_UNITS:
        raise ValueError(
            f"native_unit={native_unit.value} is contract-denominated; "
            "contract-multiplier conversion is the I04B terms surface "
            "(bloc_05/03 §6/§7/§8), not stablecoin conversion (§9)"
        )
    if native_unit not in _USD_CONVERTIBLE:  # pragma: no cover - defensive
        raise ValueError(f"native_unit={native_unit.value} is not quote notional")
    if not native_value.is_finite():
        raise ValueError("native_value must be finite (bloc_05/03 §3.2)")
    _require_utc_aware(cutoff, "cutoff")

    def _blocked() -> StablecoinConversionResult:
        return StablecoinConversionResult(
            native_value=native_value,
            native_unit=native_unit,
            usd_equivalent=None,
            quality_flags=(_BLOCK,),
            conversion_inputs=(),
            methodology_version=METHODOLOGY_VERSION,
        )

    if rate is None:
        return _blocked()  # S9: absent evidence, not a defaulted 1:1
    if not _leg_matches(rate, native_unit.value):
        return _blocked()  # no silent substitution between legs
    if not _leg_is_pit_valid(rate, cutoff):
        return _blocked()  # S10: never a future/unavailable rate
    if native_unit is CanonicalQuantityUnit.USD:
        # USD->USD needs no observation: identity, not an assumption.
        return StablecoinConversionResult(
            native_value=native_value,
            native_unit=native_unit,
            usd_equivalent=native_value,
            quality_flags=(),
            conversion_inputs=("usd_native_identity",),
            methodology_version=METHODOLOGY_VERSION,
        )
    derived = native_value * rate.rate
    return StablecoinConversionResult(
        native_value=native_value,
        native_unit=native_unit,
        usd_equivalent=derived,
        quality_flags=(),
        conversion_inputs=(_rate_ref(rate),),
        methodology_version=METHODOLOGY_VERSION,
    )


def cross_convert_via_usd(
    native_value: Decimal,
    native_unit: CanonicalQuantityUnit,
    into_asset: str,
    rate_from: ConversionRateObservation | None,
    rate_into: ConversionRateObservation | None,
    cutoff: datetime,
) -> CrossCurrencyResult:
    """S10 tier 3: derived cross through USD when BOTH legs are PIT-valid.

    ``native --rate_from--> USD --rate_into--> into_asset`` with exact
    Decimal arithmetic (multiply by the first leg, divide by the second).
    Either leg absent, direction-mismatched or not yet effective/available
    at ``cutoff`` -> tier 4: NULL + blocking flag, no consumed inputs
    (S10's "no conversion" is a lawful answer, never a fabricated rate).

    Same contract-denominated refusal as the single-leg path (I04B owns
    contract units); ``into_asset`` is an opaque token checked only for
    well-formedness -- resolving it against the asset registry is I02/I09
    territory and is deliberately not guessed here.
    """
    if native_unit in _CONTRACT_UNITS:
        raise ValueError(
            f"native_unit={native_unit.value} is contract-denominated; "
            "use the I04B terms surface (bloc_05/03 §6-§8)"
        )
    if native_unit not in _USD_CONVERTIBLE:  # pragma: no cover - defensive
        raise ValueError(f"native_unit={native_unit.value} is not quote notional")
    if not native_value.is_finite():
        raise ValueError("native_value must be finite (bloc_05/03 §3.2)")
    _require_utc_aware(cutoff, "cutoff")
    if not into_asset.strip():
        raise ValueError("into_asset must not be blank")

    def _blocked() -> CrossCurrencyResult:
        return CrossCurrencyResult(
            native_value=native_value,
            native_unit=native_unit,
            derived_asset=into_asset,
            derived_value=None,
            quality_flags=(_BLOCK,),
            conversion_inputs=(),
            methodology_version=METHODOLOGY_VERSION,
        )

    if rate_from is None or rate_into is None:
        return _blocked()  # tier 4: a missing leg is not a guessable leg
    if not _leg_matches(rate_from, native_unit.value):
        return _blocked()
    if not _leg_matches(rate_into, into_asset):
        return _blocked()
    if not _leg_is_pit_valid(rate_from, cutoff):
        return _blocked()
    if not _leg_is_pit_valid(rate_into, cutoff):
        return _blocked()
    usd = native_value * rate_from.rate
    derived = usd / rate_into.rate
    return CrossCurrencyResult(
        native_value=native_value,
        native_unit=native_unit,
        derived_asset=into_asset,
        derived_value=derived,
        quality_flags=(),
        conversion_inputs=(_rate_ref(rate_from), _rate_ref(rate_into)),
        methodology_version=METHODOLOGY_VERSION,
    )
