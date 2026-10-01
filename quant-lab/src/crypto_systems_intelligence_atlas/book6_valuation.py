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
  which takes an explicit ``as_of`` and refuses a stale price, and the
  historical path, which preserves a statement that was valid at its own
  recorded valid time. ``CURRENT UNAVAILABLE`` is not
  ``HISTORICALLY INVALID``, and there is no hidden wall clock.
- **R2-D4** the historical path above shared ONE helper with the current path,
  so it revalidated the price's Book 2 claims with ``require_current=True``.
  A price claim valid when the valuation was observed and later STALE or
  SUPERSEDED retroactively erased the historical statement. The semantics are
  now split honestly: ``validate_recorded_historical_shape(...)`` proves
  RECORD SHAPE only and never consults Book 2, while
  ``historical_authority_status(...)`` reports that Book 2 authority replay is
  :data:`HISTORICAL_BOOK2_AUTHORITY_REPLAY`. A preserved record is not
  revalidated historical authority, and Book 6 does not claim otherwise.
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


#: R2-D4 capability ledger. Accepted Book 2 EXPOSES raw claim history
#: (``ClaimStore.history`` plus timestamped ``TransitionEvent``s), but its
#: epistemic predicate ``can_promote_to_graph`` requires the claim to BE the
#: canonical current record:
#:
#:     if claim_store.require(claim.claim_id) != claim: return False
#:
#: It is therefore CURRENT-ONLY BY DESIGN, and Book 2 offers no "was this claim
#: authoritative at valid_time T" query. Book 6 cannot re-derive that predicate
#: bitemporally without inventing a Book 2 feature and standing up a second
#: epistemic engine, so R2 records the capability as absent rather than faking
#: a historical PASS. This is an accepted capability limitation; only a
#: governance-authorized Book 2 amendment can change it.
HISTORICAL_BOOK2_AUTHORITY_REPLAY: Final[str] = "NOT_IMPLEMENTED"


class HistoricalAuthorityReport(Book6FrozenModel):
    """What can honestly be said about a historical valuation's authority.

    R2-D4. Two DIFFERENT claims are kept apart instead of being collapsed:

    ``record_shape_valid``
        PRESERVED HISTORICAL RECORD — provable offline from the record itself:
        explicit numeraire, cited price, purpose/class admissibility, resolvable
        methodology, and a price that was not already stale at its own
        ``observed_at``.

    ``current_claims_backed``
        CURRENT authority as of *now* — a separate, clearly-labelled fact.

    ``replay_available``
        Whether Book 2 can revalidate historical epistemic authority. It is
        ``False``: see :data:`HISTORICAL_BOOK2_AUTHORITY_REPLAY`.

    ``PRESERVED_HISTORICAL_RECORD`` is NOT ``REVALIDATED_HISTORICAL_AUTHORITY``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    valuation_id: str = Field(min_length=1)
    replay_capability: str = HISTORICAL_BOOK2_AUTHORITY_REPLAY
    replay_available: bool = False
    replay_unavailable_reason: str = Field(min_length=1)
    current_claims_backed: bool
    record_shape_valid: bool

    @model_validator(mode="after")
    def _check_no_false_replay_claim(self) -> "HistoricalAuthorityReport":
        """No report may claim what the kernel cannot deliver.

        Bound to the MODULE capability constant, not to this instance's field:
        while ``HISTORICAL_BOOK2_AUTHORITY_REPLAY`` is not ``"AVAILABLE"``, a
        forged report claiming ``replay_available=True`` is invalid data, full
        stop. A caller cannot launder the claim by asserting a capability the
        kernel does not ship.
        """

        if self.replay_available and HISTORICAL_BOOK2_AUTHORITY_REPLAY != "AVAILABLE":
            raise ValuationError(
                "a historical authority report may not claim replay availability "
                f"while Book 2 authority replay is {HISTORICAL_BOOK2_AUTHORITY_REPLAY}"
            )
        return self


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
    "HISTORICAL_BOOK2_AUTHORITY_REPLAY",
    "Book5WriteBackRefusal",
    "HistoricalAuthorityReport",
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
