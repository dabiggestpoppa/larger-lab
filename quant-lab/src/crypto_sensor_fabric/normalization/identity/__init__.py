"""SENSOR-B5-I02 — Bloc 5 identity records and registries (bloc_05/01 §2).

The five frozen identity objects (:class:`CanonicalAsset`, :class:`Venue`,
:class:`VenueInstrument`, :class:`EconomicContract`,
:class:`ContractInstance`) plus the minimal versioned registry structures
that store and retrieve them by explicit identity.

This subpackage ESTABLISHES identity records; it does not resolve provider
observations to them.  Resolver behavior is B5-I03 (bloc_05/01 §9), term
conversion is B5-I04, and no alias/lifecycle/universe machinery exists here.

OFFLINE: no network, no provider adapter, no filesystem access.  The module
surface is text-in/text-out registry serialization only.

Symbols are exposed from ``crypto_sensor_fabric.normalization.identity`` only:
the top-level normalization surface stays exactly the 24 ratified B5-I01
public symbols (directive §29).
"""

from __future__ import annotations

from .models import (
    CanonicalAsset,
    ContractInstance,
    EconomicContract,
    SemanticToken,
    Venue,
    VenueInstrument,
)
from .registry import (
    IdentityRegistrySnapshot,
    parse_identity_registry_yaml,
    serialize_identity_registry_yaml,
    validate_registry_succession,
)

__all__ = [
    "CanonicalAsset",
    "ContractInstance",
    "EconomicContract",
    "IdentityRegistrySnapshot",
    "SemanticToken",
    "Venue",
    "VenueInstrument",
    "parse_identity_registry_yaml",
    "serialize_identity_registry_yaml",
    "validate_registry_succession",
]
