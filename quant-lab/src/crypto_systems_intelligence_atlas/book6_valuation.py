"""Book 6 valuation — the Book 5 → Book 6 seam and purpose-specific price authority.

Book 5 remains frozen. Book 6 may produce a valuation product that REFERENCES
Book 5 native quantities, and may NEVER write a numeraire, a price, or a
common-value scalar back into a Book 5 canonical record (ratified plan v0.2 §11,
§18; Book 5 plan v0.3 §4 — ``BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE``
remains a Book 5 invariant).

Ratified D6M-4 = A: there is NO universal authoritative price-source class.

    PRICE_AUTHORITY = PURPOSE x SUBJECT x VALID_TIME x METHODOLOGY

Admissibility is therefore checked per valuation purpose against the subject and
the price class, not by consulting one global "the" price source. Divergence
between price classes is preserved, never averaged: a redemption value, a market
observation, an oracle mark, a venue index and a NAV are different measurements,
and manufacturing a consensus price from them would invent authority.

Sensor retains market-state mechanics; no D8 decision is implemented here.

Book 6 Hardening R1 closes two authority gaps here:

- **R1-D2** ``PriceObservation.source_ref`` was a bare string, so
  ``source_ref="fake:oracle"`` authorized a collateral valuation. A ``source_ref``
  is an attribution label, not epistemic evidence. ``source_claim_refs`` is now
  REQUIRED and is resolved through the Book 2 provenance adapter at valuation
  authority time, so an unattributed, unknown, decayed or detached price carries
  no authority.
- **R1-D3** ``ValuationObservation.is_stale`` existed but the engine never
  consulted it, so a month-old price authorized a *current* valuation. The
  authority boundary is now split into ``authorize_current_valuation(...)``,
  which takes an explicit ``as_of`` and refuses a stale price, and
  ``validate_historical_valuation(...)``, which preserves a statement that was
  valid at its own recorded valid time. ``CURRENT UNAVAILABLE`` is not
  ``HISTORICALLY INVALID``, and there is no hidden wall clock.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import ConfigDict, Field, model_validator

from .book6_frozen import Book6FrozenModel

from .book6_grammar import ObservationStatus


class ValuationError(ValueError):
    """A valuation observation violates the ratified seam or price doctrine."""


class ValuationPurpose(str, Enum):
    """Why a value is being struck. Purpose selects the admissible price class."""

    REDEMPTION_ACCOUNTING = "REDEMPTION_ACCOUNTING"
    MARKET_VALUATION = "MARKET_VALUATION"
    PROTOCOL_COLLATERAL_MARK = "PROTOCOL_COLLATERAL_MARK"
    VENUE_MARGIN_MARK = "VENUE_MARGIN_MARK"
    ASSET_NAV = "ASSET_NAV"
    POSITION_VALUATION = "POSITION_VALUATION"
    WRAPPED_ASSET_BASIS = "WRAPPED_ASSET_BASIS"


class PriceObservationClass(str, Enum):
    """Price observation classes. None is universally authoritative."""

    OFFICIAL_REDEMPTION_VALUE = "OFFICIAL_REDEMPTION_VALUE"
    MARKET_OBSERVATION = "MARKET_OBSERVATION"
    ORACLE_MARK = "ORACLE_MARK"
    VENUE_INDEX = "VENUE_INDEX"
    ISSUER_NAV = "ISSUER_NAV"
    UNDERLYING_REFERENCE_PRICE = "UNDERLYING_REFERENCE_PRICE"


#: Purpose -> admissible price classes (D6M-4 = A). This table IS the
#: purpose-specific authority: no entry names a global winner, and a purpose
#: absent from this mapping admits nothing.
PRICE_AUTHORITY_MATRIX: Final[dict[ValuationPurpose, frozenset[PriceObservationClass]]] = {
    ValuationPurpose.REDEMPTION_ACCOUNTING: frozenset(
        {PriceObservationClass.OFFICIAL_REDEMPTION_VALUE}
    ),
    ValuationPurpose.MARKET_VALUATION: frozenset(
        {PriceObservationClass.MARKET_OBSERVATION}
    ),
    ValuationPurpose.PROTOCOL_COLLATERAL_MARK: frozenset(
        {
            PriceObservationClass.ORACLE_MARK,
            PriceObservationClass.MARKET_OBSERVATION,
        }
    ),
    ValuationPurpose.VENUE_MARGIN_MARK: frozenset(
        {
            PriceObservationClass.VENUE_INDEX,
            PriceObservationClass.MARKET_OBSERVATION,
        }
    ),
    ValuationPurpose.ASSET_NAV: frozenset(
        {
            PriceObservationClass.ISSUER_NAV,
            PriceObservationClass.OFFICIAL_REDEMPTION_VALUE,
        }
    ),
    ValuationPurpose.POSITION_VALUATION: frozenset(
        {
            PriceObservationClass.MARKET_OBSERVATION,
            PriceObservationClass.ISSUER_NAV,
        }
    ),
    ValuationPurpose.WRAPPED_ASSET_BASIS: frozenset(
        {
            PriceObservationClass.UNDERLYING_REFERENCE_PRICE,
            PriceObservationClass.MARKET_OBSERVATION,
            PriceObservationClass.OFFICIAL_REDEMPTION_VALUE,
        }
    ),
}


class PriceObservation(Book6FrozenModel):
    """A cited price observation with explicit source class and timestamp.

    R1-D2: ``source_claim_refs`` is REQUIRED. ``source_ref`` names where a
    price came from and is deliberately NOT epistemic evidence — a string like
    ``"fake:oracle"`` is an attribution, not a Book 2 claim. Only the cited
    Book 2 claims, resolved live through ``Book6Provenance``, give the price
    authority.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    price_observation_id: str = Field(min_length=1)
    price_class: PriceObservationClass
    source_ref: str = Field(min_length=1)
    source_claim_refs: tuple[str, ...] = Field(min_length=1)
    price: float = Field(gt=0.0)
    valid_time: datetime
    observed_at: datetime
    coverage: float = Field(ge=0.0, le=1.0)


class ValuationObservation(Book6FrozenModel):
    """A Book 6 valuation product over a Book 5 native quantity (D6M-4 = A).

    ``numeraire`` is REQUIRED with no default and no implicit USD. There is no
    common-value calculation without an explicit, cited price observation
    (ratified plan v0.2 §16).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    valuation_id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    native_quantity: float
    native_unit: str = Field(min_length=1)
    numeraire: str = Field(min_length=1)
    purpose: ValuationPurpose
    price: PriceObservation
    conversion_methodology_ref: str = Field(min_length=1)
    valid_time: datetime
    observed_at: datetime
    coverage: float = Field(ge=0.0, le=1.0)
    staleness_bound_seconds: int = Field(gt=0)
    status: ObservationStatus = ObservationStatus.OBSERVED

    @model_validator(mode="after")
    def _check_price_admissibility(self) -> "ValuationObservation":
        admissible = PRICE_AUTHORITY_MATRIX[self.purpose]
        if self.price.price_class not in admissible:
            raise ValuationError(
                f"price class {self.price.price_class.value} is not admissible "
                f"for valuation purpose {self.purpose.value}; authority is "
                f"purpose-specific, and no universal price-source class exists"
            )
        return self

    @property
    def is_stale(self) -> bool:
        """Whether the price was stale at this valuation's own observed time."""

        return self.is_stale_at(self.observed_at)

    def is_stale_at(self, as_of: datetime) -> bool:
        """Whether the cited price is older than the staleness bound at ``as_of``.

        The evaluation time is always explicit — passed in, never read from a
        hidden wall clock — so a replay at a historical instant is reproducible.
        """

        age = (as_of - self.price.observed_at).total_seconds()
        return age > self.staleness_bound_seconds

    def is_currently_fresh(self, as_of: datetime) -> bool:
        """Current-value availability at an explicit instant.

        A stale or absent CURRENT price makes a *current* valuation unavailable.
        It never invalidates a valuation whose own valid time is historical: the
        historical statement remains historical (ratified plan v0.2 §11).
        """

        return not self.is_stale_at(as_of)


class Book5WriteBackRefusal(Book6FrozenModel):
    """Explicit refusal token for the Book 5 seam (documentation + test surface).

    Book 5 is frozen. There is deliberately NO Book 6 API that writes a numeraire,
    a price or a common-value scalar into a Book 5 record; this object records
    the refusal reason for evidence and tests.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_kind: str = "BOOK5_CANONICAL_RECORD"
    refused_fields: tuple[str, ...] = ("numeraire", "price", "common_value_scalar")
    reason: str = (
        "Book 5 owns capital topology and same-unit algebra; cross-asset "
        "valuation is a Book 6 product and never writes back "
        "(BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE)"
    )


#: Canonical invariants asserted by the accepted implementation.
PRICE_AUTHORITY_IS_PURPOSE_SPECIFIC: Final[bool] = True
NO_GLOBAL_PRICE_SOURCE_CLASS: Final[bool] = True
BOOK5_WRITE_BACK_IS_REFUSED: Final[bool] = True


def check_price_divergence_is_preserved(
    observations: tuple[PriceObservation, ...],
) -> tuple[tuple[str, PriceObservationClass], ...]:
    """Return every (subject, price class) pair present, preserving divergence.

    Divergent price classes are returned side by side and NEVER merged. A caller
    that wants one number has no ratified methodology to do it with.
    """

    return tuple((obs.source_ref, obs.price_class) for obs in observations)


__all__ = [
    "BOOK5_WRITE_BACK_IS_REFUSED",
    "Book5WriteBackRefusal",
    "check_price_divergence_is_preserved",
    "NO_GLOBAL_PRICE_SOURCE_CLASS",
    "PRICE_AUTHORITY_IS_PURPOSE_SPECIFIC",
    "PRICE_AUTHORITY_MATRIX",
    "PriceObservation",
    "PriceObservationClass",
    "ValuationError",
    "ValuationObservation",
    "ValuationPurpose",
]
