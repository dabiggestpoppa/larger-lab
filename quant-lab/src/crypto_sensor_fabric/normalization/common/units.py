"""SENSOR-B5-I08E1 - frozen canonical quantity vocabulary (bloc_05/03 S4).

The vocabulary layer of the common-units checkpoint: the 13 frozen minimum
units, and the law that **unit identity includes asset identity where
relevant** -- "1000 BASE_ASSET" without a BTC/ETH identity is incomplete
(bloc_05/03 S4 verbatim).

Three identity classes are kept deliberately distinct, because collapsing
any two of them would erase a frozen distinction:

* ASSET-IDENTITY-REQUIRED units (BASE_ASSET, QUOTE_ASSET, SETTLEMENT_ASSET)
  are incomplete without an ``asset_id`` -- the S4 hard example;
* SELF-IDENTIFYING units (USD, USDT, USDC) are their own identity, and a
  second asset identity beside them is a contradiction (S22 inv.3:
  stablecoin != USD by default -- the three never collapse, and neither do
  they acquire a subsidiary "asset");
* DIMENSIONLESS/CONTRACT units (CONTRACTS, COUNT, PERCENT, BPS,
  RATE_PER_INTERVAL, PRICE) declare no asset dimension here.  CONTRACTS is
  bound to its contract instance by I02/I04 terms, not by an asset id on
  the unit token; PRICE's unit-identity pairing is the I04B price-dimension
  law (``reference_price_unit``/``reference_price_base_unit``).

``OTHER_QUOTE`` is asset-required in effect: it exists precisely for a
quote asset outside the named set, so a bare OTHER_QUOTE with no asset
identity is as incomplete as a bare BASE_ASSET.

This module resolves nothing: no conversion, no registry lookup, no
provider behavior.  Conversion is ``common/conversion.py``; linear/inverse
contract primitives stay in the operator-accepted I04B
``normalization/terms/conversion.py`` and are never re-implemented here.
"""

from __future__ import annotations

from enum import Enum

from pydantic import ConfigDict, Field, model_validator

from ..models import NormalizationModelBase

__all__ = [
    "ASSET_IDENTITY_REQUIRED",
    "SELF_IDENTIFYING",
    "CanonicalQuantityUnit",
    "QuantityUnitIdentity",
]


class CanonicalQuantityUnit(str, Enum):
    """The frozen minimum quantity vocabulary (bloc_05/03 S4).

    Exact frozen set of 13 members; values equal member names.  Unit identity
    must include asset where relevant (S4), which is enforced by
    :class:`QuantityUnitIdentity`, not by this enum.

    Deliberately NOT the Bloc 4 ``SourceUnit*`` vocabulary: those describe
    what a provider payload physically declared (evidence about a source);
    these are canonical quantity kinds a normalized value may be expressed
    in.  Names never transfer semantics across the two (I07D1 S1.3 law).
    """

    CONTRACTS = "CONTRACTS"
    BASE_ASSET = "BASE_ASSET"
    QUOTE_ASSET = "QUOTE_ASSET"
    SETTLEMENT_ASSET = "SETTLEMENT_ASSET"
    USD = "USD"
    USDT = "USDT"
    USDC = "USDC"
    OTHER_QUOTE = "OTHER_QUOTE"
    PERCENT = "PERCENT"
    RATE_PER_INTERVAL = "RATE_PER_INTERVAL"
    BPS = "BPS"
    PRICE = "PRICE"
    COUNT = "COUNT"


#: Units whose identity is incomplete without an asset id (S4).
ASSET_IDENTITY_REQUIRED: frozenset[CanonicalQuantityUnit] = frozenset(
    {
        CanonicalQuantityUnit.BASE_ASSET,
        CanonicalQuantityUnit.QUOTE_ASSET,
        CanonicalQuantityUnit.SETTLEMENT_ASSET,
        CanonicalQuantityUnit.OTHER_QUOTE,
    }
)

#: Units that are their own identity; a second asset identity beside them is
#: a contradiction, never an enrichment (S22 inv.3).
SELF_IDENTIFYING: frozenset[CanonicalQuantityUnit] = frozenset(
    {
        CanonicalQuantityUnit.USD,
        CanonicalQuantityUnit.USDT,
        CanonicalQuantityUnit.USDC,
    }
)


class QuantityUnitIdentity(NormalizationModelBase):
    """A unit token with its asset identity, where relevant (bloc_05/03 S4).

    Fail-closed construction:

    * asset-required units refuse to exist without ``asset_id`` -- the
      "1000 BASE_ASSET" incompleteness rule made unrepresentable;
    * self-identifying units refuse a ``asset_id`` -- USD/BTC identity
      smuggling would blur stablecoin != USD (S22 inv.3);
    * dimensionless/contract units refuse a ``asset_id`` too -- inventing an
      asset dimension the frozen vocabulary does not declare is fabrication.

    ``asset_id`` is an opaque validated token, NOT a registry lookup: the
    canonical asset registry is I02-owned and this layer only checks
    well-formedness (the I01 opaque-identifier law).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    unit: CanonicalQuantityUnit
    asset_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _identity_laws(self) -> QuantityUnitIdentity:
        if self.unit in ASSET_IDENTITY_REQUIRED:
            if self.asset_id is None:
                raise ValueError(
                    f"unit={self.unit.value} requires asset identity "
                    "(bloc_05/03 S4: '1000 BASE_ASSET' without BTC/ETH "
                    "identity is incomplete)"
                )
        elif self.asset_id is not None:
            raise ValueError(
                f"unit={self.unit.value} is its own identity or dimensionless; "
                "an asset_id beside it is a contradiction "
                "(bloc_05/03 S4, S22 inv.3)"
            )
        return self
