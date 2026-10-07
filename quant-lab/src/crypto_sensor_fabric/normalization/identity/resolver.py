"""SENSOR-B5-I03 - pure PIT identity resolver (bloc_05/01 sections 5-10).

Deterministic, dependency-free resolution from (provider, venue, native
symbol, event_time, knowledge_cutoff [, provider instrument id]) to an
immutable :class:`IdentityResolution` verdict, run entirely over one explicit
immutable :class:`~crypto_sensor_fabric.normalization.identity.registry.
IdentityRegistrySnapshot`:

* pure: no global state, no filesystem, no network, no wall clock (I03
  directive 35/36/37);
* dual-clock (bloc_05/01 section 5): a candidate may be used ONLY while
  ``valid_from <= event_time < valid_to`` (open-ended valid_to explicit) AND
  ``known_from <= knowledge_cutoff`` - no future metadata may leak backward;
* EXACT matching only (section 10): no fuzzy, no prefix, no substring, no case
  folding, no separator normalization, no BTC/XBT inference without a
  registered alias, and no USDT-for-USD substitution (section 12 stablecoin
  firewall);
* frozen five-tier order (section 10): (1) provider instrument id valid at
  event time, (2) exact native symbol + venue + lifecycle interval,
  (3) documented alias valid at event time, (4) curated evidence-backed manual
  mapping (carried, per the vocabulary matrix, as InstrumentAlias rows), and
  (5) no result.  Tiers 3 and 4 are ONE pooled scan by design (ambiguity
  dominates convenience, section 9): splitting curated carriers into a later
  sequential tier would let a convenience match silently outrank an ambiguity
  the pooled scan can see.  Tier-4 semantics live in the discrimination of
  the winner: a curated non-API carrier that wins the scan surfaces
  IDENTITY_MANUAL_OVERRIDE (section 14) instead of IDENTITY_ALIAS_USED;
* ambiguity refuses (section 9, directive 24): at one tier, several equally
  PIT-valid candidates yield AMBIGUOUS and NEVER a sorted/first/last winner;
  a curated carrier can never outrank an ambiguity the pooled alias scan sees;
* lifecycle-verdict law (section 6; directives 11/12/13/33): a queried symbol
  with instances known by the cutoff but no instance valid at event_time is
  NOT_YET_LISTED strictly before the earliest valid_from and DELISTED at/after
  the latest valid_to (cutover to the next instance is the relisting law, not
  a silent latest-win); knowledge-blocked candidates are PIT_KNOWLEDGE_BLOCKED;
  lifecycle evidence (SUSPENDED / DELISTING_ANNOUNCED windows over the event
  time) downgrades a resolution to RESOLVED_WITH_WARNING with
  IDENTITY_LIFECYCLE_BOUNDARY - nothing is invented beyond the frozen nine
  statuses.  A downgraded ALIAS match keeps its status RESOLVED_WITH_WARNING
  and its provenance (alias evidence refs, confidence, IDENTITY_ALIAS_USED)
  but carries NO matched_alias_id: that field is only set for RESOLVED_ALIAS
  (I03 validator law);
* unresolved answers carry NO fabricated identifiers (directive 25):
  contract_instance_id / economic_contract_id / canonical_asset_id /
  matched_alias_id / terms_version stay None and source refs stay empty
  unless a real identity was selected (then evidence names it).

The returned ``canonical_asset_id`` is the underlying asset of the selected
instance's economic contract (bloc_05/07 F1 "canonical underlying asset";
vocabulary matrix row 7) - supplied by the registry, never computed.
``terms_version`` mirrors ``ContractInstance.contract_terms_version`` verbatim
(directive 27); no term is converted or applied (B5-I04+).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, ConfigDict, Field, model_validator

from ..enums import NormalizationQualityFlag, _FLAG_ORDER
from ..models import NormalizationModelBase, OpaqueIdentifier, RegistryVersion
from .enums import (
    AliasType,
    IdentityResolutionStatus,
    LifecycleState,
)
from .registry import IdentityRegistrySnapshot

__all__ = [
    "IdentityResolution",
    "resolve_instrument",
]


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

_BLOCKERS = frozenset(
    {
        IdentityResolutionStatus.AMBIGUOUS,
        IdentityResolutionStatus.UNKNOWN_SYMBOL,
        IdentityResolutionStatus.TERMS_UNVERIFIED,
        IdentityResolutionStatus.PIT_KNOWLEDGE_BLOCKED,
    }
)
_RESOLVED_SET = frozenset(
    {
        IdentityResolutionStatus.RESOLVED_EXACT,
        IdentityResolutionStatus.RESOLVED_ALIAS,
        IdentityResolutionStatus.RESOLVED_WITH_WARNING,
    }
)

#: Section 8 alias kinds that are provider-documented symbol surfaces: a win
#: through one of these is an ordinary registered-alias match (tier 3).  Every
#: other frozen kind is a curated, evidence-backed carrier (vocabulary matrix
#: directive 29 path A): a win through one of those carries tier-4 semantics
#: and surfaces IDENTITY_MANUAL_OVERRIDE (section 14) instead of
#: IDENTITY_ALIAS_USED.
_DOCUMENTED_SYMBOL_ALIAS_TYPES = frozenset(
    {AliasType.API_SYMBOL, AliasType.WEBSOCKET_SYMBOL}
)


def _flags_in_canonical_order(
    flags: tuple[NormalizationQualityFlag, ...],
) -> tuple[NormalizationQualityFlag, ...]:
    idx = _FLAG_ORDER
    order = [idx[flag] for flag in flags]
    if order != sorted(order) or len(set(order)) != len(order):
        raise ValueError("quality_flags must be canonical-order and duplicate-free")
    return flags


def _require_unique_ref(values: tuple[str, ...]) -> tuple[str, ...]:
    if len(set(values)) != len(values):
        raise ValueError("duplicate evidence reference")
    return values


class IdentityResolution(NormalizationModelBase):
    """Immutable verdict of one PIT identity query (bloc_05/01 section 9).

    Exactly the frozen field list: status, contract_instance_id,
    canonical_asset_id, economic_contract_id, matched_alias_id, terms_version,
    confidence, quality_flags, source_evidence_refs.  Unresolved (blocking and
    verdict) statuses carry None identifiers and no evidence; resolved
    statuses must carry the selected instance identity.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: IdentityResolutionStatus
    contract_instance_id: OpaqueIdentifier | None = None
    canonical_asset_id: OpaqueIdentifier | None = None
    economic_contract_id: OpaqueIdentifier | None = None
    matched_alias_id: OpaqueIdentifier | None = None
    terms_version: RegistryVersion | None = None
    confidence: str | None = None
    quality_flags: Annotated[
        tuple[NormalizationQualityFlag, ...],
        Field(default=()),
        AfterValidator(_flags_in_canonical_order),
    ] = ()
    source_evidence_refs: Annotated[
        tuple[str, ...],
        Field(default=()),
        AfterValidator(_require_unique_ref),
    ] = ()

    @model_validator(mode="after")
    def _validate_status_to_fields(self) -> IdentityResolution:
        blocking = self.status in _BLOCKERS
        unresolved = self.status in (
            IdentityResolutionStatus.NOT_YET_LISTED,
            IdentityResolutionStatus.DELISTED,
        )
        resolved = self.status in _RESOLVED_SET
        if blocking or unresolved:
            bad = [
                name
                for name, value in (
                    ("contract_instance_id", self.contract_instance_id),
                    ("economic_contract_id", self.economic_contract_id),
                    ("canonical_asset_id", self.canonical_asset_id),
                    ("matched_alias_id", self.matched_alias_id),
                    ("terms_version", self.terms_version),
                )
                if value is not None
            ]
            if bad:
                raise ValueError(
                    f"status {self.status.value} must not carry "
                    + ", ".join(bad)
                    + " (no fabricated identity)"
                )
            if self.source_evidence_refs:
                raise ValueError(
                    f"status {self.status.value} must not carry source evidence refs"
                )
        if resolved:
            bad = [
                name
                for name in (
                    "contract_instance_id",
                    "economic_contract_id",
                    "canonical_asset_id",
                    "terms_version",
                )
                if getattr(self, name) is None
            ]
            if bad:
                raise ValueError(
                    f"resolved status {self.status.value} requires "
                    + ", ".join(bad)
                )
        if self.status is IdentityResolutionStatus.RESOLVED_ALIAS and self.matched_alias_id is None:
            raise ValueError(
                "RESOLVED_ALIAS must name matched_alias_id (bloc_05/01 section 9)"
            )
        if (
            self.matched_alias_id is not None
            and self.status is not IdentityResolutionStatus.RESOLVED_ALIAS
        ):
            raise ValueError(
                "matched_alias_id is only set for RESOLVED_ALIAS "
                "(RESOLVED_WITH_WARNING carries its own lifecycle evidence)"
            )
        return self


# ---------------------------------------------------------------------------
# PIT predicates (dual-clock law)
# ---------------------------------------------------------------------------


def _valid_at(event_time: datetime, valid_from: datetime, valid_to: datetime | None) -> bool:
    """valid-time law: [valid_from, valid_to) with open-ended None."""
    return valid_from <= event_time and (valid_to is None or event_time < valid_to)


def _known_by(known_from: datetime, knowledge_cutoff: datetime) -> bool:
    """knowledge-time law: known_from <= knowledge_cutoff (inclusive)."""
    return known_from <= knowledge_cutoff


# ---------------------------------------------------------------------------
# Resolver internals
# ---------------------------------------------------------------------------


def _empty(status: IdentityResolutionStatus) -> IdentityResolution:
    return IdentityResolution(
        status=status,
        quality_flags=_sorted_flags(_advisory_flags(status)),
        source_evidence_refs=(),
    )


def _sorted_flags(
    flags,
) -> tuple[NormalizationQualityFlag, ...]:
    return tuple(
        sorted(set(flags), key=lambda flag: _FLAG_ORDER[flag])
    )


def _advisory_flags(status: IdentityResolutionStatus):
    if status is IdentityResolutionStatus.NOT_YET_LISTED:
        return (NormalizationQualityFlag.IDENTITY_LIFECYCLE_BOUNDARY,)
    if status is IdentityResolutionStatus.DELISTED:
        return (NormalizationQualityFlag.IDENTITY_LIFECYCLE_BOUNDARY,)
    return ()


def _instances_for(
    snapshot: IdentityRegistrySnapshot,
    provider: str,
    venue: str,
    native_symbol: str,
) -> list:
    """All instances registered for the exact (provider, venue, native symbol)."""
    return [
        ci
        for ci in snapshot.contract_instances
        if ci.provider == provider
        and ci.venue == venue
        and ci.native_symbol == native_symbol
    ]


def _pit_valid(instances, event_time: datetime, knowledge_cutoff: datetime) -> list:
    """Dual-clock gate applied per instance (valid-time AND knowledge-time)."""
    return [
        ci
        for ci in instances
        if _valid_at(event_time, ci.valid_from, ci.valid_to)
        and _known_by(ci.known_from, knowledge_cutoff)
    ]


def _lifecycle_warning(
    snapshot: IdentityRegistrySnapshot,
    provider: str,
    venue: str,
    instance_id: str,
    event_time: datetime,
    knowledge_cutoff: datetime,
) -> bool:
    """True iff knowledge-valid lifecycle evidence marks a non-active state
    window (SUSPENDED / DELISTING_ANNOUNCED) covering the event time."""
    for event in snapshot.lifecycle_events:
        if (
            event.provider == provider
            and event.venue == venue
            and event.contract_instance_id == instance_id
            and _known_by(event.known_from, knowledge_cutoff)
            and _valid_at(event_time, event.valid_from, event.valid_to)
            and event.lifecycle_state
            in (LifecycleState.SUSPENDED, LifecycleState.DELISTING_ANNOUNCED)
        ):
            return True
    return False


# ---------------------------------------------------------------------------
# Public resolver
# ---------------------------------------------------------------------------


def resolve_instrument(
    snapshot: IdentityRegistrySnapshot,
    provider: str,
    venue: str,
    native_symbol: str,
    event_time: datetime,
    knowledge_cutoff: datetime,
    optional_provider_instrument_id: str | None = None,
) -> IdentityResolution:
    """Resolve one provider-native observation to its PIT contract identity.

    The five-tier frozen order (bloc_05/01 section 10) with the dual-clock
    gate applied to every candidate at every tier.  Higher tiers win only
    with PIT-valid evidence; ties inside one tier are AMBIGUOUS.  Naive
    datetimes are refused outright (directive 35).
    """
    # -- input validation (fail closed; no wall-clock defaults) -------------
    if not provider or not provider.strip():
        raise ValueError("provider must be nonblank")
    if not venue or not venue.strip():
        raise ValueError("venue must be nonblank")
    if not native_symbol or not native_symbol.strip():
        raise ValueError("native_symbol must be nonblank")
    if not isinstance(event_time, datetime) or event_time.tzinfo is None:
        raise ValueError("event_time must be timezone-aware (no naive datetimes)")
    if not isinstance(knowledge_cutoff, datetime) or knowledge_cutoff.tzinfo is None:
        raise ValueError(
            "knowledge_cutoff must be timezone-aware (no naive datetimes)"
        )
    if optional_provider_instrument_id is not None and not str(
        optional_provider_instrument_id
    ).strip():
        raise ValueError(
            "optional_provider_instrument_id must be nonblank when given"
        )

    # -- tier 1: provider instrument id valid at event time ------------------
    if optional_provider_instrument_id is not None:
        outcome = _tier_provider_id(
            snapshot,
            provider,
            venue,
            event_time,
            knowledge_cutoff,
            optional_provider_instrument_id,
        )
        if outcome is not None:
            return outcome

    # -- tier 2: exact native symbol + venue + lifecycle interval -----------
    outcome = _tier_exact_symbol(
        snapshot, provider, venue, native_symbol, event_time, knowledge_cutoff
    )
    if outcome is not None:
        return outcome

    # -- tiers 3+4: registered alias scan (section 10).  ONE pooled scan:
    #    documented symbol surfaces AND curated evidence-backed carriers
    #    (vocabulary matrix directive 29 path A) are candidates alike, so
    #    several equally PIT-valid candidates are AMBIGUOUS and a curated
    #    carrier can never quietly outrank an ambiguity (ambiguity dominates
    #    convenience).  Tier-4 semantics are carried by the winner's alias
    #    kind: a curated non-API carrier wins with IDENTITY_MANUAL_OVERRIDE
    #    (section 14) instead of IDENTITY_ALIAS_USED.
    outcome = _tier_alias(
        snapshot, provider, venue, native_symbol, event_time, knowledge_cutoff
    )
    if outcome is not None:
        return outcome

    # -- tier 5: no result - but first, the evidence-aware blocker sweep: a
    #    registered-but-late row (alias or instance) that the cutoff has not
    #    caught up with is PIT_KNOWLEDGE_BLOCKED, not a silent unknown
    #    (directive 41: knowledge gate is fail-closed, never optimistic).
    late_alias = any(
        alias.provider == provider
        and alias.venue == venue
        and alias.alias_text == native_symbol
        and alias.known_from > knowledge_cutoff
        for alias in snapshot.aliases
    )
    if late_alias:
        return _empty(IdentityResolutionStatus.PIT_KNOWLEDGE_BLOCKED)
    late_instance = any(
        ci.known_from > knowledge_cutoff
        for ci in _instances_for(snapshot, provider, venue, native_symbol)
    )
    if late_instance:
        return _empty(IdentityResolutionStatus.PIT_KNOWLEDGE_BLOCKED)
    return _empty(IdentityResolutionStatus.UNKNOWN_SYMBOL)


def _tier_provider_id(snapshot, provider, venue, event_time, knowledge_cutoff,
                      provider_instrument_id):
    """Tier 1 (section 10 / directive 15): the provider instrument ID anchors
    the instrument; the PIT-valid ContractInstance bound to that instrument's
    native symbol carries the identity.  Requires provider + venue + time +
    knowledge context (never the bare ID)."""
    instrument = None
    for inst in snapshot.venue_instruments:
        if (
            inst.provider == provider
            and inst.venue == venue
            and inst.provider_instrument_id == provider_instrument_id
        ):
            instrument = inst
            break
    if instrument is None:
        # No such instrument in this registry context: the ID alone is not a
        # lifeline (directive 15); the symbol tiers still apply.
        return None
    matches = _pit_valid(
        _instances_for(snapshot, provider, venue, instrument.native_symbol),
        event_time,
        knowledge_cutoff,
    )
    if len(matches) == 1:
        return _resolved(
            snapshot,
            provider,
            venue,
            event_time,
            knowledge_cutoff,
            matches[0],
            alias_row=None,
            extra_flags=[NormalizationQualityFlag.IDENTITY_PROVIDER_ID_MISSING],
        )
    if len(matches) > 1:
        return _empty(IdentityResolutionStatus.AMBIGUOUS)
    # The instrument exists but has no PIT-valid instance right now: fall
    # through to the symbol tiers so temporal verdicts (not-yet-listed /
    # delisted) come from the same law as the exact-symbol tier.
    return None


def _tier_exact_symbol(snapshot, provider, venue, native_symbol, event_time, knowledge_cutoff):
    """Tier 2 (section 10 / directive 16): exact native symbol, no folding.
    Verdict law for temporal negatives (directives 11/12/13): known-but-not-
    valid resolves NOT_YET_LISTED strictly before the earliest valid_from and
    DELISTED otherwise (event_time >= some valid_to with no valid instance
    left; the between-gap relisting law does not fabricate an identity)."""
    known_any = _instances_for(snapshot, provider, venue, native_symbol)
    if not known_any:
        # Symbol never registered in this context (covers BTC-vs-XBT and all
        # prefix/fuzzy/case-fold probes); tiers 3/4 still get their chance.
        return None
    pit_known_at_all = [ci for ci in known_any if _known_by(ci.known_from, knowledge_cutoff)]
    if not pit_known_at_all:
        return _empty(IdentityResolutionStatus.PIT_KNOWLEDGE_BLOCKED)
    valid_now = [
        ci for ci in pit_known_at_all if _valid_at(event_time, ci.valid_from, ci.valid_to)
    ]
    if len(valid_now) == 1:
        return _resolved(
            snapshot,
            provider,
            venue,
            event_time,
            knowledge_cutoff,
            valid_now[0],
            alias_row=None,
            extra_flags=[],
        )
    if len(valid_now) > 1:
        # Registry refuses overlapping active terms at publication time; two
        # PIT-valid instances here mean temporally adjacent evidence with a
        # boundary the event time cannot disambiguate - fail closed.
        return _empty(IdentityResolutionStatus.AMBIGUOUS)
    # No instance covers the event time:
    earliest = min(ci.valid_from for ci in pit_known_at_all)
    if event_time < earliest:
        return _empty(IdentityResolutionStatus.NOT_YET_LISTED)
    return _empty(IdentityResolutionStatus.DELISTED)


def _tier_alias(snapshot, provider, venue, alias_text, event_time,
                knowledge_cutoff):
    """Tiers 3+4 (section 10; vocabulary matrix directive 29 path A): the
    registered-alias scan.  Provider exact, venue exact, alias_text exact,
    alias valid-time + knowledge-time admissible, linked instance doubly
    PIT-valid (directive 17).  ONE pooled scan over EVERY registered alias
    kind - documented symbol surfaces and curated non-API carriers alike - so
    several equally valid candidates at the tier are AMBIGUOUS, never a winner
    (directives 17/24).  The winner's alias kind decides the tier-3 vs tier-4
    reading of the match: a curated non-API carrier wins with
    IDENTITY_MANUAL_OVERRIDE (section 14) instead of IDENTITY_ALIAS_USED
    (discriminated in :func:`_resolved`).
    """
    matched = []
    for alias in snapshot.aliases:
        if alias.provider != provider or alias.venue != venue:
            continue
        if alias.alias_text != alias_text:
            continue
        if not _valid_at(event_time, alias.valid_from, alias.valid_to):
            continue
        if not _known_by(alias.known_from, knowledge_cutoff):
            continue
        matched.append(alias)
    matched.sort(key=lambda alias: alias.alias_id)  # deterministic canonical scan
    if not matched:
        return None
    instance_ids = {alias.contract_instance_id for alias in matched}
    if len(instance_ids) > 1:
        return _empty(IdentityResolutionStatus.AMBIGUOUS)
    found_all = [
        ci
        for ci in snapshot.contract_instances
        if ci.provider == provider
        and ci.venue == venue
        and ci.contract_instance_id in instance_ids
    ]
    if found_all and not _pit_valid(found_all, event_time, knowledge_cutoff):
        # Alias matched and its instance is registered, but NO PIT-valid
        # instance backs the alias at the queried instant.  The alias itself
        # passed the knowledge gate, so reaching here means the failure is
        # temporal on the linked instance (directive 12/13 verdicts):
        earliest = min(ci.valid_from for ci in found_all)
        if event_time < earliest:
            return _empty(IdentityResolutionStatus.NOT_YET_LISTED)
        return _empty(IdentityResolutionStatus.DELISTED)
    found = _pit_valid(found_all, event_time, knowledge_cutoff)
    if len(found) > 1:
        return _empty(IdentityResolutionStatus.AMBIGUOUS)
    return _resolved(
        snapshot,
        provider,
        venue,
        event_time,
        knowledge_cutoff,
        found[0],
        alias_row=matched[0],
        extra_flags=[],
    )


def _resolved(
    snapshot,
    provider,
    venue,
    event_time,
    knowledge_cutoff,
    winner,
    alias_row,
    extra_flags,
):
    """Build the final resolved verdict for one PIT-valid winner."""
    economic = next(
        (
            ec
            for ec in snapshot.economic_contracts
            if ec.economic_contract_id == winner.economic_contract_id
        ),
        None,
    )
    lifecycle_boundary = _lifecycle_warning(
        snapshot,
        provider,
        venue,
        winner.contract_instance_id,
        event_time,
        knowledge_cutoff,
    )
    flags = list(extra_flags)
    status = IdentityResolutionStatus.RESOLVED_EXACT
    evidence = list(winner.source_evidence_refs)
    confidence = None
    matched_alias_id = None
    if alias_row is not None:
        matched_alias_id = alias_row.alias_id
        confidence = alias_row.confidence
        evidence = list(alias_row.source_evidence_refs) + evidence
        flags.append(
            NormalizationQualityFlag.IDENTITY_ALIAS_USED
            if alias_row.alias_type in _DOCUMENTED_SYMBOL_ALIAS_TYPES
            else NormalizationQualityFlag.IDENTITY_MANUAL_OVERRIDE
        )
    evidence = list(dict.fromkeys(evidence))
    status = (
        IdentityResolutionStatus.RESOLVED_ALIAS
        if alias_row is not None
        else status
    )
    if lifecycle_boundary:
        flags.append(NormalizationQualityFlag.IDENTITY_LIFECYCLE_BOUNDARY)
        status = IdentityResolutionStatus.RESOLVED_WITH_WARNING
        # The warning status carries its own lifecycle evidence (I03 validator
        # law): matched_alias_id is reserved for RESOLVED_ALIAS.  Alias
        # provenance stays in source_evidence_refs, confidence and
        # IDENTITY_ALIAS_USED - nothing is lost, nothing is fabricated.
        matched_alias_id = None
    return IdentityResolution(
        status=status,
        contract_instance_id=winner.contract_instance_id,
        canonical_asset_id=(economic.underlying_asset_id if economic is not None else None),
        economic_contract_id=winner.economic_contract_id,
        matched_alias_id=matched_alias_id,
        terms_version=winner.contract_terms_version,
        confidence=confidence,
        quality_flags=_sorted_flags(flags),
        source_evidence_refs=tuple(evidence),
    )
