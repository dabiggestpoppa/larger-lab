"""SENSOR-B5-I04A - pure point-in-time terms projection (D1 + D2).

Hierarchy preserved (I04A directive S02): source evidence -> registry record
-> PIT-valid ``ContractInstance`` -> :class:`ContractTermsSnapshot` -> future
conversion primitives (I04B+, not implemented here).

D2 selects readiness interpretation B: the I03 identity resolver is CONSUMED,
never modified; ``TERMS_UNVERIFIED`` remains a reserved identity status that
no code in this package constructs; and a successfully resolved identity does
NOT qualify for a verified economic view merely because identity resolved --
the terms-verification boundary is enforced HERE, inside the projection.

Interface law (I04A directive S03.3): the projection performs no symbol
matching, selects no ambiguous candidate, queries no provider, retrieves no
reference price, and infers no multiplier.  It returns an immutable
provenance-bearing snapshot or ``None`` (typed absence under the existing
authorized vocabulary); refusal reasons are derivable by the caller from the
supplied clocks and inputs, so no new public response contract is created.

Plan citations use the compact S<n> form for bloc_05/01 section <n>.
"""

from __future__ import annotations

from datetime import datetime

from ..enums import PayoffType
from ..identity import (
    IdentityRegistrySnapshot,
    IdentityResolution,
    IdentityResolutionStatus,
)
from .snapshot import ContractTermsSnapshot

__all__ = ["project_contract_terms"]

_RESOLVED_STATUSES = frozenset(
    {
        IdentityResolutionStatus.RESOLVED_EXACT,
        IdentityResolutionStatus.RESOLVED_ALIAS,
        IdentityResolutionStatus.RESOLVED_WITH_WARNING,
    }
)


def _valid_at(event_time: datetime, valid_from: datetime, valid_to: datetime | None) -> bool:
    """Valid-time law: ``valid_from <= event_time < valid_to`` with the
    frozen open-ended rule when ``valid_to`` is absent (bloc_05/01 S9)."""
    if event_time < valid_from:
        return False
    if valid_to is not None and not event_time < valid_to:
        return False
    return True


def _known_at(cutoff: datetime, known_from: datetime, known_to: datetime | None) -> bool:
    """Knowledge-time law: ``known_from <= cutoff`` plus the operator Option 1
    upper boundary ``cutoff < known_to`` where the record carries one; an
    absent ``known_to`` is open-ended (bloc_05/01 S9, accepted I03 semantics,
    restated here as I04-owned economic-terms eligibility per directive S07
    Stage D - not a copy claiming parity: S04A-06..12 pin both layers against
    one resolved registry fixture)."""
    if not known_from <= cutoff:
        return False
    if known_to is not None and not cutoff < known_to:
        return False
    return True


def project_contract_terms(
    registry: IdentityRegistrySnapshot,
    resolution: IdentityResolution,
    event_time: datetime,
    knowledge_cutoff: datetime,
) -> ContractTermsSnapshot | None:
    """Project eligible recorded terms for an upstream I03 resolution.

    Returns the immutable terms snapshot when the resolution selected a
    unique instance that is PIT-eligible at both clocks and whose payoff
    semantics are verified; ``None`` otherwise (unresolved/ambiguous
    identity, ineligible clocks, unverified terms, or referentially missing
    source record).  Never mutates its inputs.
    """
    # 1. identity must already be resolved to exactly one instance (S03.3:
    #    ambiguity, unknown symbols, blocks and verdicts are never laundered
    #    into a selection here).
    if resolution.status not in _RESOLVED_STATUSES:
        return None
    if resolution.contract_instance_id is None:
        return None

    instance = next(
        (
            ci
            for ci in registry.contract_instances
            if ci.contract_instance_id == resolution.contract_instance_id
        ),
        None,
    )
    if instance is None:
        return None

    # 2. I04-owned PIT eligibility on both clocks (directive S03.2/S07 Stage D).
    if not _valid_at(event_time, instance.valid_from, instance.valid_to):
        return None
    if not _known_at(knowledge_cutoff, instance.known_from, instance.known_to):
        return None

    # 3. terms-verification boundary (D2): unverified payoff semantics means
    #    no verified economic view - identity resolution status is untouched
    #    and no reserved status is constructed (bloc_05/01 S3, bloc_05/07 F3).
    if instance.payoff_type is PayoffType.UNKNOWN:
        return None

    economic_contract = next(
        (
            ec
            for ec in registry.economic_contracts
            if ec.economic_contract_id == instance.economic_contract_id
        ),
        None,
    )
    if economic_contract is None:
        # Referential integrity normally makes this unreachable; refusing is
        # the fail-closed answer rather than inventing the quote asset.
        return None

    return ContractTermsSnapshot(
        contract_instance_id=instance.contract_instance_id,
        economic_contract_id=instance.economic_contract_id,
        contract_terms_version=instance.contract_terms_version,
        contract_multiplier=instance.contract_multiplier,
        multiplier_unit=instance.multiplier_unit,
        price_unit=instance.price_unit,
        quantity_unit=instance.quantity_unit,
        payoff_type=instance.payoff_type,
        inverse_flag=instance.inverse_flag,
        quanto_flag=instance.quanto_flag,
        quote_asset_id=economic_contract.quote_asset_id,
        settlement_asset_id=instance.settlement_asset_id,
        margin_asset_id=instance.margin_asset_id,
        tick_size=instance.tick_size,
        lot_size=instance.lot_size,
        expiry=instance.expiry,
        source_evidence_refs=instance.source_evidence_refs,
    )
