"""SENSOR-B5-I02 — frozen Bloc 5 identity models and registries (bloc_05/01 §2).

The five identity records: :class:`CanonicalAsset`, :class:`Venue`,
:class:`VenueInstrument`, :class:`EconomicContract` and
:class:`ContractInstance`, plus the versioned registry snapshot that stores
and retrieves them by explicit identity.

This layer ESTABLISHES identity records.  It does not resolve provider
observations to them yet, and it computes nothing:

* no lifecycle, alias or PIT resolution (bloc_05/01 §6/§8/§9 -- B5-I03);
* no contract-term conversion: linear/inverse exposure, unit conversion,
  base quantity, quote notional and USD value are all absent (B5-I04);
* no ``native_symbol`` parsing: a symbol is preserved verbatim and is never
  durable contract identity (bloc_05/01 §7);
* no current-metadata backcast: valid/knowledge intervals are stored, never
  silently answered by a "latest" view (bloc_05/01 §5/§10).

Laws enforced here (fail closed):

* non-blank, unpadded identifiers everywhere; symbols preserved verbatim;
* timezone-aware UTC datetimes only; naive input refused outright;
* finite intervals order forward: ``valid_to > valid_from`` and
  ``known_to > known_from`` where finite (directive §15 "where finite");
* ``native_metadata_hash`` is format-checked SHA-256 hex;
* source evidence is a non-empty, duplicate-free tuple of durable
  identifiers -- never filesystem paths;
* ``payoff_type=INVERSE`` cannot claim ``inverse_flag=False`` and
  ``payoff_type=QUANTO`` cannot claim ``quanto_flag=False`` (directive §16);
* registry records are immutable (``frozen``): updating truth means a new
  versioned snapshot, never a silent rewrite (directive §20).

Vocabulary authority: only ``payoff_type`` carries a frozen vocabulary, and it
is the B5-I01 :class:`PayoffType` reused, not redefined.  Every other audited
field (``asset_type``, ``instrument_type``, ``perpetual_or_delivery``, the
unit fields, ``index_family``, ``chain_or_issuer_context``) is a validated
opaque :data:`SemanticToken` -- see
``BLOC_05_I02_VOCABULARY_AUTHORITY_MATRIX.json``.
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import (
    AfterValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from ...contracts.base import coerce_utc
from ..enums import PayoffType
from ..models import NormalizationModelBase, OpaqueIdentifier, RegistryVersion

__all__ = [
    "CanonicalAsset",
    "ContractInstance",
    "EconomicContract",
    "SemanticToken",
    "Venue",
    "VenueInstrument",
]

#: SHA-256 hexadecimal syntax for ``native_metadata_hash``.  Format-only:
#: nothing here hashes anything (Bloc 4 owns checksums; B5-I16 owns T1 IDs).
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


def _reject_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value


def _require_unpadded(value: str) -> str:
    if value != value.strip():
        raise ValueError(f"must not carry leading/trailing whitespace: {value!r}")
    return value


def _reject_path_shaped(value: str) -> str:
    """Refuse filesystem-path-shaped evidence references (directive §17).

    Durable identifiers name evidence, not files: they carry no path
    separators at all (no absolute or relative paths, no Windows drive or
    backslash forms).  ``provider-docs:kraken-futures`` is an identifier;
    ``relative/file.json`` is a path.
    """
    if (
        "/" in value
        or "\\" in value
        or re.match(r"^[A-Za-z]:", value)
        or value.startswith(".")
    ):
        raise ValueError(
            f"source evidence must be a durable identifier, not a filesystem path: {value!r}"
        )
    return value


def _require_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    if len(set(values)) != len(values):
        raise ValueError("contains duplicate references")
    return values


#: Validated opaque semantic token: non-blank, unpadded, preserved verbatim.
#: Deliberately NOT an enum: no audited I02-owned vocabulary is frozen (the
#: vocabulary authority matrix records the operator-decision boundary).
SemanticToken = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"\S"),
    AfterValidator(_reject_blank),
    AfterValidator(_require_unpadded),
]

#: Timezone-aware UTC datetime; naive input refused at the field level so
#: immutable records never need post-construction mutation.
UtcDatetime = Annotated[datetime, AfterValidator(coerce_utc)]

_EvidenceRef = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"\S"),
    AfterValidator(_reject_blank),
    AfterValidator(_require_unpadded),
    AfterValidator(_reject_path_shaped),
]


class IdentityModelBase(NormalizationModelBase):
    """Immutable fail-closed base for registry records (directive §20).

    ``frozen`` is a deliberate registry-specific choice: identity records are
    versioned truth, so in-place mutation must be structurally impossible --
    updating metadata means publishing a new registry version, exactly as
    bloc_05/01 §15 requires.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


class CanonicalAsset(IdentityModelBase):
    """The economic asset itself (bloc_05/01 §2.1).

    Economic identity only: this object is explicitly NOT sufficient to
    identify a derivative contract instance, and it must never collapse
    USD/USDT/USDC into one another (bloc_05/01 §12, bloc_05/07 F7).
    """

    asset_id: OpaqueIdentifier
    symbol_canonical: OpaqueIdentifier
    asset_type: SemanticToken
    chain_or_issuer_context: SemanticToken | None = None
    valid_from: UtcDatetime | None = None
    valid_to: UtcDatetime | None = None
    metadata_version: RegistryVersion

    @model_validator(mode="after")
    def _validate_validity_interval(self) -> CanonicalAsset:
        if (
            self.valid_from is not None
            and self.valid_to is not None
            and self.valid_to <= self.valid_from
        ):
            raise ValueError("valid_to must be strictly after valid_from")
        return self


class Venue(IdentityModelBase):
    """A market venue / exchange family (bloc_05/01 §2.2).

    The frozen plan gives Venue no field list -- §2.2 names the concept and
    lists example identifiers, which are examples, not a closed enum
    (directive §8).  ``venue_id`` is therefore the minimum referential anchor:
    the key VenueInstrument and ContractInstance reference.  Any descriptive
    metadata field would be invented vocabulary and requires an operator
    decision (see the vocabulary authority matrix).
    """

    venue_id: OpaqueIdentifier


class VenueInstrument(IdentityModelBase):
    """The provider/venue-native instrument identity (bloc_05/01 §2.3).

    This is what raw payloads refer to.  ``native_symbol`` is preserved
    exactly and is never durable contract identity (bloc_05/01 §7).  Provider
    and venue stay separate fields: an aggregator provider may reference a
    venue it does not operate (bloc_05/01 §13, bloc_05/07 F1).
    """

    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    native_symbol: OpaqueIdentifier
    provider_instrument_id: OpaqueIdentifier | None = None
    instrument_type: SemanticToken
    native_metadata_hash: Annotated[
        str, StringConstraints(pattern=_SHA256_HEX_RE.pattern)
    ]
    first_seen_at: UtcDatetime
    last_seen_at: UtcDatetime

    @model_validator(mode="after")
    def _validate_observation_window(self) -> VenueInstrument:
        if self.last_seen_at < self.first_seen_at:
            raise ValueError("last_seen_at must not be before first_seen_at")
        return self


class EconomicContract(IdentityModelBase):
    """Stable economic grouping across comparable native symbols (bloc_05/01 §2.4).

    Useful for grouping, never for destructive replacement of contract-instance
    identity (bloc_05/01 §2.4, bloc_05/07 F1).  Underlying, quote, settlement
    and margin remain separate references (bloc_05/01 §4, bloc_05/07 F6); no
    conversion semantics exist at this layer (B5-I04 owns terms logic).
    """

    economic_contract_id: OpaqueIdentifier
    underlying_asset_id: OpaqueIdentifier
    quote_asset_id: OpaqueIdentifier
    settlement_asset_id: OpaqueIdentifier
    margin_asset_id: OpaqueIdentifier | None = None
    instrument_type: SemanticToken
    perpetual_or_delivery: SemanticToken
    payoff_type: PayoffType
    index_family: SemanticToken | None = None


class ContractInstance(IdentityModelBase):
    """The exact lifecycle-valid contract terms at a point in time (bloc_05/01 §2.5).

    A DATA MODEL only (directive §13/§14): it stores the frozen term fields
    and validates structural consistency, but computes no exposure, converts
    no units and resolves no changing terms through time.  The PIT lookup
    ``valid_from <= t < valid_to`` / ``known_from <= cutoff`` is B5-I03.

    ``valid_to``/``known_to`` are ``None`` when not finite: an active instance
    has no known end, and a fabricated far-future date would be invented truth
    (directive §15 "where finite").
    """

    contract_instance_id: OpaqueIdentifier
    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    native_symbol: OpaqueIdentifier
    economic_contract_id: OpaqueIdentifier
    valid_from: UtcDatetime
    valid_to: UtcDatetime | None = None
    known_from: UtcDatetime
    known_to: UtcDatetime | None = None
    contract_multiplier: Decimal
    multiplier_unit: SemanticToken
    price_unit: SemanticToken
    quantity_unit: SemanticToken
    settlement_asset_id: OpaqueIdentifier
    margin_asset_id: OpaqueIdentifier | None = None
    payoff_type: PayoffType
    inverse_flag: bool
    quanto_flag: bool
    tick_size: Decimal
    lot_size: Decimal
    expiry: UtcDatetime | None = None
    contract_terms_version: RegistryVersion
    source_evidence_refs: Annotated[
        tuple[_EvidenceRef, ...],
        Field(min_length=1),
        AfterValidator(_require_unique),
    ]

    @model_validator(mode="after")
    def _validate_intervals(self) -> ContractInstance:
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("finite valid_to must be strictly after valid_from")
        if self.known_to is not None and self.known_to <= self.known_from:
            raise ValueError("finite known_to must be strictly after known_from")
        return self

    @model_validator(mode="after")
    def _validate_payoff_flags(self) -> ContractInstance:
        """Directive §16: only the structural contradictions the frozen model
        explicitly supports.  Deeper flag-equivalence rules (e.g. LINEAR with
        ``inverse_flag=True``) are ambiguous in the plan and are recorded, not
        invented."""
        if self.payoff_type is PayoffType.INVERSE and not self.inverse_flag:
            raise ValueError(
                "payoff_type=INVERSE must not claim inverse_flag=False"
            )
        if self.payoff_type is PayoffType.QUANTO and not self.quanto_flag:
            raise ValueError("payoff_type=QUANTO must not claim quanto_flag=False")
        return self
