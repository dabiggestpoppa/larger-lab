"""SENSOR-B5-I02 — minimal versioned identity registry (bloc_05/01 §15/§17).

The registry is the minimum deterministic structure that stores and retrieves
the five identity records by explicit identity:

* explicit ``registry_version`` — the identity registry is versioned
  independently from normalization code (bloc_05/01 §15);
* stable canonical ordering and duplicate-ID refusal, so serialization is
  byte-deterministic and no identifier can be quietly replaced;
* referential integrity inside one accepted snapshot: no dangling asset,
  venue or economic-contract reference (directive §31/§32/§33);
* no overlapping active terms for the same provider instrument
  (bloc_05/01 §17 invariant 3) — without an explicit ambiguity state, the
  only fail-closed answer is refusal;
* text-in/text-out YAML persistence: serialization and parsing carry no
  filesystem knowledge, so the registry cannot read or write paths here.

Serialization is deterministic (sorted keys, canonical collection order,
Decimals as exact decimal strings, UTC ISO-8601 times).  ``json.loads`` of
``model_dump_json`` is reused from the I01 canonical serializer so the same
payload is yaml-safe and byte-stable.  No wall-clock value is ever minted and
no identifier is ever derived: IDs are supplied, never computed.
"""

from __future__ import annotations

import json
from typing import Annotated

import yaml
from pydantic import AfterValidator, ConfigDict, model_validator

from ..models import NormalizationModelBase, RegistryVersion, canonical_json_bytes
from .models import (
    CanonicalAsset,
    ContractInstance,
    EconomicContract,
    Venue,
    VenueInstrument,
)

__all__ = [
    "IdentityRegistrySnapshot",
    "parse_identity_registry_yaml",
    "serialize_identity_registry_yaml",
    "validate_registry_succession",
]


def _canonical_assets(values: tuple[CanonicalAsset, ...]) -> tuple[CanonicalAsset, ...]:
    ids = [value.asset_id for value in values]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate asset_id in registry snapshot")
    return tuple(sorted(values, key=lambda value: value.asset_id))


def _canonical_venues(values: tuple[Venue, ...]) -> tuple[Venue, ...]:
    ids = [value.venue_id for value in values]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate venue_id in registry snapshot")
    return tuple(sorted(values, key=lambda value: value.venue_id))


def _instrument_key(value: VenueInstrument) -> tuple[str, str, str, str]:
    return (
        value.provider,
        value.venue,
        value.native_symbol,
        value.provider_instrument_id or "",
    )


def _canonical_venue_instruments(
    values: tuple[VenueInstrument, ...],
) -> tuple[VenueInstrument, ...]:
    keys = [_instrument_key(value) for value in values]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate venue instrument identity in registry snapshot")
    return tuple(sorted(values, key=_instrument_key))


def _canonical_economic_contracts(
    values: tuple[EconomicContract, ...],
) -> tuple[EconomicContract, ...]:
    ids = [value.economic_contract_id for value in values]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate economic_contract_id in registry snapshot")
    return tuple(sorted(values, key=lambda value: value.economic_contract_id))


def _canonical_contract_instances(
    values: tuple[ContractInstance, ...],
) -> tuple[ContractInstance, ...]:
    ids = [value.contract_instance_id for value in values]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate contract_instance_id in registry snapshot")
    return tuple(sorted(values, key=lambda value: value.contract_instance_id))


class IdentityRegistrySnapshot(NormalizationModelBase):
    """One immutable, versioned, referentially-closed identity registry snapshot.

    A snapshot is truth for exactly one ``registry_version``.  Because the
    model is frozen and every collection is canonically ordered and
    duplicate-free, updating identity truth is structurally forced to be a
    NEW snapshot (bloc_05/01 §15): nothing can mutate in place, and
    :func:`validate_registry_succession` refuses a same-version republish with
    conflicting content.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    registry_version: RegistryVersion
    assets: Annotated[tuple[CanonicalAsset, ...], AfterValidator(_canonical_assets)] = ()
    venues: Annotated[tuple[Venue, ...], AfterValidator(_canonical_venues)] = ()
    venue_instruments: Annotated[
        tuple[VenueInstrument, ...], AfterValidator(_canonical_venue_instruments)
    ] = ()
    economic_contracts: Annotated[
        tuple[EconomicContract, ...], AfterValidator(_canonical_economic_contracts)
    ] = ()
    contract_instances: Annotated[
        tuple[ContractInstance, ...], AfterValidator(_canonical_contract_instances)
    ] = ()

    @model_validator(mode="after")
    def _validate_referential_integrity(self) -> IdentityRegistrySnapshot:
        asset_ids = {asset.asset_id for asset in self.assets}
        venue_ids = {venue.venue_id for venue in self.venues}
        economic_ids = {ec.economic_contract_id for ec in self.economic_contracts}

        for vi in self.venue_instruments:
            if vi.venue not in venue_ids:
                raise ValueError(
                    f"venue instrument {vi.native_symbol!r} references unregistered venue {vi.venue!r}"
                )

        for ec in self.economic_contracts:
            for label, ref in (
                ("underlying_asset_id", ec.underlying_asset_id),
                ("quote_asset_id", ec.quote_asset_id),
                ("settlement_asset_id", ec.settlement_asset_id),
                ("margin_asset_id", ec.margin_asset_id),
            ):
                if ref is not None and ref not in asset_ids:
                    raise ValueError(
                        f"economic contract {ec.economic_contract_id!r} {label} {ref!r} is not a registered asset"
                    )

        for ci in self.contract_instances:
            if ci.economic_contract_id not in economic_ids:
                raise ValueError(
                    f"contract instance {ci.contract_instance_id!r} references unregistered economic contract {ci.economic_contract_id!r}"
                )
            if ci.venue not in venue_ids:
                raise ValueError(
                    f"contract instance {ci.contract_instance_id!r} references unregistered venue {ci.venue!r}"
                )
            for label, ref in (
                ("settlement_asset_id", ci.settlement_asset_id),
                ("margin_asset_id", ci.margin_asset_id),
            ):
                if ref is not None and ref not in asset_ids:
                    raise ValueError(
                        f"contract instance {ci.contract_instance_id!r} {label} {ref!r} is not a registered asset"
                    )
        return self

    @model_validator(mode="after")
    def _validate_no_overlapping_active_terms(self) -> IdentityRegistrySnapshot:
        """bloc_05/01 §17 invariant 3: one provider instrument may not have two
        overlapping active contract instances without an explicit ambiguity
        state -- and no ambiguity state exists at B5-I02, so overlap fails
        closed.  Adjacent intervals (end == next start) are not overlap."""
        groups: dict[tuple[str, str, str], list[ContractInstance]] = {}
        for ci in self.contract_instances:
            groups.setdefault((ci.provider, ci.venue, ci.native_symbol), []).append(ci)
        for key, group in groups.items():
            ordered = sorted(group, key=lambda c: c.valid_from)
            for earlier, later in zip(ordered, ordered[1:]):
                if earlier.valid_to is None or later.valid_from < earlier.valid_to:
                    raise ValueError(
                        "overlapping active terms for provider instrument "
                        f"{key[0]!r}/{key[1]!r}/{key[2]!r} without an explicit "
                        "ambiguity state"
                    )
        return self


def serialize_identity_registry_yaml(snapshot: IdentityRegistrySnapshot) -> str:
    """Deterministic YAML text for a registry snapshot.

    Byte-stable for structurally equal snapshots: sorted keys, canonical
    collection order, exact decimal strings, UTC ISO-8601 timestamps.
    """
    payload = json.loads(snapshot.model_dump_json())
    return yaml.safe_dump(
        payload,
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
        width=4096,
    )


def parse_identity_registry_yaml(text: str) -> IdentityRegistrySnapshot:
    """Parse and fully validate a registry snapshot from YAML text."""
    data = yaml.safe_load(text)
    return IdentityRegistrySnapshot.model_validate(data)


def validate_registry_succession(
    previous: IdentityRegistrySnapshot,
    successor: IdentityRegistrySnapshot,
) -> None:
    """Refuse a same-version republish whose content differs.

    Publishing different content under an unchanged ``registry_version`` is a
    silent rewrite of historical truth (bloc_05/01 §15, directive §20).  An
    identical republish of the same version is idempotent and accepted; any
    content change requires a new version.
    """
    if canonical_json_bytes(previous) == canonical_json_bytes(successor):
        return
    if previous.registry_version == successor.registry_version:
        raise ValueError(
            "same registry version with conflicting content would silently "
            f"rewrite registry truth (registry_version={previous.registry_version!r})"
        )
